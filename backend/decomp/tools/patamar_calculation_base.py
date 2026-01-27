"""
Classe base para cálculos por patamares de usinas térmicas (disponibilidade, inflexibilidade, etc).
Contém toda a lógica comum de extração e cálculo.

OTIMIZADO: Carrega CT apenas uma vez, regex pré-compiladas, operações vetorizadas.
"""
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import pandas as pd
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

# Adicionar shared ao path para importar o matcher
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from backend.core.utils.usina_name_matcher import find_usina_match, normalize_usina_name
from backend.decomp.utils.thermal_plant_matcher import get_decomp_thermal_plant_matcher


class PatamarCalculationBase(DECOMPTool):
    """
    Classe base para cálculos por patamares de usinas térmicas.
    
    Implementa:
    - Extração de usina da query
    - Extração de inflexibilidades do CT
    - Extração de durações do DP
    - Cálculo de média ponderada
    
    Classes filhas devem implementar:
    - get_calculation_type() -> str: "disponibilidade" ou "inflexibilidade"
    - get_result_key() -> str: "disponibilidade_total" ou "inflexibilidade_total"
    - _format_result() -> Dict: formata o resultado final
    """
    
    # ⚡ OTIMIZAÇÃO: Patterns compilados UMA vez (não toda chamada)
    _CODIGO_PATTERNS = [
        re.compile(r'usina\s*(\d+)'),
        re.compile(r'usina\s*térmica\s*(\d+)'),
        re.compile(r'usina\s*termica\s*(\d+)'),
        re.compile(r'usina\s*#?\s*(\d+)'),
        re.compile(r'código\s*(\d+)'),
        re.compile(r'codigo\s*(\d+)'),
        re.compile(r'térmica\s*(\d+)'),
        re.compile(r'termica\s*(\d+)'),
        re.compile(r'ute\s*(\d+)'),
    ]
    
    # ⚡ OTIMIZAÇÃO: Palavras ignoradas como frozenset (busca O(1))
    _PALAVRAS_IGNORAR = frozenset({
        'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 
        'em', 'na', 'no', 'nas', 'nos', 'qual', 'disponibilidade', 'inflexibilidade'
    })
    
    def get_calculation_type(self) -> str:
        """Retorna o tipo de cálculo: 'disponibilidade' ou 'inflexibilidade'"""
        raise NotImplementedError("Subclasses devem implementar get_calculation_type()")
    
    def get_result_key(self) -> str:
        """Retorna a chave do resultado: 'disponibilidade_total' ou 'inflexibilidade_total'"""
        raise NotImplementedError("Subclasses devem implementar get_result_key()")
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa o cálculo - lógica comum para todas as tools.
        
        OTIMIZADO: Carrega CT apenas UMA vez e passa para os métodos.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from backend.decomp.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            verbose = kwargs.get("verbose", True)
            forced_plant_code = kwargs.get("forced_plant_code")
            calc_type = self.get_calculation_type()
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Query recebida: {query}")
            
            # ⚡ OTIMIZAÇÃO: Carregar CT DataFrame UMA ÚNICA VEZ
            ct_df = dadger.ct(estagio=1, df=True)
            if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
                return {
                    "success": False,
                    "error": "Dados do bloco CT (estágio 1) não encontrados"
                }
            
            # Priorizar código vindo do follow-up (__PLANT_CORR__) se disponível
            if forced_plant_code is not None:
                codigo_usina = int(forced_plant_code)
                safe_print(f"[{calc_type.upper()} TOOL] ⚙️ Código forçado recebido via follow-up: {codigo_usina}")
            else:
                # Passar ct_df já carregado para evitar leituras duplicadas
                codigo_usina = self._extract_usina_from_query_fast(query, ct_df)
            
            if codigo_usina is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar a usina na query. Por favor, especifique o nome ou código da usina (ex: '{calc_type} de Cubatao' ou '{calc_type} da usina 97')"
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Usina identificada: código {codigo_usina}")
            
            # ⚡ Chamar método otimizado passando ct_df já carregado
            return self._execute_with_ct_loaded(codigo_usina, dadger, ct_df, verbose=verbose)
            
        except Exception as e:
            calc_type = self.get_calculation_type()
            safe_print(f"[{calc_type.upper()} TOOL] ❌ Erro ao calcular {calc_type}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular {calc_type}: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_usina_from_query_fast(self, query: str, ct_df: pd.DataFrame) -> Optional[int]:
        """
        ⚡ VERSÃO OTIMIZADA: Extrai código da usina da query usando DecompThermalPlantMatcher.
        Recebe ct_df já carregado para evitar leituras duplicadas.
        
        Args:
            query: Query do usuário
            ct_df: DataFrame do bloco CT já carregado
            
        Returns:
            Código da usina ou None
        """
        calc_type = self.get_calculation_type()
        
        # Usar matcher DECOMP com CSV como fonte de verdade
        matcher = get_decomp_thermal_plant_matcher()
        
        # O matcher usa CSV como fonte de verdade, mas valida contra DataFrame
        codigo = matcher.extract_plant_from_query(
            query=query,
            available_plants=ct_df,
            entity_type="usina",
            threshold=0.5
        )
        
        if codigo is not None:
            safe_print(f"[{calc_type.upper()} TOOL] ✅ Código {codigo} encontrado via DecompThermalPlantMatcher")
        else:
            safe_print(f"[{calc_type.upper()} TOOL] ⚠️ Nenhuma usina específica detectada na query")
        
        return codigo
    
    def _execute_with_ct_loaded(
        self, 
        codigo_usina: int, 
        dadger: Any,
        ct_df: pd.DataFrame,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        ⚡ VERSÃO OTIMIZADA: Executa cálculo com ct_df já carregado.
        Evita leitura duplicada do bloco CT.
        
        Args:
            codigo_usina: Código da usina já identificado
            dadger: Objeto Dadger já carregado
            ct_df: DataFrame do bloco CT já carregado
            verbose: Se True, exibe logs detalhados
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            calc_type = self.get_calculation_type()
            
            # ⚡ OTIMIZAÇÃO: Não precisa chamar dadger.ct() novamente!
            # Filtrar diretamente no DataFrame já carregado
            ct_filtrado = ct_df[ct_df['codigo_usina'] == codigo_usina]
            
            if ct_filtrado.empty:
                return {
                    "success": False,
                    "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                }
            
            ct_record = ct_filtrado.iloc[0].to_dict()
            
            # Extrair informações da usina
            nome_usina = str(ct_record.get('nome_usina', '')).strip() or f"Usina {codigo_usina}"
            codigo_submercado = ct_record.get('codigo_submercado') or ct_record.get('submercado')
            
            if codigo_submercado is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar o submercado da usina {codigo_usina}"
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Submercado identificado: {codigo_submercado}")
            
            # Extrair inflexibilidades dos 3 patamares
            inflexibilidades = self._extract_inflexibilidades(ct_record)
            
            if not inflexibilidades or all(v is None for v in inflexibilidades.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair inflexibilidades da usina {codigo_usina} no bloco CT"
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Inflexibilidades: {inflexibilidades}")
            
            # Buscar dados do DP (estágio 1, submercado)
            dp_data = dadger.dp(
                codigo_submercado=codigo_submercado,
                estagio=1,
                df=True
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} (estágio 1)"
                }
            
            # Filtrar DP
            dp_record = None
            if isinstance(dp_data, pd.DataFrame):
                for col_sub in ['codigo_submercado', 'submercado', 's']:
                    if col_sub in dp_data.columns:
                        dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                        if not dp_filtrado.empty:
                            dp_record = dp_filtrado.iloc[0].to_dict()
                            break
            
            if dp_record is None:
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} no estágio 1"
                }
            
            # Extrair durações dos patamares
            duracoes = self._extract_duracoes(dp_record)
            
            if not duracoes or all(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Durações: {duracoes}")
            
            # Calcular média ponderada (mesma fórmula para disponibilidade e inflexibilidade)
            resultado = self._calcular_media_ponderada(inflexibilidades, duracoes)
            
            if resultado is None:
                return {
                    "success": False,
                    "error": f"Erro ao calcular {calc_type}. Verifique se todos os dados necessários estão disponíveis."
                }
            
            # Formatar resultado usando método da classe filha
            return self._format_result(
                codigo_usina,
                nome_usina,
                codigo_submercado,
                inflexibilidades,
                duracoes,
                resultado
            )
            
        except Exception as e:
            calc_type = self.get_calculation_type()
            safe_print(f"[{calc_type.upper()} TOOL] ❌ Erro ao calcular {calc_type}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular {calc_type}: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_inflexibilidades(self, ct_record: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        ⚡ OTIMIZADO: Extrai inflexibilidades dos 3 patamares do registro CT.
        Removidos logs excessivos dentro de loops.
        
        Args:
            ct_record: Registro do bloco CT
            
        Returns:
            Dict com inflexibilidades por patamar (pesada, media, leve)
        """
        inflexibilidades = {
            "pesada": None,
            "media": None,
            "leve": None
        }
        
        # ⚡ OTIMIZAÇÃO: Criar set de chaves uma vez
        ct_keys = set(ct_record.keys())
        
        # Tentar múltiplas variações de nomes de campos
        for patamar_idx, patamar_nome in [(1, "pesada"), (2, "media"), (3, "leve")]:
            valor = None
            
            # ⚡ OTIMIZAÇÃO: Tentar variações mais comuns primeiro
            common_keys = [
                f"inflexibilidade_patamar_{patamar_idx}",
                f"inflexibilidade_{patamar_idx}",
                f"inflexibilidade_pat{patamar_idx}",
            ]
            
            for key in common_keys:
                if key in ct_keys:
                    # Verificar explicitamente se não é None (0 é um valor válido!)
                    if ct_record[key] is not None:
                        valor = ct_record[key]
                        break
            
            # Fallback: buscar por padrão (sem logs)
            if valor is None:
                for key, value in ct_record.items():
                    # Verificar se é número (incluindo 0) e não None
                    if value is not None and isinstance(value, (int, float)):
                        key_lower = str(key).lower()
                        if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                            f"_{patamar_idx}" in key_lower) and ("inflexibilidade" in key_lower):
                            valor = value
                            break
            
            # Se encontrou valor (incluindo 0), converter para float
            if valor is not None:
                try:
                    # 0 é um valor válido - converter explicitamente
                    inflexibilidades[patamar_nome] = float(valor)
                except (ValueError, TypeError):
                    pass  # Silencioso - erro será capturado depois
        
        return inflexibilidades
    
    def _extract_duracoes(self, dp_record: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        ⚡ OTIMIZADO: Extrai durações dos 3 patamares do registro DP.
        Removidos logs excessivos dentro de loops.
        
        Args:
            dp_record: Registro do bloco DP
            
        Returns:
            Dict com durações por patamar (pesada, media, leve) em horas
        """
        duracoes = {
            "pesada": None,
            "media": None,
            "leve": None
        }
        
        # ⚡ OTIMIZAÇÃO: Criar set de chaves uma vez
        dp_keys = set(dp_record.keys())
        
        # Tentar múltiplas variações de nomes de campos
        for patamar_idx, patamar_nome in [(1, "pesada"), (2, "media"), (3, "leve")]:
            valor = None
            
            # ⚡ OTIMIZAÇÃO: Tentar variações mais comuns primeiro
            common_keys = [
                f"duracao_patamar_{patamar_idx}",
                f"duracao_{patamar_idx}",
                f"horas_patamar_{patamar_idx}",
                f"horas_{patamar_idx}",
            ]
            
            for key in common_keys:
                if key in dp_keys and dp_record[key] is not None:
                    valor = dp_record[key]
                    break
            
            # Fallback: buscar por padrão (sem logs)
            if valor is None:
                for key, value in dp_record.items():
                    if value is not None and isinstance(value, (int, float)):
                        key_lower = str(key).lower()
                        if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                            f"_{patamar_idx}" in key_lower) and ("hora" in key_lower or "duracao" in key_lower):
                            valor = value
                            break
            
            if valor is not None:
                try:
                    duracoes[patamar_nome] = float(valor)
                except (ValueError, TypeError):
                    pass  # Silencioso - erro será capturado depois
        
        return duracoes
    
    def _calcular_media_ponderada(
        self, 
        valores: Dict[str, Optional[float]], 
        duracoes: Dict[str, Optional[float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula média ponderada usando a fórmula especificada.
        Mesma fórmula para disponibilidade e inflexibilidade.
        
        Args:
            valores: Dict com valores por patamar (pesada, media, leve) - inflexibilidades
            duracoes: Dict com durações por patamar em horas (pesada, media, leve)
            
        Returns:
            Dict com resultado do cálculo ou None se houver erro
        """
        # Validar que temos todos os dados necessários (verificar None, não valores falsy como 0.0)
        # 0.0 é um valor válido! Significa que a usina não tem inflexibilidade naquele patamar
        if any(v is None for v in valores.values()) or any(v is None for v in duracoes.values()):
            calc_type = self.get_calculation_type()
            safe_print(f"[{calc_type.upper()} TOOL] [ERRO] Dados incompletos: valores={valores}, duracoes={duracoes}")
            return None
        
        # Extrair valores (0.0 é válido e deve ser considerado!)
        val_pesada = valores.get("pesada", 0) or 0
        val_media = valores.get("media", 0) or 0
        val_leve = valores.get("leve", 0) or 0
        
        dur_pesada = duracoes.get("pesada", 0) or 0
        dur_media = duracoes.get("media", 0) or 0
        dur_leve = duracoes.get("leve", 0) or 0
        
        # Calcular numerador: (Val_Leve × Dur_Leve + Val_Médio × Dur_Médio + Val_Pesada × Dur_Pesada)
        numerador = (val_leve * dur_leve) + (val_media * dur_media) + (val_pesada * dur_pesada)
        
        # Calcular denominador: (Dur_Leve + Dur_Médio + Dur_Pesada)
        denominador = dur_leve + dur_media + dur_pesada
        
        if denominador == 0:
            calc_type = self.get_calculation_type()
            safe_print(f"[{calc_type.upper()} TOOL] [ERRO] Denominador zero (soma das durações = 0)")
            return None
        
        # Calcular total (média ponderada)
        total = numerador / denominador
        
        return {
            "total": round(total, 2),
            "calculo": {
                "numerador": round(numerador, 2),
                "denominador": round(denominador, 2),
                "resultado": round(total, 2)
            }
        }
    
    def _format_result(
        self,
        codigo_usina: int,
        nome_usina: str,
        codigo_submercado: int,
        inflexibilidades: Dict[str, Optional[float]],
        duracoes: Dict[str, Optional[float]],
        resultado: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formata resultado final - deve ser sobrescrito pelas classes filhas.
        
        Args:
            codigo_usina: Código da usina
            nome_usina: Nome da usina
            codigo_submercado: Código do submercado
            inflexibilidades: Dict com inflexibilidades por patamar
            duracoes: Dict com durações por patamar
            resultado: Dict com resultado do cálculo (contém "total" e "calculo")
            
        Returns:
            Dict formatado com resultado
        """
        raise NotImplementedError("Subclasses devem implementar _format_result()")

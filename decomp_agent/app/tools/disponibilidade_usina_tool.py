"""
Tool para calcular disponibilidade total de uma usina termelétrica.
Combina dados dos blocos CT (disponibilidades) e DP (durações dos patamares).

OTIMIZADO: Herda de PatamarCalculationBase, reutiliza toda a lógica comum.
"""
from decomp_agent.app.tools.patamar_calculation_base import PatamarCalculationBase
from decomp_agent.app.config import safe_print
from typing import Dict, Any, Optional
import pandas as pd


class DisponibilidadeUsinaTool(PatamarCalculationBase):
    """
    Tool para calcular disponibilidade total de uma usina termelétrica.
    
    Combina dados de:
    - Bloco CT: Disponibilidades por patamar (PESADA, MEDIA, LEVE)
    - Bloco DP: Durações dos patamares em horas
    
    Fórmula:
    Disponibilidade Total = 
      (Disponibilidade_Leve × Duração_Leve + 
       Disponibilidade_Médio × Duração_Médio + 
       Disponibilidade_Pesada × Duração_Pesada) 
      / 
      (Duração_Leve + Duração_Médio + Duração_Pesada)
    """
    
    def get_name(self) -> str:
        return "DisponibilidadeUsinaTool"
    
    def get_calculation_type(self) -> str:
        # Usado apenas para mensagens de erro e logs
        return "disponibilidade"
    
    def get_result_key(self) -> str:
        return "disponibilidade_total"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cálculo de disponibilidade de usina.
        """
        query_lower = query.lower()
        keywords = [
            "disponibilidade",
            "disponibilidade usina",
            "disponibilidade da usina",
            "calcular disponibilidade",
            "disponibilidade total",
            "disponibilidade de",
            "disponibilidade cubatao",
            "disponibilidade angra",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para calcular disponibilidade total de uma usina termelétrica.
        
        Combina dados dos blocos CT e DP do DECOMP:
        - Bloco CT: Disponibilidades por patamar (PESADA, MEDIA, LEVE) no estágio 1
        - Bloco DP: Durações dos patamares em horas no estágio 1
        
        Fórmula de cálculo:
        Disponibilidade Total = 
          (Disponibilidade_Leve × Duração_Leve + 
           Disponibilidade_Médio × Duração_Médio + 
           Disponibilidade_Pesada × Duração_Pesada) 
          / 
          (Duração_Leve + Duração_Médio + Duração_Pesada)
        
        Exemplos de queries:
        - "Qual a disponibilidade de Cubatao?"
        - "Calcular disponibilidade da usina 97"
        - "Disponibilidade total de Angra 1"
        """
    
    def _extract_disponibilidades(self, ct_record: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extrai disponibilidades dos 3 patamares do registro CT.
        
        A lógica é análoga à extração de inflexibilidades em PatamarCalculationBase,
        mas procurando por campos de disponibilidade_*.
        """
        disponibilidades = {
            "pesada": None,
            "media": None,
            "leve": None,
        }
        
        ct_keys = set(ct_record.keys())
        
        for patamar_idx, patamar_nome in [(1, "pesada"), (2, "media"), (3, "leve")]:
            valor = None
            
            # Primeiro, tentar os campos mais comuns do CTTool
            common_keys = [
                f"disponibilidade_{patamar_idx}",
                f"disponibilidade_patamar_{patamar_idx}",
                f"disponibilidade_pat{patamar_idx}",
            ]
            
            for key in common_keys:
                if key in ct_keys and ct_record[key] is not None:
                    valor = ct_record[key]
                    break
            
            # Fallback: varrer chaves procurando por "disponibilidade" + índice de patamar
            if valor is None:
                for key, value in ct_record.items():
                    if value is None:
                        continue
                    if not isinstance(value, (int, float)):
                        continue
                    key_lower = str(key).lower()
                    if (
                        "disponibilidade" in key_lower
                        and (
                            f"pat{patamar_idx}" in key_lower
                            or f"patamar{patamar_idx}" in key_lower
                            or f"_{patamar_idx}" in key_lower
                        )
                    ):
                        valor = value
                        break
            
            if valor is not None:
                try:
                    disponibilidades[patamar_nome] = float(valor)
                except (ValueError, TypeError):
                    # Se não conseguir converter, deixa como None
                    pass
        
        return disponibilidades
    
    def _format_result(
        self,
        codigo_usina: int,
        nome_usina: str,
        codigo_submercado: int,
        disponibilidades: Dict[str, Optional[float]],
        duracoes: Dict[str, Optional[float]],
        resultado: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Formata resultado para disponibilidade.
        
        Mantém estrutura muito próxima da InflexibilidadeUsinaTool, mas com chave
        disponibilidade_total e campos de detalhes rotulados como disponibilidade.
        """
        return {
            "success": True,
            "disponibilidade_total": resultado["total"],
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina,
                "submercado": codigo_submercado,
            },
            "detalhes": {
                "pesada": {
                    "disponibilidade": disponibilidades.get("pesada"),
                    "duracao": duracoes.get("pesada"),
                },
                "media": {
                    "disponibilidade": disponibilidades.get("media"),
                    "duracao": duracoes.get("media"),
                },
                "leve": {
                    "disponibilidade": disponibilidades.get("leve"),
                    "duracao": duracoes.get("leve"),
                },
            },
            "calculo": resultado["calculo"],
            "tool": self.get_name(),
        }
    
    def _execute_with_ct_loaded(
        self,
        codigo_usina: int,
        dadger: Any,
        ct_df: pd.DataFrame,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Versão otimizada do execute, reaproveitando ct_df já carregado,
        mas usando disponibilidades em vez de inflexibilidades.
        """
        try:
            calc_type = self.get_calculation_type()
            
            ct_filtrado = ct_df[ct_df["codigo_usina"] == codigo_usina]
            if ct_filtrado.empty:
                return {
                    "success": False,
                    "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)",
                }
            
            ct_record = ct_filtrado.iloc[0].to_dict()
            
            nome_usina = str(ct_record.get("nome_usina", "")).strip() or f"Usina {codigo_usina}"
            codigo_submercado = ct_record.get("codigo_submercado") or ct_record.get("submercado")
            if codigo_submercado is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar o submercado da usina {codigo_usina}",
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Submercado identificado: {codigo_submercado}")
            
            # Extrair disponibilidades por patamar
            disponibilidades = self._extract_disponibilidades(ct_record)
            if not disponibilidades or all(v is None for v in disponibilidades.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair disponibilidades da usina {codigo_usina} no bloco CT",
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Disponibilidades: {disponibilidades}")
            
            # Buscar dados do DP (estágio 1, submercado)
            dp_data = dadger.dp(codigo_submercado=codigo_submercado, estagio=1, df=True)
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} (estágio 1)",
                }
            
            dp_record = None
            if isinstance(dp_data, pd.DataFrame):
                for col_sub in ["codigo_submercado", "submercado", "s"]:
                    if col_sub in dp_data.columns:
                        dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                        if not dp_filtrado.empty:
                            dp_record = dp_filtrado.iloc[0].to_dict()
                            break
            
            if dp_record is None:
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} no estágio 1",
                }
            
            # Extrair durações
            duracoes = self._extract_duracoes(dp_record)
            if not duracoes or all(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": "Não foi possível extrair durações dos patamares do bloco DP",
                }
            
            if verbose:
                safe_print(f"[{calc_type.upper()} TOOL] Durações: {duracoes}")
            
            # Calcular média ponderada
            resultado = self._calcular_media_ponderada(disponibilidades, duracoes)
            if resultado is None:
                return {
                    "success": False,
                    "error": "Erro ao calcular disponibilidade. Verifique se todos os dados necessários estão disponíveis.",
                }
            
            return self._format_result(
                codigo_usina,
                nome_usina,
                codigo_submercado,
                disponibilidades,
                duracoes,
                resultado,
            )
        
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ❌ Erro ao calcular disponibilidade: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular disponibilidade: {str(e)}",
                "tool": self.get_name(),
            }
    
    # Manter método execute_with_codigo_usina para compatibilidade com futuros multi-decks
    def execute_with_codigo_usina(
        self,
        codigo_usina: int,
        dadger: Any,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o cálculo de disponibilidade para uma usina (versão otimizada).
        Usa os mesmos dados já carregados que as outras tools por patamar.
        """
        try:
            ct_data = dadger.ct(estagio=1, df=True)
            if ct_data is None or (isinstance(ct_data, pd.DataFrame) and ct_data.empty):
                return {
                    "success": False,
                    "error": "Dados do bloco CT (estágio 1) não encontrados",
                }
            
            # Reaproveita a lógica de _execute_with_ct_loaded para não duplicar código
            return self._execute_with_ct_loaded(
                codigo_usina=codigo_usina,
                dadger=dadger,
                ct_df=ct_data,
                verbose=verbose,
            )
        
        except Exception as e:
            safe_print(f"[DISPONIBILIDADE TOOL] ❌ Erro ao calcular disponibilidade (execute_with_codigo_usina): {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular disponibilidade: {str(e)}",
                "tool": self.get_name(),
            }

"""
Tool para calcular inflexibilidade total de uma usina termelétrica.
Combina dados dos blocos CT (inflexibilidades) e DP (durações dos patamares).

OTIMIZADO: Herda de PatamarCalculationBase, reutiliza toda a lógica comum.
"""
from decomp_agent.app.tools.patamar_calculation_base import PatamarCalculationBase
from decomp_agent.app.config import safe_print
from typing import Dict, Any, Optional
import pandas as pd


class InflexibilidadeUsinaTool(PatamarCalculationBase):
    """
    Tool para calcular inflexibilidade total de uma usina termelétrica.
    
    Combina dados de:
    - Bloco CT: Inflexibilidades por patamar (PESADA, MEDIA, LEVE)
    - Bloco DP: Durações dos patamares em horas
    
    Fórmula:
    Inflexibilidade Total = 
      (Inflexibilidade_Leve × Duração_Leve + 
       Inflexibilidade_Médio × Duração_Médio + 
       Inflexibilidade_Pesada × Duração_Pesada) 
      / 
      (Duração_Leve + Duração_Médio + Duração_Pesada)
    """
    
    def get_name(self) -> str:
        return "InflexibilidadeUsinaTool"
    
    def get_calculation_type(self) -> str:
        return "inflexibilidade"
    
    def get_result_key(self) -> str:
        return "inflexibilidade_total"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cálculo de inflexibilidade de usina.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "inflexibilidade",
            "inflexibilidade usina",
            "inflexibilidade da usina",
            "calcular inflexibilidade",
            "inflexibilidade total",
            "inflexibilidade de",
            "inflexibilidade cubatao",
            "inflexibilidade angra",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para calcular inflexibilidade total de uma usina termelétrica.
        
        Combina dados dos blocos CT e DP do DECOMP:
        - Bloco CT: Inflexibilidades por patamar (PESADA, MEDIA, LEVE) no estágio 1
        - Bloco DP: Durações dos patamares em horas no estágio 1
        
        Fórmula de cálculo:
        Inflexibilidade Total = 
          (Inflexibilidade_Leve × Duração_Leve + 
           Inflexibilidade_Médio × Duração_Médio + 
           Inflexibilidade_Pesada × Duração_Pesada) 
          / 
          (Duração_Leve + Duração_Médio + Duração_Pesada)
        
        Exemplos de queries:
        - "Qual a inflexibilidade de Cubatao?"
        - "Calcular inflexibilidade da usina 97"
        - "Inflexibilidade total de Angra 1"
        """
    
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
        Formata resultado para inflexibilidade.
        
        Args:
            codigo_usina: Código da usina
            nome_usina: Nome da usina
            codigo_submercado: Código do submercado
            inflexibilidades: Dict com inflexibilidades por patamar
            duracoes: Dict com durações por patamar
            resultado: Dict com resultado do cálculo (contém "total" e "calculo")
            
        Returns:
            Dict formatado com resultado de inflexibilidade
        """
        return {
            "success": True,
            "inflexibilidade_total": resultado["total"],
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina,
                "submercado": codigo_submercado
            },
            "detalhes": {
                "pesada": {
                    "inflexibilidade": inflexibilidades.get("pesada"),
                    "duracao": duracoes.get("pesada")
                },
                "media": {
                    "inflexibilidade": inflexibilidades.get("media"),
                    "duracao": duracoes.get("media")
                },
                "leve": {
                    "inflexibilidade": inflexibilidades.get("leve"),
                    "duracao": duracoes.get("leve")
                }
            },
            "calculo": resultado["calculo"],
            "tool": self.get_name()
        }
    
    # Manter método execute_with_codigo_usina para compatibilidade com multi-deck
    def execute_with_codigo_usina(
        self, 
        codigo_usina: int, 
        dadger: Any,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Executa o cálculo de inflexibilidade para uma usina (versão otimizada).
        Pula leitura de arquivo e extração de usina da query.
        
        Mantido para compatibilidade com InflexibilidadeMultiDeckTool.
        
        Args:
            codigo_usina: Código da usina já identificado
            dadger: Objeto Dadger já carregado
            verbose: Se True, exibe logs detalhados
            
        Returns:
            Dict com resultado do cálculo e detalhes
        """
        try:
            # Carregar CT
            ct_data = dadger.ct(estagio=1, df=True)
            
            if ct_data is None or (isinstance(ct_data, pd.DataFrame) and ct_data.empty):
                return {
                    "success": False,
                    "error": f"Dados do bloco CT (estágio 1) não encontrados"
                }
            
            # Filtrar pelo código
            if isinstance(ct_data, pd.DataFrame):
                ct_filtrado = ct_data[ct_data['codigo_usina'] == codigo_usina]
                if ct_filtrado.empty:
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                    }
                ct_record = ct_filtrado.iloc[0].to_dict()
            else:
                ct_records = [ct_data] if not isinstance(ct_data, list) else ct_data
                ct_records = [r for r in ct_records if r.get('codigo_usina') == codigo_usina]
                if not ct_records:
                    return {
                        "success": False,
                        "error": f"Usina {codigo_usina} não encontrada no bloco CT (estágio 1)"
                    }
                ct_record = ct_records[0]
                if isinstance(ct_record, pd.Series):
                    ct_record = ct_record.to_dict()
            
            # Extrair informações
            nome_usina = str(ct_record.get('nome_usina', '')).strip() or f"Usina {codigo_usina}"
            codigo_submercado = ct_record.get('codigo_submercado') or ct_record.get('submercado')
            
            if codigo_submercado is None:
                return {
                    "success": False,
                    "error": f"Não foi possível identificar o submercado da usina {codigo_usina}"
                }
            
            # Extrair inflexibilidades
            inflexibilidades = self._extract_inflexibilidades(ct_record)
            
            # Verificar se todas as inflexibilidades são None (0 é um valor válido!)
            # Se todas forem None, significa que não encontrou os dados
            # Se alguma for 0, isso é válido e deve prosseguir com o cálculo
            if not inflexibilidades or all(v is None for v in inflexibilidades.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair inflexibilidades da usina {codigo_usina} no bloco CT"
                }
            
            # Buscar DP
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
                            for col_est in ['estagio', 'ip']:
                                if col_est in dp_filtrado.columns:
                                    dp_filtrado_est = dp_filtrado[dp_filtrado[col_est].fillna(1) == 1]
                                    if not dp_filtrado_est.empty:
                                        dp_record = dp_filtrado_est.iloc[0].to_dict()
                                        break
                            if dp_record is None:
                                dp_record = dp_filtrado.iloc[0].to_dict()
                            if dp_record:
                                break
                
                if dp_record is None:
                    for col_sub in ['codigo_submercado', 'submercado', 's']:
                        if col_sub in dp_data.columns:
                            dp_filtrado = dp_data[dp_data[col_sub] == codigo_submercado]
                            if not dp_filtrado.empty:
                                dp_record = dp_filtrado.iloc[0].to_dict()
                                break
            else:
                dp_records = [dp_data] if not isinstance(dp_data, list) else dp_data
                for record in dp_records:
                    if isinstance(record, pd.Series):
                        record = record.to_dict()
                    record_submercado = (
                        record.get('codigo_submercado') or 
                        record.get('submercado') or 
                        record.get('s')
                    )
                    record_estagio = record.get('estagio') or record.get('ip')
                    if record_submercado == codigo_submercado:
                        if record_estagio is None or record_estagio == 1:
                            dp_record = record
                            break
                
                if dp_record is None:
                    for record in dp_records:
                        if isinstance(record, pd.Series):
                            record = record.to_dict()
                        record_submercado = (
                            record.get('codigo_submercado') or 
                            record.get('submercado') or 
                            record.get('s')
                        )
                        if record_submercado == codigo_submercado:
                            dp_record = record
                            break
            
            if dp_record is None:
                return {
                    "success": False,
                    "error": f"Dados do bloco DP não encontrados para submercado {codigo_submercado} no estágio 1"
                }
            
            # Extrair durações
            duracoes = self._extract_duracoes(dp_record)
            
            if not duracoes or all(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": f"Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            # Calcular
            resultado = self._calcular_media_ponderada(inflexibilidades, duracoes)
            
            if resultado is None:
                return {
                    "success": False,
                    "error": "Erro ao calcular inflexibilidade. Verifique se todos os dados necessários estão disponíveis."
                }
            
            # Formatar resultado
            return self._format_result(
                codigo_usina,
                nome_usina,
                codigo_submercado,
                inflexibilidades,
                duracoes,
                resultado
            )
            
        except Exception as e:
            safe_print(f"[INFLEXIBILIDADE TOOL] ❌ Erro ao calcular inflexibilidade: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao calcular inflexibilidade: {str(e)}",
                "tool": self.get_name()
            }

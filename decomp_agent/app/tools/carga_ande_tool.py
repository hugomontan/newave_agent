"""
Tool para consultar informações de Carga ANDE (participação da ANDE na Itaipu) do Bloco RI do DECOMP.
Calcula média ponderada dos valores ANDE dos 3 patamares.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import pandas as pd
from typing import Dict, Any, Optional

# Código padrão da UHE Itaipu
ITAIPU_CODIGO = 66

# Mapeamento de códigos de submercado para regiões
SUBMERCADO_TO_REGIAO = {
    1: "SUDESTE/CENTRO-OESTE",
    2: "SUL",
    3: "NORDESTE",
    4: "NORTE"
}


class CargaAndeTool(DECOMPTool):
    """
    Tool para consultar informações de Carga ANDE (participação da ANDE na Itaipu) do Bloco RI do DECOMP.
    
    Específica para Single Deck:
    - Apenas estágio 1
    - Apenas usina 66 (Itaipu)
    - Sem filtros opcionais
    - Cálculo ponderado pelas horas por patamar
    - Output: tabela por patamares e horas + MW médio
    """
    
    def get_name(self) -> str:
        return "CargaAndeTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga ANDE.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "carga ande",
            "ande itaipu",
            "participação ande",
            "participacao ande",
            "ande",
            "bloco ri ande",
            "restrição itaipu ande",
            "restricao itaipu ande",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações de Carga ANDE (participação da ANDE na Itaipu) do Bloco RI do DECOMP.
        
        Específica para Single Deck:
        - Apenas estágio 1
        - Apenas usina 66 (Itaipu)
        - Cálculo ponderado pelas horas por patamar
        - Output: tabela por patamares e horas + MW médio
        
        Exemplos de queries:
        - "Carga ANDE"
        - "ANDE Itaipu"
        - "Participação ANDE"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre carga ANDE do Bloco RI.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados da carga ANDE formatados
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from decomp_agent.app.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            # SEMPRE usar estágio 1, usina 66 (Itaipu)
            estagio = 1
            codigo_usina = ITAIPU_CODIGO
            
            safe_print(f"[CARGA ANDE TOOL] Query recebida: {query}")
            safe_print(f"[CARGA ANDE TOOL] Buscando RI estágio {estagio}, usina {codigo_usina}")
            
            # Obter dados do bloco RI (estágio 1, usina 66)
            ri_data = dadger.ri(
                codigo_usina=codigo_usina,
                estagio=estagio,
                df=True  # Retornar como DataFrame
            )
            
            if ri_data is None or (isinstance(ri_data, pd.DataFrame) and ri_data.empty):
                return {
                    "success": False,
                    "error": f"Nenhum registro RI encontrado para usina {codigo_usina} no estágio {estagio}"
                }
            
            # Filtrar apenas estágio 1 (garantia)
            if isinstance(ri_data, pd.DataFrame):
                if "estagio" in ri_data.columns:
                    ri_data = ri_data[ri_data["estagio"] == estagio].copy()
                
                # Filtrar por usina 66 (garantia)
                col_usina = None
                for col in ["codigo_usina", "uhe", "codigo_uhe"]:
                    if col in ri_data.columns:
                        col_usina = col
                        break
                
                if col_usina:
                    ri_data = ri_data[ri_data[col_usina] == codigo_usina].copy()
                
                safe_print(f"[CARGA ANDE TOOL] Total de registros RI: {len(ri_data)}")
            
            if ri_data.empty if isinstance(ri_data, pd.DataFrame) else not ri_data:
                return {
                    "success": False,
                    "error": f"Nenhum registro RI encontrado para usina {codigo_usina} no estágio {estagio}"
                }
            
            # Obter durações dos patamares do bloco DP (estágio 1)
            dp_data = dadger.dp(
                estagio=estagio,
                df=True
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": "Nenhum registro de duração de patamares encontrado no estágio 1"
                }
            
            # Filtrar apenas estágio 1
            if isinstance(dp_data, pd.DataFrame):
                if "estagio" in dp_data.columns:
                    dp_data = dp_data[dp_data["estagio"] == estagio].copy()
            
            # Extrair durações por patamar
            duracoes = self._extrair_duracoes_patamares(dp_data)
            
            if not duracoes or any(v is None for v in duracoes.values()):
                return {
                    "success": False,
                    "error": "Não foi possível extrair durações dos patamares do bloco DP"
                }
            
            # Processar dados: extrair valores ANDE por patamar e calcular MW médio
            data = []
            registros = ri_data.to_dict('records') if isinstance(ri_data, pd.DataFrame) else []
            
            # Pegar apenas o primeiro registro (Itaipu no estágio 1)
            if registros:
                registro = registros[0]
                
                codigo_submercado_reg = (
                    registro.get("codigo_submercado") or
                    registro.get("submercado") or
                    registro.get("s") or
                    1  # Default: Sudeste
                )
                regiao = self._mapear_submercado_para_regiao(codigo_submercado_reg)
                
                # Extrair valores ANDE por patamar
                valores_ande = self._extrair_valores_ande(registro)
                
                # Calcular MW médio ponderado
                carga_ande_media_ponderada = self._calcular_carga_ande_media_ponderada(valores_ande, duracoes)
                
                # Estruturar dados do patamar
                patamares = {
                    "pesada": {
                        "carga_ande": valores_ande.get("pesada"),
                        "duracao_horas": duracoes.get("pesada")
                    },
                    "media": {
                        "carga_ande": valores_ande.get("media"),
                        "duracao_horas": duracoes.get("media")
                    },
                    "leve": {
                        "carga_ande": valores_ande.get("leve"),
                        "duracao_horas": duracoes.get("leve")
                    }
                }
                
                data.append({
                    "estagio": estagio,
                    "codigo_usina": codigo_usina,
                    "nome_usina": "ITAIPU",
                    "codigo_submercado": codigo_submercado_reg,
                    "regiao": regiao,
                    "carga_ande_media_ponderada": carga_ande_media_ponderada,
                    "mw_medio": carga_ande_media_ponderada,  # Alias para compatibilidade
                    "patamares": patamares
                })
            
            if not data:
                return {
                    "success": False,
                    "error": f"Nenhum registro de carga ANDE encontrado para usina {codigo_usina} no estágio {estagio}"
                }
            
            safe_print(f"[CARGA ANDE TOOL] ✅ Carga ANDE média ponderada: {data[0].get('carga_ande_media_ponderada')} MW")
            
            return {
                "success": True,
                "data": data,
                "total_registros": len(data),
                "calcular_media_ponderada": True,
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[CARGA ANDE TOOL] ❌ Erro ao consultar Carga ANDE: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Carga ANDE: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extrair_duracoes_patamares(self, dp_data: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Extrai durações dos patamares do DataFrame DP.
        
        Args:
            dp_data: DataFrame com dados do bloco DP
            
        Returns:
            Dict com durações por patamar: {"pesada": X, "media": Y, "leve": Z}
        """
        duracoes = {"pesada": None, "media": None, "leve": None}
        
        if dp_data is None or dp_data.empty:
            return duracoes
        
        # Tentar extrair durações do primeiro registro (assumindo que são iguais para todos no estágio 1)
        primeiro_registro = dp_data.iloc[0].to_dict()
        
        # Mapeamento de patamares: 1=PESADA, 2=MEDIA, 3=LEVE
        patamar_map = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        for patamar_nome, patamar_num in patamar_map.items():
            # Tentar múltiplas variações de nomes de colunas
            colunas_possiveis = [
                f"duracao_patamar_{patamar_num}",
                f"duracao_{patamar_num}",
                f"horas_{patamar_num}",
                f"horas_patamar_{patamar_num}",
                f"duracao_pat{patamar_num}",
                f"horas_pat{patamar_num}",
                f"duracao_patamar_{patamar_nome}",
                f"horas_{patamar_nome}",
            ]
            
            for col in colunas_possiveis:
                if col in primeiro_registro:
                    valor = primeiro_registro[col]
                    if valor is not None:
                        try:
                            duracoes[patamar_nome] = float(valor)
                            break
                        except (ValueError, TypeError):
                            continue
        
        return duracoes
    
    def _extrair_valores_ande(self, registro: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extrai valores ANDE por patamar do registro RI.
        
        Args:
            registro: Dict com dados do registro RI
            
        Returns:
            Dict com valores por patamar: {"pesada": X, "media": Y, "leve": Z}
        """
        valores = {"pesada": None, "media": None, "leve": None}
        
        # Mapeamento de patamares: 1=PESADA, 2=MEDIA, 3=LEVE
        patamar_map = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        for patamar_nome, patamar_num in patamar_map.items():
            # Tentar múltiplas variações de nomes de colunas para ANDE
            colunas_possiveis = [
                f"ande_patamar_{patamar_num}",
                f"ande_{patamar_num}",
                f"parte_ande_patamar_{patamar_num}",
                f"parte_ande_{patamar_num}",
                f"carga_ande_patamar_{patamar_num}",
                f"carga_ande_{patamar_num}",
                f"ande_pat{patamar_num}",
                f"parte_ande_pat{patamar_num}",
            ]
            
            for col in colunas_possiveis:
                if col in registro:
                    valor = registro[col]
                    if valor is not None:
                        try:
                            valores[patamar_nome] = float(valor)
                            break
                        except (ValueError, TypeError):
                            continue
        
        return valores
    
    def _calcular_carga_ande_media_ponderada(
        self,
        valores: Dict[str, Optional[float]],
        duracoes: Dict[str, Optional[float]]
    ) -> Optional[float]:
        """
        Calcula carga ANDE média ponderada usando a fórmula de patamares.
        
        Args:
            valores: Dict com valores ANDE por patamar {"pesada": X, "media": Y, "leve": Z}
            duracoes: Dict com durações por patamar em horas {"pesada": X, "media": Y, "leve": Z}
            
        Returns:
            Carga ANDE média ponderada ou None se houver erro
        """
        # Validar dados
        if any(v is None for v in valores.values()) or any(v is None for v in duracoes.values()):
            return None
        
        # Extrair valores (0.0 é válido!)
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
            return None
        
        # Calcular MW médio
        mw_medio = numerador / denominador
        
        return round(mw_medio, 2)
    
    def _mapear_submercado_para_regiao(self, codigo_submercado: Optional[int]) -> str:
        """
        Mapeia código de submercado para região.
        
        Args:
            codigo_submercado: Código do submercado (1-4)
            
        Returns:
            Nome da região ou "DESCONHECIDO" se código inválido
        """
        if codigo_submercado is None:
            return "DESCONHECIDO"
        
        return SUBMERCADO_TO_REGIAO.get(codigo_submercado, "DESCONHECIDO")

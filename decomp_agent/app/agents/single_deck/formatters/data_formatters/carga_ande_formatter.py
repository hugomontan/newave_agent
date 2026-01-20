"""
Formatter específico para CargaAndeTool (Bloco RI do DECOMP).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class CargaAndeSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da CargaAndeTool.
    Formata dados de Carga ANDE (participação da ANDE na Itaipu) do Bloco RI do DECOMP.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da CargaAndeTool."""
        tool_name_lower = tool_name.lower() if tool_name else ""
        return (
            tool_name == "CargaAndeTool" or
            "carga ande" in tool_name_lower or
            ("ande" in tool_name_lower and "carga" in tool_name_lower)
        )
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 90
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta da CargaAndeTool.
        
        Args:
            tool_result: Resultado da execução da tool
            tool_name: Nome da tool
            query: Query original do usuário
            
        Returns:
            Dict com final_response e visualization_data
        """
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"## Erro ao Consultar Carga ANDE\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        total_registros = tool_result.get("total_registros", len(data))
        calcular_media = tool_result.get("calcular_media_ponderada", False)
        
        if not data:
            return {
                "final_response": "## Carga ANDE\n\nNenhum registro encontrado.",
                "visualization_data": None
            }
        
        # Normalizar dados para formato padronizado
        normalized_data = self._normalize_data(data)
        
        # Extrair carga ANDE média ponderada (similar ao DP que extrai mw_medios)
        carga_ande_media_ponderada = None
        if data and len(data) > 0:
            primeiro_registro = data[0]
            carga_ande_media_ponderada = (
                primeiro_registro.get("carga_ande_media_ponderada") or
                primeiro_registro.get("mw_medio")
            )
        
        # Construir resposta em Markdown (mínima, dados aparecem na tabela)
        response_parts = []
        
        # Título (similar ao DP quando calcula média)
        if calcular_media:
            response_parts.append("## Carga ANDE Média Ponderada\n\n")
        else:
            response_parts.append("## Carga ANDE (Itaipu)\n\n")
            response_parts.append(f"Total de registros: {total_registros}\n\n")
        
        # Dados de visualização (similar ao DP)
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_with_summary" if calcular_media and carga_ande_media_ponderada is not None else "table_only",
            "tool_name": tool_name,
        }
        
        # Adicionar carga ANDE médios usando mw_medios (para compatibilidade com DPView)
        # O DPView espera mw_medios para renderizar o summary
        if calcular_media and carga_ande_media_ponderada is not None:
            # Formatar como mw_medios para que o DPView funcione
            mw_medios = [{
                "mw_medio": carga_ande_media_ponderada
            }]
            visualization_data["mw_medios"] = mw_medios
            visualization_data["carga_ande_media_ponderada"] = carga_ande_media_ponderada  # Manter para referência
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza os dados de Carga ANDE para um formato consistente.
        Expande patamares em linhas separadas para melhor visualização.
        
        Formato minimalista (Opção C):
        - PATAMAR
        - CARGA ANDE (MW)
        - DURAÇÃO (HORAS)
        
        Args:
            data: Lista de dicionários com dados da carga ANDE
            
        Returns:
            Lista de dicionários normalizados (expandidos por patamar)
        """
        from decomp_agent.app.config import safe_print
        
        normalized = []
        
        # Mapeamento de nomes de patamar
        patamar_names = {
            "pesada": "PESADA",
            "media": "MEDIA",
            "leve": "LEVE"
        }
        
        patamar_numbers = {
            "pesada": 1,
            "media": 2,
            "leve": 3
        }
        
        for registro in data:
            # Obter dados dos patamares
            patamares_dict = registro.get("patamares", {})
            
            # Expandir por patamar (pesada, media, leve)
            for patamar_key, patamar_nome in patamar_names.items():
                patamar_data = patamares_dict.get(patamar_key, {}) if patamares_dict else {}
                
                carga_ande = None
                duracao_horas = None
                
                if isinstance(patamar_data, dict):
                    carga_ande = patamar_data.get("carga_ande")
                    duracao_horas = patamar_data.get("duracao_horas")
                
                # Formato minimalista: apenas patamar, carga ANDE e duração
                normalized_record = {
                    "patamar": patamar_nome,
                    "patamar_numero": patamar_numbers.get(patamar_key),
                    "carga_ande_mw": carga_ande,
                    "duracao_horas": duracao_horas,
                }
                
                # Apenas adicionar se houver dados relevantes
                if normalized_record.get("carga_ande_mw") is not None or \
                   normalized_record.get("duracao_horas") is not None:
                    normalized.append(normalized_record)
        
        safe_print(f"[CARGA ANDE FORMATTER] Total de registros normalizados: {len(normalized)}")
        
        return normalized

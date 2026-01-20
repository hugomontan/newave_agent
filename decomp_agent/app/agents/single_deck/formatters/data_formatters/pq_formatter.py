"""
Formatter específico para PQPequenasUsinasTool (Bloco PQ do DECOMP).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from decomp_agent.app.config import safe_print


class PQSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da PQPequenasUsinasTool.
    Formata dados do Bloco PQ (Gerações das Pequenas Usinas) do DECOMP.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da PQPequenasUsinasTool."""
        return tool_name == "PQPequenasUsinasTool" or "pq" in tool_name.lower()
    
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
        Formata resposta da PQPequenasUsinasTool.
        
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
                "final_response": f"## Erro ao Consultar Bloco PQ\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        total_registros = tool_result.get("total_registros", len(data))
        filtros = tool_result.get("filtros", {})
        calcular_media = tool_result.get("calcular_media_ponderada", False)
        
        if not data:
            return {
                "final_response": "## Bloco PQ - Gerações das Pequenas Usinas\n\nNenhum registro encontrado com os filtros especificados.",
                "visualization_data": None
            }
        
        # Normalizar dados para formato de tabela (similar ao DP)
        normalized_data = self._normalize_data(data)
        
        # Extrair MW médios se houver cálculo
        mw_medios = []
        if calcular_media:
            for registro in data:
                mw_medio = registro.get("mw_medio")
                if mw_medio is not None:
                    mw_medios.append({
                        "nome": registro.get("nome"),
                        "tipo": registro.get("tipo"),
                        "regiao": registro.get("regiao"),
                        "mw_medio": mw_medio
                    })
        
        # Construir resposta em Markdown
        response_parts = []
        
        # Título baseado nos filtros
        if filtros.get("tipo") and filtros.get("regiao"):
            response_parts.append(f"## Geração {filtros['tipo']} - {filtros['regiao']}\n\n")
        elif filtros.get("tipo"):
            response_parts.append(f"## Geração {filtros['tipo']}\n\n")
        elif filtros.get("regiao"):
            response_parts.append(f"## Gerações - {filtros['regiao']}\n\n")
        else:
            response_parts.append("## Bloco PQ - Gerações das Pequenas Usinas\n\n")
        
        if calcular_media and mw_medios:
            response_parts.append(f"**Total de registros:** {total_registros}\n\n")
        else:
            response_parts.append(f"**Total de registros encontrados:** {total_registros}\n\n")
        
        # Dados de visualização
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_with_summary" if calcular_media and mw_medios else "table_only",
            "tool_name": tool_name,
            "filtros": {
                "tipo": filtros.get("tipo"),
                "regiao": filtros.get("regiao"),
                "estagio": filtros.get("estagio"),
            } if filtros else None,
        }
        
        # Adicionar MW médios se houver cálculo
        if calcular_media and mw_medios:
            visualization_data["mw_medios"] = mw_medios
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza os dados das pequenas usinas para um formato consistente.
        Expande patamares em linhas separadas para melhor visualização (similar ao DP).
        
        Args:
            data: Lista de dicionários com dados das gerações
            
        Returns:
            Lista de dicionários normalizados (expandidos por patamar)
        """
        normalized = []
        
        # Mapeamento de patamares
        patamar_map = {
            "pesada": "PESADA",
            "media": "MEDIA",
            "leve": "LEVE"
        }
        
        for registro in data:
            nome = registro.get("nome", "")
            tipo = registro.get("tipo", "OUTROS")
            regiao = registro.get("regiao", "DESCONHECIDO")
            patamares = registro.get("patamares", {})
            
            # Expandir por patamar
            for patamar_nome, patamar_label in patamar_map.items():
                patamar_data = patamares.get(patamar_nome, {})
                
                normalized_record = {
                    "nome": nome,
                    "tipo": tipo,
                    "regiao": regiao,
                    "patamar": patamar_label,
                    "patamar_numero": {"pesada": 1, "media": 2, "leve": 3}[patamar_nome],
                    "geracao_mw": patamar_data.get("geracao_mw"),
                    "duracao_horas": patamar_data.get("duracao_horas"),
                }
                
                # Apenas adicionar se houver dados relevantes
                if normalized_record.get("geracao_mw") is not None or \
                   normalized_record.get("duracao_horas") is not None:
                    normalized.append(normalized_record)
        
        return normalized

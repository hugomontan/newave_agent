"""
Formatter específico para UHUsinasHidrelétricasTool (Bloco UH do DECOMP).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class UHSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da UHUsinasHidrelétricasTool.
    Formata dados do Bloco UH (Usinas Hidrelétricas) do DECOMP.
    
    Suporta filtro por usina específica através do visualization_data.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da UHUsinasHidrelétricasTool."""
        return tool_name == "UHUsinasHidrelétricasTool" or "uh" in tool_name.lower()
    
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
        Formata resposta da UHUsinasHidrelétricasTool.
        
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
                "final_response": f"## Erro ao Consultar Bloco UH\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        total_usinas = tool_result.get("total_usinas", len(data))
        filtros = tool_result.get("filtros", {})
        mapeamento_codigo_nome = tool_result.get("mapeamento_codigo_nome", {})
        
        if not data:
            return {
                "final_response": "## Bloco UH - Usinas Hidrelétricas\n\nNenhuma usina encontrada com os filtros especificados.",
                "visualization_data": None
            }
        
        # Normalizar dados para formato padronizado
        normalized_data = self._normalize_data(data)
        
        # Construir resposta em Markdown (SIMPLIFICADA - sem markdown extenso quando há filtro por usina)
        response_parts = []
        
        # Se filtrado por usina específica, resposta mínima (dados aparecem na tabela)
        if filtros.get("codigo_usina"):
            nome_filtrado = mapeamento_codigo_nome.get(filtros['codigo_usina'], f"Usina {filtros['codigo_usina']}")
            response_parts.append(f"## Bloco UH - {nome_filtrado}\n\n")
            response_parts.append(f"Dados da usina {nome_filtrado} (Código {filtros['codigo_usina']}).\n\n")
        elif filtros.get("codigo_ree"):
            response_parts.append(f"## Bloco UH - REE {filtros['codigo_ree']}\n\n")
            response_parts.append(f"Total de usinas: {total_usinas}\n\n")
        else:
            # Sem filtro - resposta completa
            response_parts.append("## Bloco UH - Usinas Hidrelétricas\n\n")
            response_parts.append(f"**Total de usinas encontradas**: {total_usinas}\n\n")
        
        # Dados de visualização (SEM filtro no frontend - matching já feito na tool)
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_only",
            "tool_name": tool_name,
            "filtros": {
                "usina_especifica": filtros.get("codigo_usina"),
                "ree": filtros.get("codigo_ree"),
                "nome_usina": mapeamento_codigo_nome.get(filtros.get("codigo_usina")) if filtros.get("codigo_usina") else None,
            } if filtros else None,
        }
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza os dados das usinas para um formato consistente.
        
        Args:
            data: Lista de dicionários com dados das usinas
            
        Returns:
            Lista de dicionários normalizados
        """
        normalized = []
        
        for usina in data:
            # Normalizar campos (aceitar múltiplas nomenclaturas)
            normalized_usina = {
                "codigo_usina": usina.get("codigo_usina") or usina.get("codigo"),
                "codigo_ree": usina.get("codigo_ree") or usina.get("ree"),
                "volume_inicial": usina.get("volume_inicial") or usina.get("vini"),
                "vazao_minima": usina.get("vazao_minima") or usina.get("defmin"),
                "evaporacao": usina.get("evaporacao") or usina.get("evap"),
                "operacao": usina.get("operacao") or usina.get("oper"),
                "volume_morto_inicial": usina.get("volume_morto_inicial") or usina.get("vmortoin"),
                "limite_superior": usina.get("limite_superior") or usina.get("limsup"),
            }
            normalized.append(normalized_usina)
        
        return normalized

"""
Formatadores com liberdade total para LLM interpretar.
Para tools que não precisam de estruturação rígida.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List
from app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class LLMFreeFormatter(ComparisonFormatter):
    """
    Formatador genérico com liberdade total para LLM.
    Para tools como LimitesIntercambioTool, AgrintTool, RestricaoEletricaTool.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        # Este é o fallback - sempre retorna True mas com baixa prioridade
        return True
    
    def get_priority(self) -> int:
        return 1  # Prioridade muito baixa - usado apenas como fallback
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação com liberdade total para LLM.
        Retorna dados brutos sem estruturação pré-definida.
        """
        raw_data_per_deck = {
            deck.name: {
                "display_name": deck.display_name,
                "result": deck.result,
                "success": deck.success
            }
            for deck in decks_data
        }
        
        return {
            "comparison_table": None,
            "chart_data": None,
            "visualization_type": "llm_free",
            "raw_data_per_deck": raw_data_per_deck,
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2,
            "llm_context": {
                "tool_name": tool_name,
                "query": query,
                "deck_count": len(decks_data)
            }
        }


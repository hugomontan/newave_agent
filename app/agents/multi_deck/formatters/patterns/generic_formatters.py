"""
Formatters genéricos para multi-deck (fallback).
"""

from typing import Dict, Any
from app.agents.multi_deck.formatters.base import ComparisonFormatter
from app.agents.multi_deck.nodes.helpers.comparison.llm_formatters import format_with_llm_free
from app.config import safe_print


class LLMFreeFormatter(ComparisonFormatter):
    """
    Formatter genérico que sempre pode formatar (fallback).
    Usa LLM para gerar resposta livre.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Sempre retorna True - é o fallback."""
        return True
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: str = None,
        deck_2_name: str = None
    ) -> Dict[str, Any]:
        """
        Formata comparação usando LLM livre.
        """
        safe_print(f"[LLM FREE FORMATTER] Formatando comparação para {tool_name}")
        
        try:
            # Usar LLM formatter para gerar resposta
            final_response = format_with_llm_free(
                result_dec,
                result_jan,
                tool_name,
                query,
                deck_1_name or "Deck 1",
                deck_2_name or "Deck 2"
            )
            
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "llm_free",
                "final_response": final_response
            }
        except Exception as e:
            safe_print(f"[LLM FREE FORMATTER] Erro ao formatar: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "llm_free",
                "final_response": f"## Erro ao formatar comparação\n\nErro: {str(e)}"
            }
    
    def get_priority(self) -> int:
        return 0  # Prioridade mais baixa - sempre último

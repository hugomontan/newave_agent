"""
Formatter genérico para single deck - formata qualquer tool usando formatação padrão.
"""

from typing import Dict, Any
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.single_deck.nodes.helpers.tool_formatting.base import format_tool_response


class GenericSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter genérico que usa formatação padrão para qualquer tool.
    Fallback quando não há formatter específico.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Sempre pode formatar (fallback)."""
        return True
    
    def get_priority(self) -> int:
        """Prioridade muito baixa - apenas fallback."""
        return -1
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta usando formatação padrão.
        """
        return format_tool_response(tool_result, tool_name)

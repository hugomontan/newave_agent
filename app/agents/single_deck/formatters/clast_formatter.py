"""
Formatter específico para ClastValoresTool no modo single deck.
"""

from typing import Dict, Any
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.shared.interpreter.tool_formatting.specific_formatters import format_clast_valores_response


class ClastSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter para ClastValoresTool no modo single deck.
    Reutiliza a lógica existente de formatação.
    """
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta de ClastValoresTool para single deck.
        """
        return format_clast_valores_response(tool_result, tool_name, query)

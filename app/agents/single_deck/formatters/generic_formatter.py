"""
Formatter genérico para single deck - usa LLM para formatar qualquer tool.
"""

from typing import Dict, Any
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.shared.interpreter.tool_formatting.llm_formatter import format_tool_response_with_llm


class GenericSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter genérico que usa LLM para formatar qualquer tool.
    Fallback quando não há formatter específico.
    """
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta usando LLM (compartilhado).
        """
        return format_tool_response_with_llm(tool_result, tool_name, query)

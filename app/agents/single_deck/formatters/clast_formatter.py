"""
Formatter específico para ClastValoresTool no modo single deck.
"""

from typing import Dict, Any
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.single_deck.nodes.helpers.tool_formatting.llm_formatter import format_tool_response_with_llm


class ClastSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter para ClastValoresTool no modo single deck.
    Usa LLM formatter para aplicar as instruções de formatação corretamente.
    """
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta de ClastValoresTool para single deck.
        Usa LLM formatter para seguir as instruções de formatação (focar na pergunta, não calcular médias, etc.).
        """
        # Extrair query original se vier de disambiguation
        if " - " in query:
            query = query.split(" - ", 1)[0].strip()
        
        return format_tool_response_with_llm(tool_result, tool_name, query)

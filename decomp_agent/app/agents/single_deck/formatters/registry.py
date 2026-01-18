"""
Registry de formatters para single deck.
Atribui formatter baseado na tool executada usando can_format() e get_priority().
"""

from typing import Dict, Any, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from decomp_agent.app.tools.base import DECOMPTool

# Formatters específicos do single deck
from decomp_agent.app.agents.single_deck.formatters.data_formatters import (
    UHSingleDeckFormatter,
    CTSingleDeckFormatter,
    DPSingleDeckFormatter,
    DisponibilidadeUsinaFormatter,
    InflexibilidadeUsinaFormatter,
)

# Formatter genérico (fallback)
from decomp_agent.app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter

# Lista de formatters ordenada por prioridade (maior primeiro)
SINGLE_DECK_FORMATTERS = [
    UHSingleDeckFormatter(),
    CTSingleDeckFormatter(),
    DPSingleDeckFormatter(),
    DisponibilidadeUsinaFormatter(),
    InflexibilidadeUsinaFormatter(),
]


def get_formatter_for_tool(
    tool: DECOMPTool,
    tool_result: Dict[str, Any]
) -> SingleDeckFormatter:
    """
    Retorna formatter apropriado para uma tool no modo single deck.
    
    Args:
        tool: Instância da tool executada
        tool_result: Resultado da execução
        
    Returns:
        Formatter apropriado
    """
    tool_name = tool.get_name()
    
    # Ordenar formatters por prioridade (maior primeiro)
    sorted_formatters = sorted(
        SINGLE_DECK_FORMATTERS,
        key=lambda f: f.get_priority(),
        reverse=True
    )
    
    for formatter in sorted_formatters:
        if formatter.can_format(tool_name, tool_result):
            return formatter
    
    # Fallback: formatter genérico
    return GenericSingleDeckFormatter()

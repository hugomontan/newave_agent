"""
Registry de formatters para single deck.
Atribui formatter baseado na tool executada usando can_format() e get_priority().
"""

from typing import Dict, Any, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print

# Formatters específicos do single deck
from decomp_agent.app.agents.single_deck.formatters.data_formatters import (
    UHSingleDeckFormatter,
    CTSingleDeckFormatter,
    DPSingleDeckFormatter,
    DisponibilidadeUsinaFormatter,
    InflexibilidadeUsinaFormatter,
    VolumeInicialFormatter,
)

# Formatter genérico (fallback)
from decomp_agent.app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter

# Lista de formatters ordenada por prioridade (maior primeiro)
# VolumeInicialFormatter tem prioridade 95, então vem antes de UHSingleDeckFormatter (90)
SINGLE_DECK_FORMATTERS = [
    VolumeInicialFormatter(),  # Prioridade 95 - específico para volume inicial
    UHSingleDeckFormatter(),  # Prioridade 90 - formatter genérico UH
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
        can_format_result = formatter.can_format(tool_name, tool_result)
        safe_print(f"[FORMATTER REGISTRY] {formatter.__class__.__name__}: can_format={can_format_result} (priority={formatter.get_priority()})")
        if can_format_result:
            safe_print(f"[FORMATTER REGISTRY] ✅ Selecionado: {formatter.__class__.__name__}")
            return formatter
    
    # Fallback: formatter genérico
    return GenericSingleDeckFormatter()

"""
Registry mínimo de formatters para single deck DESSEM.

Por enquanto sempre retorna o formatter genérico.
"""

from typing import Dict, Any

from .generic_formatter import GenericSingleDeckFormatter
from .base import SingleDeckFormatter


def get_formatter_for_tool(
    _tool: Any,
    _tool_result: Dict[str, Any],
) -> SingleDeckFormatter:
    """
    Retorna sempre o formatter genérico.

    A assinatura é compatível com o registry usado em NEWAVE,
    o que permite reaproveitar o `interpreter_node` compartilhado.
    """
    return GenericSingleDeckFormatter()


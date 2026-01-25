"""
Módulo de formatação para single deck DECOMP.
"""

from .base import SingleDeckFormatter
from .registry import get_formatter_for_tool, SINGLE_DECK_FORMATTERS

__all__ = [
    "SingleDeckFormatter",
    "get_formatter_for_tool",
    "SINGLE_DECK_FORMATTERS",
]

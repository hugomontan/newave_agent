"""
Formatters para Multi-Deck Agent.
"""

from .base import ComparisonFormatter
from .registry import get_formatter_for_tool

__all__ = [
    "ComparisonFormatter",
    "get_formatter_for_tool",
]

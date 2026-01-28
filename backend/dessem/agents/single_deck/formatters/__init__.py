"""
Formatters para Single Deck DESSEM.

Neste momento apenas um formatter genérico é definido, suficiente
para estruturar o fluxo base antes da criação de tools específicas.
"""

from .base import SingleDeckFormatter
from .generic_formatter import GenericSingleDeckFormatter

__all__ = ["SingleDeckFormatter", "GenericSingleDeckFormatter"]


"""
Formatters de dados para single deck.
Cada formatter é específico para uma tool.
"""

# Formatters específicos do single deck serão importados aqui
# Por enquanto, apenas o UH
from .uh_formatter import UHSingleDeckFormatter

__all__ = [
    "UHSingleDeckFormatter",
]

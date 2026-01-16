"""
Formatadores de dados para comparações multi-deck.
Geram estruturas de dados formatadas (tabelas, gráficos, etc) a partir de resultados de tools.
"""

from .uh_comparison_formatter import UHComparisonFormatter
from .disponibilidade_comparison_formatter import DisponibilidadeComparisonFormatter

__all__ = [
    "UHComparisonFormatter",
    "DisponibilidadeComparisonFormatter",
]

"""
Formatadores de dados para comparações multi-deck.
Geram estruturas de dados formatadas (tabelas, gráficos, etc) a partir de resultados de tools.
"""

from .uh_comparison_formatter import UHComparisonFormatter
from .disponibilidade_comparison_formatter import DisponibilidadeComparisonFormatter
from .inflexibilidade_comparison_formatter import InflexibilidadeComparisonFormatter
from .cvu_comparison_formatter import CVUComparisonFormatter
from .volume_inicial_comparison_formatter import VolumeInicialComparisonFormatter

__all__ = [
    "UHComparisonFormatter",
    "DisponibilidadeComparisonFormatter",
    "InflexibilidadeComparisonFormatter",
    "CVUComparisonFormatter",
    "VolumeInicialComparisonFormatter",
]

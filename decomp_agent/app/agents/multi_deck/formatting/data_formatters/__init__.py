"""
Formatadores de dados para comparações multi-deck.
Geram estruturas de dados formatadas (tabelas, gráficos, etc) a partir de resultados de tools.
"""

from .uh_comparison_formatter import UHComparisonFormatter
from .inflexibilidade_comparison_formatter import InflexibilidadeComparisonFormatter
from .cvu_comparison_formatter import CVUComparisonFormatter
from .volume_inicial_comparison_formatter import VolumeInicialComparisonFormatter
from .dp_comparison_formatter import DPComparisonFormatter
from .pq_comparison_formatter import PQComparisonFormatter
from .carga_ande_comparison_formatter import CargaAndeComparisonFormatter
from .limites_intercambio_comparison_formatter import LimitesIntercambioComparisonFormatter
from .restricoes_eletricas_comparison_formatter import RestricoesEletricasComparisonFormatter

__all__ = [
    "UHComparisonFormatter",
    "InflexibilidadeComparisonFormatter",
    "CVUComparisonFormatter",
    "VolumeInicialComparisonFormatter",
    "DPComparisonFormatter",
    "PQComparisonFormatter",
    "CargaAndeComparisonFormatter",
    "LimitesIntercambioComparisonFormatter",
    "RestricoesEletricasComparisonFormatter",
]

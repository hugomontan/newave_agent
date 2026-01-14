"""
Formatadores de dados para comparações multi-deck.
Geram estruturas de dados formatadas (tabelas, gráficos, etc) a partir de resultados de tools.
"""

from .temporal_formatters import (
    ClastComparisonFormatter,
    CargaComparisonFormatter,
    VazoesComparisonFormatter,
    UsinasNaoSimuladasFormatter,
    LimitesIntercambioComparisonFormatter,
)
from .diff_formatters import DiffComparisonFormatter
from .cadastro_formatters import CadastroComparisonFormatter
from .table_formatters import TableComparisonFormatter
from .gtmin_formatters import MudancasGeracoesTermicasFormatter
from .vazao_minima_formatters import MudancasVazaoMinimaFormatter
from .variacao_reservatorio_inicial_formatters import VariacaoReservatorioInicialFormatter
from .llm_free_formatters import LLMFreeFormatter

__all__ = [
    "ClastComparisonFormatter",
    "CargaComparisonFormatter",
    "VazoesComparisonFormatter",
    "UsinasNaoSimuladasFormatter",
    "LimitesIntercambioComparisonFormatter",
    "DiffComparisonFormatter",
    "CadastroComparisonFormatter",
    "TableComparisonFormatter",
    "MudancasGeracoesTermicasFormatter",
    "MudancasVazaoMinimaFormatter",
    "VariacaoReservatorioInicialFormatter",
    "LLMFreeFormatter",
]

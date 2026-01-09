"""
Formatadores especializados por tipo de tool.
"""
from app.comparison.formatters.temporal_formatters import (
    ClastComparisonFormatter,
    CargaComparisonFormatter,
    VazoesComparisonFormatter,
    UsinasNaoSimuladasFormatter,
    LimitesIntercambioComparisonFormatter,
)
from app.comparison.formatters.diff_formatters import (
    DiffComparisonFormatter,
)
from app.comparison.formatters.cadastro_formatters import (
    CadastroComparisonFormatter,
)
from app.comparison.formatters.table_formatters import (
    TableComparisonFormatter,
)
from app.comparison.formatters.llm_free_formatters import (
    LLMFreeFormatter,
)
from app.comparison.formatters.gtmin_formatters import (
    MudancasGeracoesTermicasFormatter,
)

__all__ = [
    'MudancasGeracoesTermicasFormatter',
    'ClastComparisonFormatter',
    'CargaComparisonFormatter',
    'VazoesComparisonFormatter',
    'UsinasNaoSimuladasFormatter',
    'LimitesIntercambioComparisonFormatter',
    'DiffComparisonFormatter',
    'CadastroComparisonFormatter',
    'TableComparisonFormatter',
    'LLMFreeFormatter',
]


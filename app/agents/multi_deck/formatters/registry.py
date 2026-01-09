"""
Registry de formatadores de comparação.
Mapeia tools para formatadores apropriados.
"""
from typing import Dict, Any
from app.agents.multi_deck.formatters.base import ComparisonFormatter
from app.agents.multi_deck.formatters.formatters.temporal_formatters import (
    ClastComparisonFormatter,
    CargaComparisonFormatter,
    VazoesComparisonFormatter,
    UsinasNaoSimuladasFormatter,
    LimitesIntercambioComparisonFormatter,
)
from app.agents.multi_deck.formatters.formatters.diff_formatters import (
    DiffComparisonFormatter,
)
from app.agents.multi_deck.formatters.formatters.cadastro_formatters import (
    CadastroComparisonFormatter,
)
from app.agents.multi_deck.formatters.formatters.table_formatters import (
    TableComparisonFormatter,
)
from app.agents.multi_deck.formatters.formatters.llm_free_formatters import (
    LLMFreeFormatter,
)
from app.agents.multi_deck.formatters.formatters.gtmin_formatters import (
    MudancasGeracoesTermicasFormatter,
)
from app.agents.multi_deck.formatters.formatters.volume_inicial_formatters import (
    VariacaoVolumesIniciaisFormatter,
)


# Lista de formatadores (em ordem de prioridade - mais específicos primeiro)
FORMATTERS = [
    VariacaoVolumesIniciaisFormatter(),  # Alta prioridade - muito específico para volumes iniciais
    MudancasGeracoesTermicasFormatter(),  # Alta prioridade - muito específico para GTMIN
    ClastComparisonFormatter(),
    CargaComparisonFormatter(),
    VazoesComparisonFormatter(),
    UsinasNaoSimuladasFormatter(),
    LimitesIntercambioComparisonFormatter(),
    DiffComparisonFormatter(),
    CadastroComparisonFormatter(),
    TableComparisonFormatter(),
    LLMFreeFormatter(),  # Fallback - sempre deve ser o último
]


def get_formatter_for_tool(
    tool_name: str, 
    result_structure: Dict[str, Any]
) -> ComparisonFormatter:
    """
    Retorna o formatador mais apropriado para uma tool específica.
    
    Args:
        tool_name: Nome da tool (ex: "ClastValoresTool")
        result_structure: Estrutura do resultado da tool (para verificar campos disponíveis)
        
    Returns:
        Formatador apropriado (ou LLMFreeFormatter como fallback)
    """
    candidates = [
        f for f in FORMATTERS 
        if f.can_format(tool_name, result_structure)
    ]
    
    if candidates:
        # Retornar o formatador com maior prioridade
        return max(candidates, key=lambda f: f.get_priority())
    
    # Fallback para LLMFreeFormatter se nenhum formatador pode processar
    return LLMFreeFormatter()


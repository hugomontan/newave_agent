"""
Módulo de Tools pré-programadas para consultas frequentes ao NEWAVE.
"""
from app.tools.carga_mensal_tool import CargaMensalTool
from app.tools.clast_valores_tool import ClastValoresTool
from app.tools.expt_operacao_tool import ExptOperacaoTool
from app.tools.modif_operacao_tool import ModifOperacaoTool
from app.tools.limites_intercambio_tool import LimitesIntercambioTool
from app.tools.agrint_tool import AgrintTool
from app.tools.vazoes_tool import VazoesTool
from app.tools.cadic_tool import CadicTool
from app.tools.hidr_cadastro_tool import HidrCadastroTool
from app.tools.confhd_tool import ConfhdTool
from app.tools.dsvagua_tool import DsvaguaTool
from app.tools.usinas_nao_simuladas_tool import UsinasNaoSimuladasTool
from app.tools.restricao_eletrica_tool import RestricaoEletricaTool
from app.tools.term_cadastro_tool import TermCadastroTool
from app.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
from app.tools.mudancas_geracoes_termicas_tool import MudancasGeracoesTermicasTool
from app.tools.variacao_volumes_iniciais_tool import VariacaoVolumesIniciaisTool

# Registry de tools para modo single (sem comparacao multi-deck)
TOOLS_REGISTRY_SINGLE = [
    CargaMensalTool,
    ClastValoresTool,
    ExptOperacaoTool,
    ModifOperacaoTool,
    LimitesIntercambioTool,
    AgrintTool,
    VazoesTool,
    CadicTool,
    HidrCadastroTool,
    ConfhdTool,
    DsvaguaTool,
    UsinasNaoSimuladasTool,
    RestricaoEletricaTool,
    TermCadastroTool,
]

# Registry de tools para modo comparison (inclui MultiDeckComparisonTool)
TOOLS_REGISTRY_COMPARISON = [
    VariacaoVolumesIniciaisTool,  # Tool específica para variação de volumes iniciais (prioridade sobre outras)
    MudancasGeracoesTermicasTool,  # Tool específica para mudanças de GTMIN (prioridade sobre MultiDeckComparisonTool)
    MultiDeckComparisonTool,  # Primeira para interceptar todas as queries em modo comparison
] + TOOLS_REGISTRY_SINGLE

# Alias para compatibilidade
TOOLS_REGISTRY = TOOLS_REGISTRY_SINGLE


def get_available_tools(deck_path: str, analysis_mode: str = "single"):
    """
    Retorna instancias de todas as tools disponiveis.
    
    Args:
        deck_path: Caminho do diretorio do deck NEWAVE
        analysis_mode: Modo de analise ("single" ou "comparison")
        
    Returns:
        Lista de instancias de tools
    """
    if analysis_mode == "comparison":
        registry = TOOLS_REGISTRY_COMPARISON
    else:
        registry = TOOLS_REGISTRY_SINGLE
    
    return [ToolClass(deck_path) for ToolClass in registry]


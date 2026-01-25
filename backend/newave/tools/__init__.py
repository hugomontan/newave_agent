"""
Módulo de Tools pré-programadas para consultas frequentes ao NEWAVE.
"""
from backend.newave.tools.carga_mensal_tool import CargaMensalTool
from backend.newave.tools.clast_valores_tool import ClastValoresTool
from backend.newave.tools.expt_operacao_tool import ExptOperacaoTool
from backend.newave.tools.modif_operacao_tool import ModifOperacaoTool
from backend.newave.tools.limites_intercambio_tool import LimitesIntercambioTool
from backend.newave.tools.agrint_tool import AgrintTool
from backend.newave.tools.vazoes_tool import VazoesTool
from backend.newave.tools.cadic_tool import CadicTool
from backend.newave.tools.hidr_cadastro_tool import HidrCadastroTool
from backend.newave.tools.confhd_tool import ConfhdTool
from backend.newave.tools.dsvagua_tool import DsvaguaTool
from backend.newave.tools.usinas_nao_simuladas_tool import UsinasNaoSimuladasTool
from backend.newave.tools.restricao_eletrica_tool import RestricaoEletricaTool
from backend.newave.tools.term_cadastro_tool import TermCadastroTool
from backend.newave.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
from backend.newave.tools.mudancas_geracoes_termicas_tool import MudancasGeracoesTermicasTool
from backend.newave.tools.mudancas_vazao_minima_tool import MudancasVazaoMinimaTool
from backend.newave.tools.variacao_reservatorio_inicial_tool import VariacaoReservatorioInicialTool

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
    VariacaoReservatorioInicialTool,  # Tool específica para variação de reservatório inicial por usina (prioridade sobre outras)
    MudancasGeracoesTermicasTool,  # Tool específica para mudanças de GTMIN (prioridade sobre MultiDeckComparisonTool)
    MudancasVazaoMinimaTool,  # Tool específica para mudanças de VAZMIN/VAZMINT (prioridade sobre MultiDeckComparisonTool)
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


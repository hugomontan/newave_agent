"""
Módulo de Tools pré-programadas para consultas frequentes ao NEWAVE.
"""
from newave_agent.app.tools.carga_mensal_tool import CargaMensalTool
from newave_agent.app.tools.clast_valores_tool import ClastValoresTool
from newave_agent.app.tools.expt_operacao_tool import ExptOperacaoTool
from newave_agent.app.tools.modif_operacao_tool import ModifOperacaoTool
from newave_agent.app.tools.limites_intercambio_tool import LimitesIntercambioTool
from newave_agent.app.tools.agrint_tool import AgrintTool
from newave_agent.app.tools.vazoes_tool import VazoesTool
from newave_agent.app.tools.cadic_tool import CadicTool
from newave_agent.app.tools.hidr_cadastro_tool import HidrCadastroTool
from newave_agent.app.tools.confhd_tool import ConfhdTool
from newave_agent.app.tools.dsvagua_tool import DsvaguaTool
from newave_agent.app.tools.usinas_nao_simuladas_tool import UsinasNaoSimuladasTool
from newave_agent.app.tools.restricao_eletrica_tool import RestricaoEletricaTool
from newave_agent.app.tools.term_cadastro_tool import TermCadastroTool
from newave_agent.app.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
from newave_agent.app.tools.mudancas_geracoes_termicas_tool import MudancasGeracoesTermicasTool
from newave_agent.app.tools.mudancas_vazao_minima_tool import MudancasVazaoMinimaTool
from newave_agent.app.tools.variacao_reservatorio_inicial_tool import VariacaoReservatorioInicialTool

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


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

# Registry de todas as tools disponíveis
TOOLS_REGISTRY = [
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
    # Adicionar outras tools aqui conforme forem criadas
]

def get_available_tools(deck_path: str):
    """
    Retorna instâncias de todas as tools disponíveis.
    
    Args:
        deck_path: Caminho do diretório do deck NEWAVE
        
    Returns:
        Lista de instâncias de tools
    """
    return [ToolClass(deck_path) for ToolClass in TOOLS_REGISTRY]


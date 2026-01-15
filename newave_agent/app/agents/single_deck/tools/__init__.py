"""
Registry de tools para modo Single Deck.
"""

from typing import List
from newave_agent.app.tools.base import NEWAVETool
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


# Registry de tools para modo single (lista completa, independente)
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


def get_available_tools(deck_path: str) -> List[NEWAVETool]:
    """
    Retorna instâncias de todas as tools disponíveis para modo single deck.
    
    Args:
        deck_path: Caminho do diretório do deck NEWAVE
        
    Returns:
        Lista de instâncias de tools
    """
    return [ToolClass(deck_path) for ToolClass in TOOLS_REGISTRY_SINGLE]

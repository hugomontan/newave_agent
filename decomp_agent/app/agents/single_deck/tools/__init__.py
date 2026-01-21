"""
Registry de tools para modo Single Deck DECOMP.
"""

from typing import List
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.tools.uh_usinas_hidreletricas_tool import UHUsinasHidrelétricasTool
from decomp_agent.app.tools.ct_usinas_termelétricas_tool import CTUsinasTermelétricasTool
from decomp_agent.app.tools.dp_carga_subsistemas_tool import DPCargaSubsistemasTool
from decomp_agent.app.tools.inflexibilidade_usina_tool import InflexibilidadeUsinaTool
from decomp_agent.app.tools.disponibilidade_usina_tool import DisponibilidadeUsinaTool
from decomp_agent.app.tools.pq_pequenas_usinas_tool import PQPequenasUsinasTool
from decomp_agent.app.tools.carga_ande_tool import CargaAndeTool
from decomp_agent.app.tools.limites_intercambio_tool import LimitesIntercambioDECOMPTool
from decomp_agent.app.tools.restricoes_eletricas_tool import RestricoesEletricasDECOMPTool
from decomp_agent.app.tools.restricoes_vazao_hq_tool import RestricoesVazaoHQTool

# Registry de tools para modo single deck DECOMP
TOOLS_REGISTRY_SINGLE = [
    UHUsinasHidrelétricasTool,
    CTUsinasTermelétricasTool,
    DPCargaSubsistemasTool,
    InflexibilidadeUsinaTool,
    DisponibilidadeUsinaTool,
    PQPequenasUsinasTool,
    CargaAndeTool,
    LimitesIntercambioDECOMPTool,
    RestricoesEletricasDECOMPTool,
    RestricoesVazaoHQTool,
]


def get_available_tools(deck_path: str) -> List[DECOMPTool]:
    """
    Retorna instâncias de todas as tools disponíveis para modo single deck DECOMP.
    
    Args:
        deck_path: Caminho do diretório do deck DECOMP
        
    Returns:
        Lista de instâncias de tools
    """
    return [ToolClass(deck_path) for ToolClass in TOOLS_REGISTRY_SINGLE]

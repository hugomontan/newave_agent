"""
Registry de tools para modo Single Deck DECOMP.
"""

from typing import List
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.tools.uh_usinas_hidreletricas_tool import UHUsinasHidrelétricasTool
from decomp_agent.app.tools.ct_usinas_termelétricas_tool import CTUsinasTermelétricasTool
from decomp_agent.app.tools.dp_carga_subsistemas_tool import DPCargaSubsistemasTool
from decomp_agent.app.tools.disponibilidade_usina_tool import DisponibilidadeUsinaTool

# Registry de tools para modo single deck DECOMP
TOOLS_REGISTRY_SINGLE = [
    UHUsinasHidrelétricasTool,
    CTUsinasTermelétricasTool,
    DPCargaSubsistemasTool,
    DisponibilidadeUsinaTool,
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

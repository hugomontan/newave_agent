"""
Tools do DECOMP Agent.
"""
from typing import List

from .base import DECOMPTool
from .uh_usinas_hidreletricas_tool import UHUsinasHidrelétricasTool
from .ct_usinas_termelétricas_tool import CTUsinasTermelétricasTool
from .dp_carga_subsistemas_tool import DPCargaSubsistemasTool
from .inflexibilidade_usina_tool import InflexibilidadeUsinaTool
from .disponibilidade_usina_tool import DisponibilidadeUsinaTool
from .pq_pequenas_usinas_tool import PQPequenasUsinasTool
from .carga_ande_tool import CargaAndeTool
from .limites_intercambio_tool import LimitesIntercambioDECOMPTool
from .restricoes_eletricas_tool import RestricoesEletricasDECOMPTool
from .restricoes_vazao_hq_tool import RestricoesVazaoHQTool
from .restricoes_vazao_hq_conjunta_tool import RestricoesVazaoHQConjuntaTool
from .gl_geracoes_gnl_tool import GLGeracoesGNLTool


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
    RestricoesVazaoHQConjuntaTool,
    GLGeracoesGNLTool,
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


__all__ = [
    "DECOMPTool",
    "UHUsinasHidrelétricasTool",
    "CTUsinasTermelétricasTool",
    "DPCargaSubsistemasTool",
    "InflexibilidadeUsinaTool",
    "DisponibilidadeUsinaTool",
    "PQPequenasUsinasTool",
    "CargaAndeTool",
    "LimitesIntercambioDECOMPTool",
    "RestricoesEletricasDECOMPTool",
    "RestricoesVazaoHQTool",
    "RestricoesVazaoHQConjuntaTool",
    "GLGeracoesGNLTool",
    "TOOLS_REGISTRY_SINGLE",
    "get_available_tools",
]

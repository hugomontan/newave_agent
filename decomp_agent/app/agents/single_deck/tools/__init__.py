"""
Registry de tools para modo Single Deck DECOMP.
"""

from typing import List
from decomp_agent.app.tools.base import DECOMPTool

# Registry de tools para modo single (vazio por enquanto - tools serão adicionadas depois)
TOOLS_REGISTRY_SINGLE = [
    # Tools DECOMP serão adicionadas aqui
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

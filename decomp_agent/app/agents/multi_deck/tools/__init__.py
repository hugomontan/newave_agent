"""Registry de tools para modo Multi-Deck DECOMP."""
from typing import List, Dict
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.agents.multi_deck.tools.disponibilidade_multi_deck_tool import DisponibilidadeMultiDeckTool

TOOLS_REGISTRY_MULTI = [
    DisponibilidadeMultiDeckTool,
]

def get_available_tools(selected_decks: List[str], deck_paths: Dict[str, str]) -> List[DECOMPTool]:
    """Retorna tools disponíveis para comparação multi-deck DECOMP."""
    return [ToolClass(deck_paths) for ToolClass in TOOLS_REGISTRY_MULTI]

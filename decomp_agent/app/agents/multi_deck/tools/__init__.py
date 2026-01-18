"""Registry de tools para modo Multi-Deck DECOMP."""
from typing import List, Dict
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.agents.multi_deck.tools.disponibilidade_multi_deck_tool import DisponibilidadeMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.inflexibilidade_multi_deck_tool import InflexibilidadeMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.cvu_multi_deck_tool import CVUMultiDeckTool

TOOLS_REGISTRY_MULTI = [
    DisponibilidadeMultiDeckTool,
    InflexibilidadeMultiDeckTool,
    CVUMultiDeckTool,
]

def get_available_tools(selected_decks: List[str], deck_paths: Dict[str, str]) -> List[DECOMPTool]:
    """Retorna tools disponíveis para comparação multi-deck DECOMP."""
    return [ToolClass(deck_paths) for ToolClass in TOOLS_REGISTRY_MULTI]

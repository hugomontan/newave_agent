"""Registry de tools para modo Multi-Deck DECOMP."""
from typing import List, Dict
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.agents.multi_deck.tools.inflexibilidade_multi_deck_tool import InflexibilidadeMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.cvu_multi_deck_tool import CVUMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.volume_inicial_multi_deck_tool import VolumeInicialMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.dp_multi_deck_tool import DPMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.pq_multi_deck_tool import PQMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.carga_ande_multi_deck_tool import CargaAndeMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.limites_intercambio_multi_deck_tool import LimitesIntercambioMultiDeckTool
from decomp_agent.app.agents.multi_deck.tools.restricoes_eletricas_multi_deck_tool import RestricoesEletricasMultiDeckTool

TOOLS_REGISTRY_MULTI = [
    InflexibilidadeMultiDeckTool,
    CVUMultiDeckTool,
    VolumeInicialMultiDeckTool,
    DPMultiDeckTool,
    PQMultiDeckTool,
    CargaAndeMultiDeckTool,
    LimitesIntercambioMultiDeckTool,
    RestricoesEletricasMultiDeckTool,
]

def get_available_tools(selected_decks: List[str], deck_paths: Dict[str, str]) -> List[DECOMPTool]:
    """Retorna tools disponíveis para comparação multi-deck DECOMP."""
    return [ToolClass(deck_paths) for ToolClass in TOOLS_REGISTRY_MULTI]

"""Registry de tools para modo Multi-Deck DECOMP."""
from typing import List, Dict
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.agents.multi_deck.tools.inflexibilidade_multi_deck_tool import InflexibilidadeMultiDeckTool
from backend.decomp.agents.multi_deck.tools.cvu_multi_deck_tool import CVUMultiDeckTool
from backend.decomp.agents.multi_deck.tools.volume_inicial_multi_deck_tool import VolumeInicialMultiDeckTool
from backend.decomp.agents.multi_deck.tools.dp_multi_deck_tool import DPMultiDeckTool
from backend.decomp.agents.multi_deck.tools.pq_multi_deck_tool import PQMultiDeckTool
from backend.decomp.agents.multi_deck.tools.carga_ande_multi_deck_tool import CargaAndeMultiDeckTool
from backend.decomp.agents.multi_deck.tools.limites_intercambio_multi_deck_tool import LimitesIntercambioMultiDeckTool
from backend.decomp.agents.multi_deck.tools.restricoes_eletricas_multi_deck_tool import RestricoesEletricasMultiDeckTool
from backend.decomp.agents.multi_deck.tools.restricoes_vazao_hq_multi_deck_tool import RestricoesVazaoHQMultiDeckTool
from backend.decomp.agents.multi_deck.tools.gl_multi_deck_tool import GLMultiDeckTool

TOOLS_REGISTRY_MULTI = [
    InflexibilidadeMultiDeckTool,
    CVUMultiDeckTool,
    VolumeInicialMultiDeckTool,
    DPMultiDeckTool,
    PQMultiDeckTool,
    CargaAndeMultiDeckTool,
    LimitesIntercambioMultiDeckTool,
    RestricoesEletricasMultiDeckTool,
    RestricoesVazaoHQMultiDeckTool,
    GLMultiDeckTool,
]

def get_available_tools(selected_decks: List[str], deck_paths: Dict[str, str]) -> List[DECOMPTool]:
    """Retorna tools disponíveis para comparação multi-deck DECOMP."""
    return [ToolClass(deck_paths) for ToolClass in TOOLS_REGISTRY_MULTI]

"""
Node de roteamento de tools de comparação para o DESSEM.

Por enquanto não há tools de comparação implementadas, então o node
apenas registra a query e indica que nenhuma tool foi executada.
"""

from backend.dessem.agents.multi_deck.state import MultiDeckState
from backend.dessem.config import safe_print


def comparison_tool_router_node(state: MultiDeckState) -> dict:
    """
    Node que decidiria qual tool de comparação DESSEM executar.

    Como ainda não há tools, sempre retorna `tool_route=False`.
    """
    query = state.get("query", "")
    selected_decks = state.get("selected_decks", [])

    safe_print("[DESSEM MULTI-DECK ROUTER] ===== INÍCIO =====")
    safe_print(f"[DESSEM MULTI-DECK ROUTER] Query: {query[:100]}")
    safe_print(f"[DESSEM MULTI-DECK ROUTER] Decks selecionados: {selected_decks}")
    safe_print("[DESSEM MULTI-DECK ROUTER] Nenhuma tool de comparação DESSEM implementada ainda.")
    safe_print("[DESSEM MULTI-DECK ROUTER] ===== FIM (tool_route=False) =====")

    return {
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        "disambiguation": None,
    }


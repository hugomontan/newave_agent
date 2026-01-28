"""
Node simples de roteamento de tools para o DESSEM.

Neste estágio inicial não existem tools implementadas para o DESSEM,
então o node apenas registra a query e informa que nenhuma tool foi executada.
"""

from backend.dessem.state import SingleDeckState
from backend.dessem.config import safe_print


def tool_router_node(state: SingleDeckState) -> dict:
    """
    Node que decidiria qual tool DESSEM executar.

    Como ainda não há tools implementadas, ele sempre retorna
    `tool_route=False`, permitindo que o fluxo siga direto para o
    interpreter, que devolve uma mensagem padrão.
    """
    query = state.get("query", "")
    deck_path = state.get("deck_path", "")

    safe_print("[DESSEM TOOL ROUTER] ===== INÍCIO =====")
    safe_print(f"[DESSEM TOOL ROUTER] Query: {query[:100]}")
    safe_print(f"[DESSEM TOOL ROUTER] Deck path: {deck_path}")
    safe_print("[DESSEM TOOL ROUTER] Nenhuma tool DESSEM implementada ainda - seguindo sem execução de tool.")
    safe_print("[DESSEM TOOL ROUTER] ===== FIM (tool_route=False) =====")

    return {
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        "disambiguation": None,
    }


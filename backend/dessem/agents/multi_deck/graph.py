"""
Graph para Multi-Deck Agent DESSEM.

Esqueleto que segue o padrão do NEWAVE, mas sem tools
de comparação implementadas ainda.
"""

from typing import Generator, Optional, List, Dict

import json
from langgraph.graph import StateGraph, END

from backend.dessem.agents.multi_deck.state import MultiDeckState
from backend.core.utils.observability import get_langfuse_handler, flush_langfuse
from backend.dessem.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, safe_print


NODE_DESCRIPTIONS = {
    "comparison_tool_router": {
        "name": "Comparison Tool Router",
        "icon": "[TOOL]",
        "description": "Verificando se ha tool de comparacao DESSEM disponivel...",
    },
    "comparison_interpreter": {
        "name": "Comparison Interpreter",
        "icon": "[AI]",
        "description": "Formatando comparacao DESSEM...",
    },
}


def should_continue_after_tool_router(state: MultiDeckState) -> str:
    """Decide o próximo passo após o roteador de comparação."""
    if state.get("disambiguation"):
        return END
    return "comparison_interpreter"


def create_multi_deck_agent() -> StateGraph:
    """Cria o grafo do Multi-Deck Agent DESSEM."""
    from backend.dessem.agents.multi_deck.nodes import (
        comparison_tool_router_node,
        comparison_interpreter_node,
    )

    workflow = StateGraph(MultiDeckState)

    workflow.add_node("comparison_tool_router", comparison_tool_router_node)
    workflow.add_node("comparison_interpreter", comparison_interpreter_node)

    workflow.set_entry_point("comparison_tool_router")
    workflow.add_conditional_edges(
        "comparison_tool_router",
        should_continue_after_tool_router,
        {
            END: END,
            "comparison_interpreter": "comparison_interpreter",
        },
    )
    workflow.add_edge("comparison_interpreter", END)

    return workflow.compile()


_agent = None


def get_multi_deck_agent():
    """Retorna instância singleton do Multi-Deck Agent DESSEM."""
    global _agent
    if _agent is None:
        _agent = create_multi_deck_agent()
    return _agent


def reset_multi_deck_agent():
    """Recria o agent multi-deck DESSEM."""
    global _agent
    _agent = None


def get_initial_state(
    query: str,
    deck_path: str,
    selected_decks: Optional[List[str]] = None,
) -> Dict:
    """
    Estado inicial para uma query multi-deck DESSEM.

    Ainda não há carregamento real de decks DESSEM aqui; o foco é
    estrutural, então apenas preservamos os nomes informados.
    """
    return {
        "query": query,
        "deck_path": deck_path,
        "selected_decks": selected_decks or [],
        "deck_paths": {},
        "deck_display_names": {},
        "final_response": "",
        "error": None,
        "messages": [],
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        "disambiguation": None,
        "comparison_data": None,
        "requires_user_choice": None,
        "alternative_type": None,
    }


def run_query(
    query: str,
    deck_path: str,
    session_id: Optional[str] = None,
    selected_decks: Optional[List[str]] = None,
) -> Dict:
    """Executa uma query no Multi-Deck Agent DESSEM (sem comparação real ainda)."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)

    safe_print("[DESSEM MULTI-DECK] ===== INÍCIO: run_query =====")
    safe_print(f"[DESSEM MULTI-DECK] Query: {query[:100]}")
    safe_print(f"[DESSEM MULTI-DECK] Deck path: {deck_path}")
    safe_print(f"[DESSEM MULTI-DECK] Selected decks: {selected_decks}")

    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="dessem-multi-deck-query",
        metadata={"query": query[:100], "selected_decks": selected_decks},
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )

    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

    result = agent.invoke(initial_state, config=config)

    if langfuse_handler:
        try:
            if hasattr(langfuse_handler, "flush"):
                langfuse_handler.flush()
            flush_langfuse(
                public_key=LANGFUSE_PUBLIC_KEY,
                secret_key=LANGFUSE_SECRET_KEY,
                host=LANGFUSE_HOST,
            )
        except Exception:  # pragma: no cover
            pass

    safe_print("[DESSEM MULTI-DECK] ===== FIM: run_query =====")
    return result


def run_query_stream(
    query: str,
    deck_path: str,
    session_id: Optional[str] = None,
    selected_decks: Optional[List[str]] = None,
) -> Generator[str, None, None]:
    """Executa uma query no Multi-Deck Agent DESSEM com streaming básico."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)

    safe_print("[DESSEM MULTI-DECK] ===== INÍCIO: run_query_stream =====")

    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="dessem-multi-deck-query-stream",
        metadata={"query": query[:100], "streaming": True, "selected_decks": selected_decks},
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )

    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

    decks_info = [{"name": name} for name in initial_state.get("selected_decks", [])]
    yield f"data: {json.dumps({'type': 'start', 'message': 'Iniciando processamento...', 'selected_decks': decks_info})}\n\n"

    try:
        for event in agent.stream(initial_state, stream_mode="updates", config=config):
            for node_name, node_output in event.items():
                if node_output is None:
                    node_output = {}

                node_info = NODE_DESCRIPTIONS.get(
                    node_name,
                    {
                        "name": node_name,
                        "icon": "[🔄]",
                        "description": f"Executando {node_name}...",
                    },
                )

                yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info})}\n\n"

                if node_name == "comparison_interpreter":
                    response = node_output.get("final_response") if node_output else ""
                    yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                    chunk_size = 50
                    for i in range(0, len(response), chunk_size):
                        yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                    yield f"data: {json.dumps({'type': 'response_complete', 'response': response})}\n\n"

                yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"

        yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!'})}\n\n"

        if langfuse_handler:
            try:
                if hasattr(langfuse_handler, "flush"):
                    langfuse_handler.flush()
                flush_langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST,
                )
            except Exception:  # pragma: no cover
                pass

    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"


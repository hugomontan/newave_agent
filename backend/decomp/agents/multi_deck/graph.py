"""
Graph para Multi-Deck Agent DECOMP - especializado para comparações entre decks.
Suporta N decks para comparação dinâmica.
"""

# Standard library imports
import json
import math
import os
from typing import Generator, Any, Optional, List, Dict

# Third-party imports
from langgraph.graph import StateGraph, END

# Local imports
from backend.decomp.agents.multi_deck.state import MultiDeckState
from backend.core.utils.observability import get_langfuse_handler
from backend.decomp.config import safe_print
from backend.decomp.utils.deck_loader import (
    load_multiple_decks,
    get_deck_display_names_dict,
    list_available_decks,
)
from backend.core.utils.debug import write_debug_log
from backend.core.utils.json_utils import clean_nan_for_json



# Descrições dos nodes para streaming
NODE_DESCRIPTIONS = {
    "comparison_tool_router": {
        "name": "Comparison Tool Router",
        "icon": "[TOOL]",
        "description": "Verificando se ha tool de comparacao disponivel..."
    },
    "comparison_interpreter": {
        "name": "Comparison Interpreter",
        "icon": "[AI]",
        "description": "Formatando comparacao..."
    }
}


def should_continue_after_tool_router(state: MultiDeckState) -> str:
    """Decide o próximo passo após Comparison Tool Router."""
    tool_route = state.get("tool_route", False)
    disambiguation = state.get("disambiguation")
    
    if disambiguation:
        return END
    else:
        # Sempre vai para comparison_interpreter (com ou sem tool)
        return "comparison_interpreter"


def create_multi_deck_agent() -> StateGraph:
    """
    Cria o grafo do Multi-Deck Agent DECOMP especializado para comparações.
    
    Fluxo:
    1. Comparison Tool Router: Verifica se há tool de comparação disponível
       - Se tool executou: vai direto para Comparison Interpreter para formatar resultado
       - Se tool não executou: vai para Comparison Interpreter que retorna mensagem informando
    2. Comparison Interpreter: Formata resultado da tool ou retorna mensagem quando não há tool
    """
    # Importar nodes específicos do multi-deck
    from backend.decomp.agents.multi_deck.nodes import (
        comparison_tool_router_node,
        comparison_interpreter_node,
    )
    
    workflow = StateGraph(MultiDeckState)
    
    # Nodes disponíveis
    workflow.add_node("comparison_tool_router", comparison_tool_router_node)
    workflow.add_node("comparison_interpreter", comparison_interpreter_node)
    
    # Entry point: sempre começa com Comparison Tool Router
    workflow.set_entry_point("comparison_tool_router")
    
    # Fluxo: comparison_tool_router → comparison_interpreter (sempre, exceto disambiguation que termina)
    workflow.add_conditional_edges(
        "comparison_tool_router",
        should_continue_after_tool_router,
        {
            END: END,
            "comparison_interpreter": "comparison_interpreter"
        }
    )
    
    workflow.add_edge("comparison_interpreter", END)
    
    return workflow.compile()


_agent = None


def get_multi_deck_agent():
    """Retorna a instância do Multi-Deck Agent (singleton)."""
    global _agent
    if _agent is None:
        _agent = create_multi_deck_agent()
    return _agent


def reset_multi_deck_agent():
    """Força recriação do agent."""
    global _agent
    _agent = None


def get_initial_state(
    query: str, 
    deck_path: str, 
    selected_decks: Optional[List[str]] = None
) -> dict:
    """
    Retorna o estado inicial para uma query multi-deck DECOMP.
    
    Args:
        query: A pergunta do usuário
        deck_path: Caminho do deck principal (para compatibilidade)
        selected_decks: Lista de nomes dos decks selecionados
        
    Returns:
        Estado inicial do agent
    """
    # Se não foram especificados decks, usar os dois mais recentes disponíveis
    if not selected_decks:
        available = list_available_decks()
        if len(available) >= 2:
            selected_decks = [d["name"] for d in available[-2:]]
        elif len(available) == 1:
            selected_decks = [available[0]["name"]]
        else:
            selected_decks = []
    
    # Carregar os decks e obter caminhos
    deck_paths: Dict[str, str] = {}
    deck_display_names: Dict[str, str] = {}
    
    if selected_decks:
        try:
            paths = load_multiple_decks(selected_decks)
            deck_paths = {name: str(path) for name, path in paths.items()}
            deck_display_names = get_deck_display_names_dict(selected_decks)
            
            # Usar o primeiro deck como deck_path para compatibilidade
            if not deck_path and selected_decks:
                deck_path = deck_paths.get(selected_decks[0], "")
        except Exception as e:
            safe_print(f"[MULTI-DECK DECOMP] Erro ao carregar decks: {e}")
    
    return {
        "query": query,
        "deck_path": deck_path,
        "selected_decks": selected_decks,
        "deck_paths": deck_paths,
        "deck_display_names": deck_display_names,
        "final_response": "",
        "error": None,
        "messages": [],
        # Campos para Tools
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        # Campos para Disambiguation
        "disambiguation": None,
        # Campos para Correção de Usina
        "plant_correction_followup": None,
        # Campos para Comparação
        "comparison_data": None,
        # Campos para escolha do usuário (requires_user_choice)
        "requires_user_choice": None,
        "alternative_type": None
    }


def run_query(
    query: str, 
    deck_path: str, 
    session_id: Optional[str] = None, 
    selected_decks: Optional[List[str]] = None
) -> dict:
    """Executa uma query no Multi-Deck Agent DECOMP."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="decomp-multi-deck-query",
        metadata={"query": query[:100], "selected_decks": selected_decks}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    result = agent.invoke(initial_state, config=config)
    
    if langfuse_handler:
        try:
            if hasattr(langfuse_handler, 'flush'):
                langfuse_handler.flush()
            from backend.core.utils.observability import flush_langfuse
            flush_langfuse()
        except Exception:
            pass
    
    return result


def run_query_stream(
    query: str, 
    deck_path: str, 
    session_id: Optional[str] = None, 
    selected_decks: Optional[List[str]] = None
) -> Generator[str, None, None]:
    """Executa uma query no Multi-Deck Agent DECOMP com streaming de eventos."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="decomp-multi-deck-query-stream",
        metadata={"query": query[:100], "streaming": True, "selected_decks": selected_decks}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    decks_info = [
        {"name": name, "display_name": initial_state["deck_display_names"].get(name, name)}
        for name in initial_state.get("selected_decks", [])
    ]
    yield f"data: {json.dumps({'type': 'start', 'message': 'Iniciando processamento...', 'selected_decks': decks_info})}\n\n"
    
    current_retry = 0
    has_disambiguation = False
    
    try:
        for event in agent.stream(initial_state, stream_mode="updates", config=config):
            for node_name, node_output in event.items():
                if node_output is None:
                    node_output = {}
                
                node_info = NODE_DESCRIPTIONS.get(node_name, {
                    "name": node_name,
                    "icon": "[🔄]",
                    "description": f"Executando {node_name}..."
                })
                
                if not (node_name == "comparison_tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info, 'retry': current_retry})}\n\n"
                
                # Detalhes específicos de cada node
                if node_name == "comparison_interpreter":
                    response = node_output.get("final_response") if node_output else None
                    comparison_data = node_output.get("comparison_data") if node_output else None
                    plant_correction_followup = node_output.get("plant_correction_followup")
                    
                    if response and response.strip():
                        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        
                        cleaned_comparison_data = clean_nan_for_json(comparison_data) if comparison_data else None
                        response_complete_data = {
                            "type": "response_complete",
                            "response": response,
                            "comparison_data": cleaned_comparison_data,
                        }
                        if plant_correction_followup:
                            response_complete_data["plant_correction_followup"] = plant_correction_followup
                        
                        yield f"data: {json.dumps(response_complete_data, allow_nan=False)}\n\n"
                
                if not (node_name == "comparison_tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"
        
        if not has_disambiguation:
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': ''})}\n\n"
        
        if langfuse_handler:
            try:
                if hasattr(langfuse_handler, 'flush'):
                    langfuse_handler.flush()
                from backend.core.utils.observability import flush_langfuse
                flush_langfuse()
            except Exception:
                pass
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

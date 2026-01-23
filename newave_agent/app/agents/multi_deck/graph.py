"""
Graph para Multi-Deck Agent - especializado para comparações entre decks.
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
from newave_agent.app.agents.multi_deck.state import MultiDeckState
from newave_agent.app.utils.observability import get_langfuse_handler
from newave_agent.app.config import safe_print
from newave_agent.app.utils.deck_loader import (
    load_multiple_decks,
    get_deck_display_names_dict,
    list_available_decks,
)
from shared.utils.debug import write_debug_log
from shared.utils.json_utils import clean_nan_for_json



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
    Cria o grafo do Multi-Deck Agent especializado para comparações.
    
    Fluxo:
    1. Comparison Tool Router: Verifica se há tool de comparação disponível
       - Se tool executou: vai direto para Comparison Interpreter para formatar resultado
       - Se tool não executou: vai para Comparison Interpreter que retorna mensagem informando
    2. Comparison Interpreter: Formata resultado da tool ou retorna mensagem quando não há tool
    """
    # Importar nodes específicos do multi-deck
    from newave_agent.app.agents.multi_deck.nodes import (
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
    Retorna o estado inicial para uma query multi-deck.
    
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
            # Pegar os dois mais recentes (últimos da lista ordenada)
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
            safe_print(f"[MULTI-DECK] Erro ao carregar decks: {e}")
    
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
    """Executa uma query no Multi-Deck Agent."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)
    
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query (multi-deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Selected decks: {selected_decks}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="multi-deck-query",
        metadata={"query": query[:100], "selected_decks": selected_decks}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    if langfuse_handler:
        safe_print(f"[LANGFUSE DEBUG] ✅ Iniciando query com rastreamento Langfuse")
    else:
        safe_print(f"[LANGFUSE DEBUG] ⚠️ Executando query SEM rastreamento Langfuse")
    
    safe_print("[LANGFUSE DEBUG] Chamando agent.invoke...")
    result = agent.invoke(initial_state, config=config)
    safe_print("[LANGFUSE DEBUG] ✅ agent.invoke concluído")
    
    if langfuse_handler:
        safe_print("[LANGFUSE DEBUG] Iniciando flush do Langfuse...")
        try:
            if hasattr(langfuse_handler, 'flush'):
                langfuse_handler.flush()
            from newave_agent.app.utils.observability import flush_langfuse
            flush_langfuse()
        except Exception as e:
            safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush: {e}")
    
    safe_print("[LANGFUSE DEBUG] ===== FIM: run_query (multi-deck) =====")
    return result


def run_query_stream(
    query: str, 
    deck_path: str, 
    session_id: Optional[str] = None, 
    selected_decks: Optional[List[str]] = None
) -> Generator[str, None, None]:
    """Executa uma query no Multi-Deck Agent com streaming de eventos."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks)
    
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query_stream (multi-deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Selected decks: {selected_decks}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="multi-deck-query-stream",
        metadata={"query": query[:100], "streaming": True, "selected_decks": selected_decks}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    if langfuse_handler:
        safe_print(f"[LANGFUSE DEBUG] ✅ Iniciando query stream com rastreamento Langfuse")
    else:
        safe_print(f"[LANGFUSE DEBUG] ⚠️ Executando query stream SEM rastreamento Langfuse")
    
    # Incluir informações dos decks selecionados no evento de início
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
                if node_name == "comparison_tool_router":
                    disambiguation = node_output.get("disambiguation")
                    tool_route = node_output.get("tool_route", False)
                    from_disambiguation = node_output.get("from_disambiguation", False)
                    tool_used = node_output.get("tool_used")
                    tool_result = node_output.get("tool_result", {})
                    
                    if disambiguation:
                        has_disambiguation = True
                        # #region agent log
                        write_debug_log({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "B",
                            "location": "multi_deck/graph.py:377",
                            "message": "Disambiguation detected, sending event",
                            "data": {"disambiguation_keys": list(disambiguation.keys()) if disambiguation else []},
                            "timestamp": int(__import__('time').time() * 1000)
                        })
                        # #endregion
                        yield f"data: {json.dumps({'type': 'disambiguation', 'data': disambiguation})}\n\n"
                    elif tool_route:
                        if from_disambiguation:
                            has_disambiguation = True
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Tool {tool_used} executada com sucesso!'})}\n\n"
                        if tool_result.get("success"):
                            summary = tool_result.get("summary", {})
                            total_registros = summary.get("total_registros", 0)
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f' {total_registros} registros processados'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': '⚠️ Nenhuma tool disponível'})}\n\n"
                
                elif node_name == "comparison_interpreter":
                    response = node_output.get("final_response") if node_output else None
                    comparison_data = node_output.get("comparison_data") if node_output else None
                    safe_print(f"[GRAPH] Comparison Interpreter retornou resposta: {len(response) if response else 0} caracteres")
                    if response and response.strip():
                        safe_print(f"[GRAPH] Emitindo resposta do comparison interpreter ({len(response)} caracteres)")
                        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        cleaned_comparison_data = clean_nan_for_json(comparison_data) if comparison_data else None
                        # Debug: verificar dados antes de enviar
                        if cleaned_comparison_data:
                            safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - visualization_type: {cleaned_comparison_data.get('visualization_type')}")
                            safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - tool_name: {cleaned_comparison_data.get('tool_name')}")
                            safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - keys: {list(cleaned_comparison_data.keys())}")
                            safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - chart_data presente: {cleaned_comparison_data.get('chart_data') is not None}")
                            matrix_data = cleaned_comparison_data.get('matrix_data')
                            if matrix_data:
                                safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - matrix_data presente: {len(matrix_data) if isinstance(matrix_data, list) else 'N/A'} registros")
                                if isinstance(matrix_data, list) and len(matrix_data) > 0:
                                    safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - matrix_data[0]: {matrix_data[0]}")
                            else:
                                safe_print(f"[GRAPH] [DEBUG] Enviando comparison_data - matrix_data: None ou vazio")
                        yield f"data: {json.dumps({'type': 'response_complete', 'response': response, 'comparison_data': cleaned_comparison_data}, allow_nan=False)}\n\n"
                
                if not (node_name == "comparison_tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"
        
        if not has_disambiguation:
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': ''})}\n\n"
        
        if langfuse_handler:
            safe_print("[LANGFUSE DEBUG] Iniciando flush do Langfuse (stream)...")
            try:
                if hasattr(langfuse_handler, 'flush'):
                    langfuse_handler.flush()
                from newave_agent.app.utils.observability import flush_langfuse
                flush_langfuse()
            except Exception as e:
                safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush (stream): {e}")
        
        safe_print("[LANGFUSE DEBUG] ===== FIM: run_query_stream (multi-deck) =====")
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

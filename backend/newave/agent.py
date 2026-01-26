"""
Graph para Single Deck Agent - especializado para consultas de um único deck.
"""

# Standard library imports
import json
import math
import os
from typing import Generator, Any, Optional

# Third-party imports
from langgraph.graph import StateGraph, END

# Local imports
from backend.newave.state import SingleDeckState
from backend.core.utils.observability import get_langfuse_handler, flush_langfuse
from backend.newave.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
from backend.newave.config import safe_print
from backend.core.utils.debug import write_debug_log
from backend.core.utils.json_utils import clean_nan_for_json



# Descrições dos nodes para streaming
NODE_DESCRIPTIONS = {
    "tool_router": {
        "name": "Tool Router",
        "icon": "[TOOL]",
        "description": "Verificando se ha tool pre-programada disponivel..."
    },
    "interpreter": {
        "name": "Interpreter",
        "icon": "[AI]",
        "description": "Formatando resposta..."
    }
}


def should_continue_after_tool_router(state: SingleDeckState) -> str:
    """
    Decide o próximo passo após Tool Router.
    
    - Se disambiguation: termina o fluxo (disambiguation já foi emitida)
    - Caso contrário: sempre vai para interpreter (com ou sem tool)
    """
    tool_route = state.get("tool_route", False)
    disambiguation = state.get("disambiguation")
    
    # #region agent log
    write_debug_log({
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "graph.py:106",
        "message": "Should continue after tool router",
        "data": {"tool_route": tool_route, "has_disambiguation": bool(disambiguation), "next_node": "END" if disambiguation else "interpreter"},
        "timestamp": int(__import__('time').time() * 1000)
    })
    # #endregion
    
    if disambiguation:
        # Disambiguation detectada - terminar fluxo imediatamente
        return END
    else:
        # Sempre vai para interpreter (com ou sem tool)
        # O interpreter vai verificar se há tool_result e processar adequadamente
        return "interpreter"


def create_single_deck_agent() -> StateGraph:
    """
    Cria o grafo do Single Deck Agent.
    
    Fluxo:
    1. Tool Router (entry point): Verifica se há tool pré-programada
       - Se tool executou: vai direto para Interpreter para formatar resultado
       - Se tool não executou: vai para Interpreter que retorna mensagem informando
    2. Interpreter: Formata resultado da tool ou retorna mensagem quando não há tool
    """
    # Importar nodes específicos do single deck
    from backend.newave.agents.single_deck.nodes import (
        tool_router_node,
        interpreter_node,
    )
    
    workflow = StateGraph(SingleDeckState)
    
    # Nodes disponíveis
    workflow.add_node("tool_router", tool_router_node)
    workflow.add_node("interpreter", interpreter_node)
    
    # Entry point: sempre começa com Tool Router
    workflow.set_entry_point("tool_router")
    
    # Fluxo: tool_router → interpreter (sempre, exceto disambiguation que termina)
    workflow.add_conditional_edges(
        "tool_router",
        should_continue_after_tool_router,
        {
            END: END,  # Termina fluxo quando há disambiguation
            "interpreter": "interpreter"
        }
    )
    
    workflow.add_edge("interpreter", END)
    
    return workflow.compile()


_agent = None


def get_single_deck_agent():
    """Retorna a instância do Single Deck Agent (singleton)."""
    global _agent
    if _agent is None:
        _agent = create_single_deck_agent()
    return _agent


def reset_single_deck_agent():
    """Força recriação do agent."""
    global _agent
    _agent = None


def get_initial_state(query: str, deck_path: str) -> dict:
    """Retorna o estado inicial para uma query single deck."""
    return {
        "query": query,
        "deck_path": deck_path,
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
        # Campos para Visualização
        "comparison_data": None,
        "visualization_data": None,
        # Campos para escolha do usuário (requires_user_choice)
        "requires_user_choice": None,
        "alternative_type": None
    }


def run_query(query: str, deck_path: str, session_id: Optional[str] = None) -> dict:
    """Executa uma query no Single Deck Agent."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path)
    
    # Configurar Langfuse para observabilidade
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query (single deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="single-deck-query",
        metadata={"query": query[:100]},
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    
    safe_print("[LANGFUSE DEBUG] Configurando callbacks para agent.invoke...")
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    if langfuse_handler:
        safe_print(f"[LANGFUSE DEBUG] ✅ Iniciando query com rastreamento Langfuse")
    else:
        safe_print(f"[LANGFUSE DEBUG] ⚠️ Executando query SEM rastreamento Langfuse")
    
    safe_print("[LANGFUSE DEBUG] Chamando agent.invoke...")
    result = agent.invoke(initial_state, config=config)
    safe_print("[LANGFUSE DEBUG] ✅ agent.invoke concluído")
    
    # Fazer flush do Langfuse
    if langfuse_handler:
        safe_print("[LANGFUSE DEBUG] Iniciando flush do Langfuse...")
        try:
            if hasattr(langfuse_handler, 'flush'):
                langfuse_handler.flush()
            flush_langfuse(
                public_key=LANGFUSE_PUBLIC_KEY,
                secret_key=LANGFUSE_SECRET_KEY,
                host=LANGFUSE_HOST
            )
        except Exception as e:
            safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush: {e}")
    
    safe_print("[LANGFUSE DEBUG] ===== FIM: run_query (single deck) =====")
    return result


def run_query_stream(query: str, deck_path: str, session_id: Optional[str] = None) -> Generator[str, None, None]:
    """Executa uma query no Single Deck Agent com streaming de eventos."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path)
    
    # Configurar Langfuse para observabilidade
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query_stream (single deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="single-deck-query-stream",
        metadata={"query": query[:100], "streaming": True},
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    if langfuse_handler:
        safe_print(f"[LANGFUSE DEBUG] ✅ Iniciando query stream com rastreamento Langfuse")
    else:
        safe_print(f"[LANGFUSE DEBUG] ⚠️ Executando query stream SEM rastreamento Langfuse")
    
    yield f"data: {json.dumps({'type': 'start', 'message': 'Iniciando processamento...'})}\n\n"
    
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
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info, 'retry': current_retry})}\n\n"
                
                # Detalhes específicos de cada node
                if node_name == "tool_router":
                    tool_route = node_output.get("tool_route", False)
                    disambiguation = node_output.get("disambiguation")
                    from_disambiguation = node_output.get("from_disambiguation", False)
                    tool_used = node_output.get("tool_used")
                    tool_result = node_output.get("tool_result", {})
                    
                    # #region agent log
                    write_debug_log({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "graph.py:438",
                        "message": "Tool router output",
                        "data": {"tool_route": tool_route, "has_disambiguation": bool(disambiguation), "tool_used": tool_used},
                        "timestamp": int(__import__('time').time() * 1000)
                    })
                    # #endregion
                    
                    if disambiguation:
                        has_disambiguation = True
                        yield f"data: {json.dumps({'type': 'disambiguation', 'data': disambiguation})}\n\n"
                    elif tool_route:
                        if from_disambiguation:
                            has_disambiguation = True
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Tool {tool_used} executada com sucesso!'})}\n\n"
                        if tool_result.get("success"):
                            summary = tool_result.get("summary", {})
                            yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f' {summary.get("total_registros", 0)} registros processados'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': '⚠️ Nenhuma tool disponível'})}\n\n"
                
                elif node_name == "interpreter":
                    response = node_output.get("final_response") if node_output else None
                    visualization_data = node_output.get("visualization_data") if node_output else None
                    safe_print(f"[GRAPH] Interpreter retornou resposta: {len(response) if response else 0} caracteres")
                    if visualization_data:
                        safe_print(f"[GRAPH] Interpreter retornou visualization_data: {visualization_data.get('visualization_type', 'N/A')}")
                    
                    # #region agent log
                    write_debug_log({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "D",
                        "location": "graph.py:497",
                        "message": "Interpreter output in graph",
                        "data": {
                            "has_response": bool(response),
                            "has_visualization_data": visualization_data is not None,
                            "response_length": len(response) if response else 0,
                            "response_preview": response[:200] if response else None,
                            "node_output_keys": list(node_output.keys()) if node_output else []
                        },
                        "timestamp": int(__import__('time').time() * 1000)
                    })
                    # #endregion
                    
                    if response and response.strip():
                        safe_print(f"[GRAPH] Emitindo resposta do interpreter ({len(response)} caracteres)")
                        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        
                        # Incluir visualization_data e plant_correction_followup no evento response_complete
                        response_complete_data = {'type': 'response_complete', 'response': response}
                        if visualization_data:
                            # Limpar NaN/Inf antes de serializar
                            cleaned_visualization_data = clean_nan_for_json(visualization_data)
                            response_complete_data['visualization_data'] = cleaned_visualization_data
                        
                        # Incluir plant_correction_followup se disponível
                        plant_correction_followup = node_output.get("plant_correction_followup")
                        safe_print(f"[GRAPH] Verificando plant_correction_followup no node_output: {plant_correction_followup is not None}")
                        if plant_correction_followup:
                            response_complete_data['plant_correction_followup'] = plant_correction_followup
                            safe_print(f"[GRAPH] ✅ plant_correction_followup incluído no response_complete_data")
                            safe_print(f"[GRAPH]   Chaves do followup: {list(plant_correction_followup.keys())}")
                        else:
                            safe_print(f"[GRAPH] ⚠️ plant_correction_followup não encontrado no node_output")
                            safe_print(f"[GRAPH]   Chaves disponíveis no node_output: {list(node_output.keys())}")
                        
                        yield f"data: {json.dumps(response_complete_data, allow_nan=False)}\n\n"
                        
                        # #region agent log
                        write_debug_log({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "D",
                            "location": "graph.py:505",
                            "message": "Response sent to frontend",
                            "data": {"response_length": len(response), "response_preview": response[:200]},
                            "timestamp": int(__import__('time').time() * 1000)
                        })
                        # #endregion
                    else:
                        safe_print(f"[GRAPH] ⚠️ Resposta vazia do interpreter")
                        if has_disambiguation:
                            safe_print(f"[GRAPH]   (Disambiguation já processada, pulando)")
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"
        
        if not has_disambiguation:
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': ''})}\n\n"
        
        # Fazer flush do Langfuse após streaming
        if langfuse_handler:
            safe_print("[LANGFUSE DEBUG] Iniciando flush do Langfuse (stream)...")
            try:
                if hasattr(langfuse_handler, 'flush'):
                    langfuse_handler.flush()
                flush_langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST
                )
            except Exception as e:
                safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush (stream): {e}")
        
        safe_print("[LANGFUSE DEBUG] ===== FIM: run_query_stream (single deck) =====")
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


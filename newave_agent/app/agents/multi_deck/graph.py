"""
Graph para Multi-Deck Agent - especializado para comparações entre decks.
Suporta N decks para comparação dinâmica.
"""

import json
import math
import os
import json as json_module
from typing import Generator, Any, Optional, List, Dict
from langgraph.graph import StateGraph, END
from newave_agent.app.agents.multi_deck.state import MultiDeckState
from newave_agent.app.agents.multi_deck.nodes.rag_nodes import (
    rag_simple_node,
    rag_enhanced_node,
)
from newave_agent.app.agents.multi_deck.nodes.llm_nodes import (
    llm_planner_node,
)
from newave_agent.app.utils.observability import get_langfuse_handler
from newave_agent.app.config import safe_print
from newave_agent.app.utils.deck_loader import (
    load_multiple_decks,
    get_deck_display_names_dict,
    list_available_decks,
)

# Função auxiliar para escrever no log de debug de forma segura
def _write_debug_log(data: dict):
    """Escreve no arquivo de debug, criando o diretório se necessário."""
    try:
        log_path = r'c:\Users\Inteli\OneDrive\Desktop\nw_multi\.cursor\debug.log'
        log_dir = os.path.dirname(log_path)
        # Criar diretório se não existir
        os.makedirs(log_dir, exist_ok=True)
        # Escrever no arquivo
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(data) + '\n')
    except Exception:
        # Silenciosamente ignorar erros de log para não interromper o fluxo
        pass


# Constantes
MAX_RETRIES = 3


def _clean_nan_for_json(obj: Any) -> Any:
    """Limpa valores NaN e Inf de um objeto antes de serializar para JSON."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {key: _clean_nan_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan_for_json(item) for item in obj]
    else:
        return obj


# Descrições dos nodes para streaming
NODE_DESCRIPTIONS = {
    "rag_simple": {
        "name": "RAG Simplificado",
        "icon": "[DOC]",
        "description": "Buscando documentacao no abstract..."
    },
    "rag_enhanced": {
        "name": "RAG Enhanced",
        "icon": "[DOCS+]",
        "description": "Buscando em toda documentacao + tools_context.md..."
    },
    "llm_planner": {
        "name": "LLM Planner",
        "icon": "[PLAN]",
        "description": "Gerando instrucoes detalhadas baseadas no contexto..."
    },
    "comparison_tool_router": {
        "name": "Comparison Tool Router",
        "icon": "[TOOL]",
        "description": "Verificando se ha tool de comparacao disponivel..."
    },
    "comparison_coder": {
        "name": "Code Generator", 
        "icon": "[CODE]",
        "description": "Gerando codigo Python para comparar os decks..."
    },
    "comparison_executor": {
        "name": "Code Executor",
        "icon": "[EXEC]",
        "description": "Executando o codigo gerado nos decks selecionados..."
    },
    "comparison_interpreter": {
        "name": "Comparison Interpreter",
        "icon": "[AI]",
        "description": "Analisando resultados e gerando comparacao..."
    },
    "retry_check": {
        "name": "Retry Check",
        "icon": "[RETRY]",
        "description": "Verificando se precisa tentar novamente..."
    }
}


def should_use_llm_mode(state: MultiDeckState) -> str:
    """Verifica se deve usar modo LLM."""
    llm_instructions = state.get("llm_instructions")
    if llm_instructions:
        return "llm"
    return "normal"


def should_continue_after_tool_router(state: MultiDeckState) -> str:
    """Decide o próximo passo após Comparison Tool Router."""
    tool_route = state.get("tool_route", False)
    disambiguation = state.get("disambiguation")
    
    if disambiguation:
        return END
    elif tool_route:
        return "comparison_interpreter"
    else:
        return "rag_simple"


def should_retry(state: MultiDeckState) -> str:
    """Decide se deve tentar novamente após erro de execução."""
    execution_result = state.get("execution_result") or {}
    success = execution_result.get("success", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", MAX_RETRIES)
    
    if success or retry_count >= max_retries:
        return "comparison_interpreter"
    
    return "comparison_coder"


def retry_check_node(state: MultiDeckState) -> dict:
    """Node que atualiza o estado para retry."""
    execution_result = state.get("execution_result") or {}
    success = execution_result.get("success", False)
    
    if not success:
        retry_count = state.get("retry_count", 0) + 1
        error_history = list(state.get("error_history", []))
        error_msg = execution_result.get("stderr", "Erro desconhecido")
        error_history.append(error_msg)
        
        return {
            "retry_count": retry_count,
            "error_history": error_history
        }
    
    return {}


def create_multi_deck_agent() -> StateGraph:
    """
    Cria o grafo do Multi-Deck Agent especializado para comparações.
    
    Fluxo:
    1. Comparison Tool Router: Verifica se há tool de comparação disponível
       - Se tool executou: vai direto para Comparison Interpreter
       - Se tool não executou: continua para RAG Simplificado
    2. RAG Simplificado: Busca no abstract.md
    3. Comparison Coder: Gera código que processa os decks selecionados
    4. Comparison Executor: Executa código em paralelo nos N decks
    5. Retry Check: Verifica se precisa retry
    6. Comparison Interpreter: Interpreta e formata comparação
    """
    # Importar nodes específicos do multi-deck
    from newave_agent.app.agents.multi_deck.nodes import (
        comparison_tool_router_node,
        comparison_coder_node,
        comparison_executor_node,
        comparison_interpreter_node,
    )
    
    workflow = StateGraph(MultiDeckState)
    
    # Nodes disponíveis
    workflow.add_node("rag_simple", rag_simple_node)
    workflow.add_node("rag_enhanced", rag_enhanced_node)
    workflow.add_node("llm_planner", llm_planner_node)
    workflow.add_node("comparison_tool_router", comparison_tool_router_node)
    workflow.add_node("comparison_coder", comparison_coder_node)
    workflow.add_node("comparison_executor", comparison_executor_node)
    workflow.add_node("retry_check", retry_check_node)
    workflow.add_node("comparison_interpreter", comparison_interpreter_node)
    
    # Entry point condicional: LLM Mode ou Normal
    workflow.set_conditional_entry_point(
        should_use_llm_mode,
        {
            "llm": "rag_enhanced",
            "normal": "comparison_tool_router"
        }
    )
    
    # Fluxo LLM Mode: rag_enhanced → llm_planner → comparison_coder → comparison_executor → retry_check → comparison_interpreter
    workflow.add_edge("rag_enhanced", "llm_planner")
    workflow.add_edge("llm_planner", "comparison_coder")
    
    # Fluxo modo normal: comparison_tool_router → (comparison_interpreter ou rag_simple → comparison_coder)
    workflow.add_conditional_edges(
        "comparison_tool_router",
        should_continue_after_tool_router,
        {
            END: END,
            "comparison_interpreter": "comparison_interpreter",
            "rag_simple": "rag_simple"
        }
    )
    
    # RAG simplificado sempre vai para Comparison Coder
    workflow.add_edge("rag_simple", "comparison_coder")
    
    # Comparison Coder → Comparison Executor
    workflow.add_edge("comparison_coder", "comparison_executor")
    workflow.add_edge("comparison_executor", "retry_check")
    
    # Decisão condicional: retry ou comparison_interpreter
    workflow.add_conditional_edges(
        "retry_check",
        should_retry,
        {
            "comparison_coder": "comparison_coder",
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
    selected_decks: Optional[List[str]] = None,
    llm_mode: bool = False
) -> dict:
    """
    Retorna o estado inicial para uma query multi-deck.
    
    Args:
        query: A pergunta do usuário
        deck_path: Caminho do deck principal (para compatibilidade)
        selected_decks: Lista de nomes dos decks selecionados
        llm_mode: Se True, usa modo LLM
        
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
        "relevant_docs": [],
        "generated_code": "",
        "execution_result": {},
        "final_response": "",
        "error": None,
        "messages": [],
        "retry_count": 0,
        "max_retries": MAX_RETRIES,
        "code_history": [],
        "error_history": [],
        "selected_files": [],
        "validation_result": None,
        "rag_status": "success",
        "fallback_response": None,
        "tried_files": [],
        "rejection_reasons": [],
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        "disambiguation": None,
        "comparison_data": None,
        "llm_instructions": None if not llm_mode else "",
        # Campos para escolha do usuário (requires_user_choice)
        "requires_user_choice": None,
        "alternative_type": None
    }


def run_query(
    query: str, 
    deck_path: str, 
    session_id: Optional[str] = None, 
    selected_decks: Optional[List[str]] = None,
    llm_mode: bool = False
) -> dict:
    """Executa uma query no Multi-Deck Agent."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks, llm_mode)
    
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
    selected_decks: Optional[List[str]] = None,
    llm_mode: bool = False
) -> Generator[str, None, None]:
    """Executa uma query no Multi-Deck Agent com streaming de eventos."""
    agent = get_multi_deck_agent()
    initial_state = get_initial_state(query, deck_path, selected_decks, llm_mode)
    
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
    is_fallback = False
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
                
                if node_name == "comparison_coder" and current_retry > 0:
                    node_info = {
                        **node_info,
                        "name": f"Code Generator (Tentativa {current_retry + 1})",
                        "description": f"Corrigindo código... (tentativa {current_retry + 1}/{MAX_RETRIES})"
                    }
                
                if not (node_name == "comparison_tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info, 'retry': current_retry})}\n\n"
                
                # Detalhes específicos de cada node (similar ao single deck)
                if node_name == "comparison_tool_router":
                    disambiguation = node_output.get("disambiguation")
                    tool_route = node_output.get("tool_route", False)
                    from_disambiguation = node_output.get("from_disambiguation", False)
                    tool_used = node_output.get("tool_used")
                    tool_result = node_output.get("tool_result", {})
                    
                    if disambiguation:
                        has_disambiguation = True
                        # #region agent log
                        _write_debug_log({
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
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': '⚠️ Nenhuma tool disponível, continuando fluxo normal'})}\n\n"
                
                elif node_name == "comparison_interpreter":
                    response = node_output.get("final_response") if node_output else None
                    comparison_data = node_output.get("comparison_data") if node_output else None
                    safe_print(f"[GRAPH] Comparison Interpreter retornou resposta: {len(response) if response else 0} caracteres")
                    if response and response.strip():
                        safe_print(f"[GRAPH] Emitindo resposta do comparison interpreter ({len(response)} caracteres)")
                        yield f"data: {json.dumps({'type': 'response_start', 'is_fallback': is_fallback})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        cleaned_comparison_data = _clean_nan_for_json(comparison_data) if comparison_data else None
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
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': '', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        
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

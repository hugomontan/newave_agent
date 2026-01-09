"""
Graph para Single Deck Agent - especializado para consultas de um único deck.
"""

import json
import math
from typing import Generator, Any, Optional
from langgraph.graph import StateGraph, END
from app.agents.single_deck.state import SingleDeckState
from app.agents.shared.rag_nodes import (
    rag_retriever_node,
    rag_simple_node,
    rag_enhanced_node,
)
from app.agents.shared.llm_nodes import (
    llm_planner_node,
)
from app.utils.observability import get_langfuse_handler
from app.config import safe_print


# Constantes
MAX_RETRIES = 3


def _clean_nan_for_json(obj: Any) -> Any:
    """
    Limpa valores NaN e Inf de um objeto antes de serializar para JSON.
    Converte NaN e Inf para None.
    """
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
    "rag": {
        "name": "RAG Retriever",
        "icon": "[DOCS]",
        "description": "Buscando documentacao e validando arquivos relevantes..."
    },
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
    "tool_router": {
        "name": "Tool Router",
        "icon": "[TOOL]",
        "description": "Verificando se ha tool pre-programada disponivel..."
    },
    "coder": {
        "name": "Code Generator", 
        "icon": "[CODE]",
        "description": "Gerando codigo Python para analisar o deck NEWAVE..."
    },
    "executor": {
        "name": "Code Executor",
        "icon": "[EXEC]",
        "description": "Executando o codigo gerado..."
    },
    "interpreter": {
        "name": "Interpreter",
        "icon": "[AI]",
        "description": "Analisando resultados e gerando resposta..."
    },
    "retry_check": {
        "name": "Retry Check",
        "icon": "[RETRY]",
        "description": "Verificando se precisa tentar novamente..."
    }
}


def should_use_llm_mode(state: SingleDeckState) -> str:
    """
    Verifica se deve usar modo LLM baseado em llm_instructions.
    
    Returns:
        "llm" se llm_instructions existe, "normal" caso contrário
    """
    llm_instructions = state.get("llm_instructions")
    if llm_instructions:
        return "llm"
    return "normal"


def should_continue_after_tool_router(state: SingleDeckState) -> str:
    """
    Decide o próximo passo após Tool Router.
    
    - Se disambiguation: termina o fluxo (disambiguation já foi emitida)
    - Se tool executou: vai para interpreter
    - Se tool não executou: faz RAG simplificado para preparar contexto para coder
    """
    tool_route = state.get("tool_route", False)
    disambiguation = state.get("disambiguation")
    
    if disambiguation:
        # Disambiguation detectada - terminar fluxo imediatamente
        return END
    elif tool_route:
        # Tool foi executada, ir direto para interpreter
        return "interpreter"
    else:
        # Nenhuma tool disponível, fazer RAG simplificado para coder
        return "rag_simple"


def should_retry(state: SingleDeckState) -> str:
    """
    Decide se deve tentar novamente após erro de execução.
    """
    execution_result = state.get("execution_result") or {}
    success = execution_result.get("success", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", MAX_RETRIES)
    
    if success or retry_count >= max_retries:
        return "interpreter"
    
    return "coder"


def retry_check_node(state: SingleDeckState) -> dict:
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


def create_single_deck_agent() -> StateGraph:
    """
    Cria o grafo do Single Deck Agent.
    
    Fluxo otimizado (modo normal):
    1. Tool Router (entry point): Verifica se há tool pré-programada
       - Se tool executou: vai direto para Interpreter ✅
       - Se tool não executou: continua para RAG Simplificado
    2. RAG Simplificado: Busca apenas no abstract.md (sem validação iterativa)
       - Retorna contexto para Coder
    3. Coder: Gera código Python usando contexto do abstract
    4. Executor: Executa o código
    5. Retry Check: Verifica se precisa retry
    6. Interpreter: Interpreta resultados e gera resposta
    
    Fluxo LLM Mode (quando llm_instructions está presente):
    1. RAG Enhanced: Busca em toda documentação + tools_context.md
    2. LLM Planner: Gera instruções detalhadas baseadas no contexto
    3. Coder: Gera código usando instruções enriquecidas
    4. Executor: Executa o código
    5. Retry Check: Verifica se precisa retry
    6. Interpreter: Interpreta resultados e gera resposta
    """
    # Importar nodes específicos do single deck
    from app.agents.single_deck.nodes import (
        tool_router_node,
        coder_node,
        executor_node,
        interpreter_node,
    )
    
    workflow = StateGraph(SingleDeckState)
    
    # Nodes disponíveis
    workflow.add_node("rag", rag_retriever_node)  # Mantido para uso futuro/fallback
    workflow.add_node("rag_simple", rag_simple_node)  # RAG simplificado (modo normal)
    workflow.add_node("rag_enhanced", rag_enhanced_node)  # RAG completo (modo LLM)
    workflow.add_node("llm_planner", llm_planner_node)  # LLM Planner (modo LLM)
    workflow.add_node("tool_router", tool_router_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("retry_check", retry_check_node)
    workflow.add_node("interpreter", interpreter_node)
    
    # Entry point condicional: LLM Mode ou Normal
    workflow.set_conditional_entry_point(
        should_use_llm_mode,
        {
            "llm": "rag_enhanced",  # Modo LLM: começa com RAG Enhanced
            "normal": "tool_router"  # Modo normal: começa com Tool Router
        }
    )
    
    # Fluxo LLM Mode: rag_enhanced → llm_planner → coder → executor → retry_check → interpreter
    workflow.add_edge("rag_enhanced", "llm_planner")
    workflow.add_edge("llm_planner", "coder")
    
    # Fluxo modo normal: tool_router → (interpreter ou rag_simple → coder)
    workflow.add_conditional_edges(
        "tool_router",
        should_continue_after_tool_router,
        {
            END: END,  # Termina fluxo quando há disambiguation
            "interpreter": "interpreter",
            "rag_simple": "rag_simple"
        }
    )
    
    # RAG simplificado sempre vai para Coder
    workflow.add_edge("rag_simple", "coder")
    
    # Coder → Executor (comum para ambos os modos)
    workflow.add_edge("coder", "executor")
    workflow.add_edge("executor", "retry_check")
    
    # Decisão condicional: retry ou interpreter
    workflow.add_conditional_edges(
        "retry_check",
        should_retry,
        {
            "coder": "coder",
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


def get_initial_state(query: str, deck_path: str, llm_mode: bool = False) -> dict:
    """Retorna o estado inicial para uma query single deck."""
    return {
        "query": query,
        "deck_path": deck_path,
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
        # Campos para RAG com Self-Reflection
        "selected_files": [],
        "validation_result": None,
        "rag_status": "success",
        "fallback_response": None,
        "tried_files": [],
        "rejection_reasons": [],
        # Campos para Tools
        "tool_route": False,
        "tool_result": None,
        "tool_used": None,
        # Campos para Disambiguation
        "disambiguation": None,
        # Campos para LLM Mode
        "llm_instructions": None if not llm_mode else ""  # Será preenchido pelo LLM Planner
    }


def run_query(query: str, deck_path: str, session_id: Optional[str] = None, llm_mode: bool = False) -> dict:
    """Executa uma query no Single Deck Agent."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path, llm_mode)
    
    # Configurar Langfuse para observabilidade
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query (single deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="single-deck-query",
        metadata={"query": query[:100]}
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
            from app.utils.observability import flush_langfuse
            flush_langfuse()
        except Exception as e:
            safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush: {e}")
    
    safe_print("[LANGFUSE DEBUG] ===== FIM: run_query (single deck) =====")
    return result


def run_query_stream(query: str, deck_path: str, session_id: Optional[str] = None, llm_mode: bool = False) -> Generator[str, None, None]:
    """Executa uma query no Single Deck Agent com streaming de eventos."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path, llm_mode)
    
    # Configurar Langfuse para observabilidade
    safe_print("[LANGFUSE DEBUG] ===== INÍCIO: run_query_stream (single deck) =====")
    safe_print(f"[LANGFUSE DEBUG] Query: {query[:100]}")
    safe_print(f"[LANGFUSE DEBUG] Deck path: {deck_path}")
    safe_print(f"[LANGFUSE DEBUG] Session ID: {session_id}")
    
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="single-deck-query-stream",
        metadata={"query": query[:100], "streaming": True}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    if langfuse_handler:
        safe_print(f"[LANGFUSE DEBUG] ✅ Iniciando query stream com rastreamento Langfuse")
    else:
        safe_print(f"[LANGFUSE DEBUG] ⚠️ Executando query stream SEM rastreamento Langfuse")
    
    yield f"data: {json.dumps({'type': 'start', 'message': 'Iniciando processamento...'})}\n\n"
    
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
                
                if node_name == "coder" and current_retry > 0:
                    node_info = {
                        **node_info,
                        "name": f"Code Generator (Tentativa {current_retry + 1})",
                        "description": f"Corrigindo código... (tentativa {current_retry + 1}/{MAX_RETRIES})"
                    }
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info, 'retry': current_retry})}\n\n"
                
                # Detalhes específicos de cada node (similar ao código original)
                if node_name == "rag":
                    rag_status = node_output.get("rag_status", "success")
                    selected_files = node_output.get("selected_files") or []
                    tried_files = node_output.get("tried_files") or []
                    validation_result = node_output.get("validation_result") or {}
                    
                    if rag_status == "fallback":
                        is_fallback = True
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'⚠️ Arquivos testados ({len(tried_files)}): {", ".join(tried_files)} - Nenhum adequado para a pergunta'})}\n\n"
                    elif selected_files:
                        colunas = validation_result.get("colunas_relevantes", []) if validation_result else []
                        detail = f'✅ Arquivo validado: {selected_files[0].upper()}' 
                        if colunas:
                            detail += f' | Colunas: {", ".join(colunas[:5])}'
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': detail})}\n\n"
                
                elif node_name == "rag_enhanced":
                    rag_status = node_output.get("rag_status", "success")
                    relevant_docs = node_output.get("relevant_docs", [])
                    if relevant_docs:
                        total_chars = sum(len(doc) for doc in relevant_docs)
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Contexto completo preparado ({total_chars} caracteres) - documentacao NEWAVE + tools_context.md'})}\n\n"
                
                elif node_name == "llm_planner":
                    llm_instructions = node_output.get("llm_instructions")
                    if llm_instructions:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Instrucoes detalhadas geradas ({len(llm_instructions)} caracteres)'})}\n\n"
                
                elif node_name == "coder":
                    code = node_output.get("generated_code", "")
                    if code:
                        yield f"data: {json.dumps({'type': 'code_start', 'node': node_name})}\n\n"
                        for i, line in enumerate(code.split('\n')):
                            yield f"data: {json.dumps({'type': 'code_line', 'line': line, 'line_number': i + 1})}\n\n"
                        yield f"data: {json.dumps({'type': 'code_complete', 'code': code})}\n\n"
                
                elif node_name == "tool_router":
                    tool_route = node_output.get("tool_route", False)
                    disambiguation = node_output.get("disambiguation")
                    from_disambiguation = node_output.get("from_disambiguation", False)
                    tool_used = node_output.get("tool_used")
                    tool_result = node_output.get("tool_result", {})
                    
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
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': '⚠️ Nenhuma tool disponível, continuando fluxo normal'})}\n\n"
                
                elif node_name == "executor":
                    result = node_output.get("execution_result") or {}
                    yield f"data: {json.dumps({'type': 'execution_result', 'success': result.get('success', False), 'stdout': result.get('stdout', ''), 'stderr': result.get('stderr', '')})}\n\n"
                
                elif node_name == "retry_check":
                    new_retry = node_output.get("retry_count", current_retry)
                    if new_retry > current_retry:
                        current_retry = new_retry
                        yield f"data: {json.dumps({'type': 'retry', 'retry_count': current_retry, 'max_retries': MAX_RETRIES, 'message': f'Erro detectado. Tentando novamente ({current_retry}/{MAX_RETRIES})...'})}\n\n"
                
                elif node_name == "interpreter":
                    response = node_output.get("final_response") if node_output else None
                    safe_print(f"[GRAPH] Interpreter retornou resposta: {len(response) if response else 0} caracteres")
                    if response and response.strip():
                        safe_print(f"[GRAPH] Emitindo resposta do interpreter ({len(response)} caracteres)")
                        yield f"data: {json.dumps({'type': 'response_start', 'is_fallback': is_fallback})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        yield f"data: {json.dumps({'type': 'response_complete', 'response': response}, allow_nan=False)}\n\n"
                    else:
                        safe_print(f"[GRAPH] ⚠️ Resposta vazia do interpreter")
                        if has_disambiguation:
                            safe_print(f"[GRAPH]   (Disambiguation já processada, pulando)")
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"
        
        if not has_disambiguation:
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': '', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        
        # Fazer flush do Langfuse após streaming
        if langfuse_handler:
            safe_print("[LANGFUSE DEBUG] Iniciando flush do Langfuse (stream)...")
            try:
                if hasattr(langfuse_handler, 'flush'):
                    langfuse_handler.flush()
                from app.utils.observability import flush_langfuse
                flush_langfuse()
            except Exception as e:
                safe_print(f"[LANGFUSE DEBUG] ❌ Erro ao fazer flush (stream): {e}")
        
        safe_print("[LANGFUSE DEBUG] ===== FIM: run_query_stream (single deck) =====")
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


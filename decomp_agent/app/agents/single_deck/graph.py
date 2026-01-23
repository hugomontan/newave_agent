"""
Graph para Single Deck Agent DECOMP - especializado para consultas de um único deck.
"""

import json
import math
import os
import json as json_module
from typing import Generator, Any, Optional
from langgraph.graph import StateGraph, END
from decomp_agent.app.agents.single_deck.state import SingleDeckState
from decomp_agent.app.agents.single_deck.nodes.rag_nodes import (
    rag_retriever_node,
)
from shared.utils.observability import get_langfuse_handler
from decomp_agent.app.config import safe_print

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
    
    if disambiguation:
        # Disambiguation detectada - terminar fluxo imediatamente
        return END
    else:
        # Sempre vai para interpreter (com ou sem tool)
        return "interpreter"


def create_single_deck_agent() -> StateGraph:
    """
    Cria o grafo do Single Deck Agent DECOMP.
    
    Fluxo:
    1. Tool Router (entry point): Verifica se há tool pré-programada
       - Se tool executou: vai direto para Interpreter para formatar resultado
       - Se tool não executou: vai para Interpreter que retorna mensagem informando
    2. Interpreter: Formata resultado da tool ou retorna mensagem quando não há tool
    """
    # Importar nodes específicos do single deck
    from decomp_agent.app.agents.single_deck.nodes import (
        tool_router_node,
        interpreter_node,
    )
    
    workflow = StateGraph(SingleDeckState)
    
    # Nodes disponíveis
    workflow.add_node("rag", rag_retriever_node)  # Mantido para uso futuro/fallback
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
        # Campos para escolha do usuário (requires_user_choice)
        "requires_user_choice": None,
        "alternative_type": None
    }


def run_query(query: str, deck_path: str, session_id: Optional[str] = None) -> dict:
    """Executa uma query no Single Deck Agent DECOMP."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path)
    
    # Configurar Langfuse para observabilidade
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="decomp-single-deck-query",
        metadata={"query": query[:100]}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
    result = agent.invoke(initial_state, config=config)
    
    # Fazer flush do Langfuse
    if langfuse_handler:
        try:
            if hasattr(langfuse_handler, 'flush'):
                langfuse_handler.flush()
            from shared.utils.observability import flush_langfuse
            flush_langfuse()
        except Exception:
            pass
    
    return result


def run_query_stream(query: str, deck_path: str, session_id: Optional[str] = None) -> Generator[str, None, None]:
    """Executa uma query no Single Deck Agent DECOMP com streaming de eventos."""
    agent = get_single_deck_agent()
    initial_state = get_initial_state(query, deck_path)
    
    # Configurar Langfuse para observabilidade
    langfuse_handler = get_langfuse_handler(
        session_id=session_id or deck_path,
        trace_name="decomp-single-deck-query-stream",
        metadata={"query": query[:100], "streaming": True}
    )
    
    config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}
    
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
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node_name, 'info': node_info, 'retry': current_retry})}\n\n"
                
                # Detalhes específicos de cada node
                if node_name == "rag":
                    rag_status = node_output.get("rag_status", "success")
                    selected_files = node_output.get("selected_files") or []
                    tried_files = node_output.get("tried_files") or []
                    
                    if rag_status == "fallback":
                        is_fallback = True
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'⚠️ Arquivos testados ({len(tried_files)}): {", ".join(tried_files)} - Nenhum adequado para a pergunta'})}\n\n"
                    elif selected_files:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Arquivo validado: {selected_files[0].upper()}'})}\n\n"
                
                elif node_name == "tool_router":
                    tool_route = node_output.get("tool_route", False)
                    disambiguation = node_output.get("disambiguation")
                    tool_used = node_output.get("tool_used")
                    tool_result = node_output.get("tool_result", {})
                    
                    if disambiguation:
                        has_disambiguation = True
                        yield f"data: {json.dumps({'type': 'disambiguation', 'data': disambiguation})}\n\n"
                    elif tool_route:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f'✅ Tool {tool_used} executada com sucesso!'})}\n\n"
                        if tool_result.get("success"):
                            summary = tool_result.get("summary", {})
                            yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': f' {summary.get("total_registros", 0)} registros processados'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'node_detail', 'node': node_name, 'detail': '⚠️ Nenhuma tool disponível'})}\n\n"
                
                elif node_name == "interpreter":
                    response = node_output.get("final_response") if node_output else None
                    visualization_data = node_output.get("visualization_data") if node_output else None
                    
                    if response and response.strip():
                        yield f"data: {json.dumps({'type': 'response_start', 'is_fallback': is_fallback})}\n\n"
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield f"data: {json.dumps({'type': 'response_chunk', 'chunk': response[i:i + chunk_size]})}\n\n"
                        
                        # Incluir visualization_data no evento response_complete
                        response_complete_data = {'type': 'response_complete', 'response': response}
                        if visualization_data:
                            cleaned_visualization_data = _clean_nan_for_json(visualization_data)
                            response_complete_data['visualization_data'] = cleaned_visualization_data
                        
                        yield f"data: {json.dumps(response_complete_data, allow_nan=False)}\n\n"
                
                if not (node_name == "tool_router" and node_output.get("disambiguation")):
                    yield f"data: {json.dumps({'type': 'node_complete', 'node': node_name})}\n\n"
        
        if not has_disambiguation:
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Processamento concluído!', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'message': '', 'total_retries': current_retry, 'was_fallback': is_fallback})}\n\n"
        
        # Fazer flush do Langfuse após streaming
        if langfuse_handler:
            try:
                if hasattr(langfuse_handler, 'flush'):
                    langfuse_handler.flush()
                from shared.utils.observability import flush_langfuse
                flush_langfuse()
            except Exception:
                pass
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

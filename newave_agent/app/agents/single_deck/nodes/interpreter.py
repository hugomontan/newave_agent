"""
Node que interpreta os resultados e gera a resposta final formatada em Markdown (single deck).
"""

import os
import json as json_module
from newave_agent.app.agents.single_deck.state import SingleDeckState
from newave_agent.app.config import safe_print
from newave_agent.app.utils.text_utils import clean_response_text
from shared.utils.debug import write_debug_log
from newave_agent.app.agents.single_deck.formatters.registry import get_formatter_for_tool
from newave_agent.app.tools import get_available_tools

def interpreter_node(state: SingleDeckState) -> dict:
    """
    Node que formata os resultados e gera a resposta final em Markdown.
    
    Prioridades:
    1. Se tool_result existe: formata resultado da tool usando formatters
    2. Se disambiguation existe: retorna resposta vazia (frontend cria mensagem)
    3. Caso contrário: retorna mensagem informando que não há tool disponível
    """
    # #region agent log
    write_debug_log({
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "interpreter.py:13",
        "message": "Interpreter node called",
        "data": {"has_tool_result": bool(state.get("tool_result")), "tool_used": state.get("tool_used"), "tool_route": state.get("tool_route", False)},
        "timestamp": int(__import__('time').time() * 1000)
    })
    # #endregion
    
    try:
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[INTERPRETER] Processando resultado de tool: {tool_used}")
            safe_print(f"[INTERPRETER]   Success: {tool_result.get('success', False)}")
            
            # #region agent log
            write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "interpreter.py:27",
                "message": "Tool result found, starting formatting",
                "data": {"tool_used": tool_used, "success": tool_result.get('success', False), "has_data": bool(tool_result.get('data'))},
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            # Obter tool instance para usar no registry
            tool_instance = None
            available_tools = get_available_tools(state.get("deck_path", ""))
            for tool in available_tools:
                if tool.get_name() == tool_used:
                    tool_instance = tool
                    break
            
            if tool_instance is None:
                safe_print(f"[INTERPRETER] ⚠️ Tool instance não encontrada, usando formatter genérico")
                from newave_agent.app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
                formatter = GenericSingleDeckFormatter()
            else:
                # Obter formatter via registry
                formatter = get_formatter_for_tool(tool_instance, tool_result)
            
            query = state.get("query", "")
            # Se a query veio de disambiguation, extrair apenas a parte original
            # Formato novo: "__DISAMBIG__:ToolName:original_query"
            if query.startswith("__DISAMBIG__:"):
                try:
                    parts = query.split(":", 2)
                    if len(parts) == 3:
                        query = parts[2].strip()  # Usar apenas a query original
                        safe_print(f"[INTERPRETER]   Query veio de disambiguation (formato novo), usando query original: {query[:100]}")
                except Exception as e:
                    safe_print(f"[INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
            # Formato antigo (compatibilidade): "query - tool_name"
            elif " - " in query:
                query = query.split(" - ", 1)[0].strip()
                safe_print(f"[INTERPRETER]   Query veio de disambiguation (formato antigo), usando query original: {query[:100]}")
            else:
                safe_print(f"[INTERPRETER]   Query original: {query[:100]}")
            safe_print(f"[INTERPRETER]   Usando formatter: {formatter.__class__.__name__}")
            
            # #region agent log
            write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "interpreter.py:48",
                "message": "Formatter obtained, about to format",
                "data": {"formatter_class": formatter.__class__.__name__, "query": query[:50]},
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            # Formatar resposta usando o formatter
            result = formatter.format_response(tool_result, tool_used, query)
            
            # Extrair visualization_data se presente
            visualization_data = result.get("visualization_data")
            
            # #region agent log
            write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "interpreter.py:51",
                "message": "Formatter result obtained",
                "data": {
                    "has_final_response": bool(result.get('final_response')),
                    "has_visualization_data": visualization_data is not None,
                    "response_length": len(result.get('final_response', '')),
                    "response_preview": result.get('final_response', '')[:100]
                },
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            safe_print(f"[INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            if visualization_data:
                safe_print(f"[INTERPRETER]   Visualization data presente: {visualization_data.get('visualization_type', 'N/A')}")
            
            return {
                "final_response": result.get("final_response", ""),
                "visualization_data": visualization_data
            }
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Se não há tool_result e não há disambiguation, retornar mensagem genérica
        safe_print(f"[INTERPRETER] Nenhuma tool disponível para processar a consulta")
        
        no_tool_msg = """## Não foi encontrado sentido semântico entre o pedido e os dados disponíveis

Não foi possível identificar uma correspondência semântica entre sua consulta e os dados disponíveis no sistema.

Por favor, reformule sua pergunta ou consulte a documentação para ver os tipos de dados que podem ser consultados."""
        no_tool_msg = clean_response_text(no_tool_msg, max_emojis=2)
        return {"final_response": no_tool_msg}
        
    except Exception as e:
        safe_print(f"[INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao processar resultado\n\nOcorreu um erro ao formatar a resposta: {str(e)}"
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}


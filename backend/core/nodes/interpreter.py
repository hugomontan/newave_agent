"""
Node genérico que interpreta os resultados e gera a resposta final formatada em Markdown.
Para Single Deck Agent (NEWAVE e DECOMP).
"""
from typing import Dict, Any, Optional, Callable
import inspect
from backend.core.config import safe_print, DEBUG_MODE
from backend.core.utils.text_utils import clean_response_text


def interpreter_node(
    state: Dict[str, Any],
    formatter_registry: Any,
    no_tool_message: str,
    get_available_tools_func: Callable,
    get_formatter_for_tool_func: Callable,
    get_generic_formatter_func: Optional[Callable] = None,
    debug_logger: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Node genérico que formata os resultados e gera a resposta final em Markdown.
    
    Prioridades:
    1. Se tool_result existe: formata resultado da tool usando formatters
    2. Se disambiguation existe: retorna resposta vazia (frontend cria mensagem)
    3. Caso contrário: retorna mensagem informando que não há tool disponível
    
    Args:
        state: Estado do Single Deck Agent
        formatter_registry: Registry de formatters (para compatibilidade, pode ser None)
        no_tool_message: Mensagem a exibir quando não há tool disponível
        get_available_tools_func: Função para obter tools disponíveis
        get_formatter_for_tool_func: Função para obter formatter para uma tool
        debug_logger: Função opcional para logging de debug
        
    Returns:
        Dict com final_response e visualization_data
    """
    if debug_logger and DEBUG_MODE:
        debug_logger({
            "location": "interpreter.py",
            "message": "Interpreter node called",
            "data": {
                "has_tool_result": bool(state.get("tool_result")),
                "tool_used": state.get("tool_used"),
                "tool_route": state.get("tool_route", False)
            }
        })
    
    try:
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[INTERPRETER] Processando resultado de tool: {tool_used}")
            safe_print(f"[INTERPRETER]   Success: {tool_result.get('success', False)}")
            
            if debug_logger and DEBUG_MODE:
                debug_logger({
                    "location": "interpreter.py",
                    "message": "Tool result found, starting formatting",
                    "data": {
                        "tool_used": tool_used,
                        "success": tool_result.get('success', False),
                        "has_data": bool(tool_result.get('data'))
                    }
                })
            
            # Obter tool instance para usar no registry
            tool_instance = None
            deck_path = state.get("deck_path", "")
            try:
                available_tools = get_available_tools_func(deck_path)
                for tool in available_tools:
                    if tool.get_name() == tool_used:
                        tool_instance = tool
                        break
            except Exception as e:
                safe_print(f"[INTERPRETER] [AVISO] Erro ao obter tools: {e}")
            
            if tool_instance is None:
                safe_print(f"[INTERPRETER] [AVISO] Tool instance não encontrada, usando formatter genérico")
                if get_generic_formatter_func:
                    formatter = get_generic_formatter_func()
                else:
                    # Fallback: resposta simples
                    return {
                        "final_response": clean_response_text(
                            f"## Resultado da Tool: {tool_used}\n\nErro: Não foi possível obter formatter.",
                            max_emojis=2
                        ),
                        "visualization_data": None
                    }
            else:
                # Obter formatter via registry
                safe_print(f"[INTERPRETER] Obtendo formatter para tool: {tool_used}")
                formatter = get_formatter_for_tool_func(tool_instance, tool_result)
                safe_print(f"[INTERPRETER] Formatter selecionado: {formatter.__class__.__name__}")
            
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
                    safe_print(f"[INTERPRETER] [AVISO] Erro ao limpar query de disambiguation: {e}")
            # Formato antigo (compatibilidade): "query - tool_name"
            elif " - " in query:
                query = query.split(" - ", 1)[0].strip()
                safe_print(f"[INTERPRETER]   Query veio de disambiguation (formato antigo), usando query original: {query[:100]}")
            else:
                safe_print(f"[INTERPRETER]   Query original: {query[:100]}")
            
            if debug_logger and DEBUG_MODE:
                debug_logger({
                    "location": "interpreter.py",
                    "message": "Formatter obtained, about to format",
                    "data": {
                        "formatter_class": formatter.__class__.__name__,
                        "query": query[:50]
                    }
                })
            
            # Formatar resposta usando o formatter
            try:
                # Verificar se o formatter aceita deck_path como parâmetro (DECOMP approach - mais robusto)
                sig = inspect.signature(formatter.format_response)
                if 'deck_path' in sig.parameters:
                    formatted = formatter.format_response(tool_result, tool_used, query, deck_path=deck_path)
                else:
                    formatted = formatter.format_response(tool_result, tool_used, query)
                
                safe_print(f"[INTERPRETER] [OK] Resposta formatada com sucesso")
                safe_print(f"[INTERPRETER]   Tem visualization_data: {bool(formatted.get('visualization_data'))}")
                
                if debug_logger and DEBUG_MODE:
                    debug_logger({
                        "location": "interpreter.py",
                        "message": "Formatter result obtained",
                        "data": {
                            "has_final_response": bool(formatted.get('final_response')),
                            "has_visualization_data": bool(formatted.get('visualization_data')),
                            "response_length": len(formatted.get('final_response', '')),
                            "response_preview": formatted.get('final_response', '')[:100]
                        }
                    })
                
                result = {
                    "final_response": clean_response_text(formatted.get("final_response", ""), max_emojis=2),
                    "visualization_data": formatted.get("visualization_data")
                }
                # Repassar requires_user_choice e alternative_type quando a tool oferece alternativa (ex: VAZMIN -> VAZMINT)
                if formatted.get("requires_user_choice") and formatted.get("alternative_type"):
                    result["requires_user_choice"] = True
                    result["alternative_type"] = formatted.get("alternative_type", "")
                
                # Incluir plant_correction_followup se disponível no state
                plant_correction_followup = state.get("plant_correction_followup")
                safe_print(f"[INTERPRETER] Verificando plant_correction_followup no state: {plant_correction_followup is not None}")
                if plant_correction_followup:
                    result["plant_correction_followup"] = plant_correction_followup
                    safe_print(f"[INTERPRETER] ✅ plant_correction_followup incluído no resultado do interpreter")
                else:
                    safe_print(f"[INTERPRETER] ⚠️ plant_correction_followup não encontrado no state")
                    safe_print(f"[INTERPRETER]   Chaves disponíveis no state: {list(state.keys())}")
                
                return result
            except Exception as e:
                safe_print(f"[INTERPRETER] [ERRO] Erro ao formatar resposta: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: resposta simples
                response = f"## Resultado da Tool: {tool_used}\n\n"
                if tool_result.get("success"):
                    data_count = len(tool_result.get("data", []))
                    response += f"Total de registros: {data_count}\n\nDados processados com sucesso."
                else:
                    response += f"Erro: {tool_result.get('error', 'Erro desconhecido')}"
                return {
                    "final_response": clean_response_text(response, max_emojis=2),
                    "visualization_data": None
                }
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Se não há tool_result e não há disambiguation, retornar mensagem
        safe_print(f"[INTERPRETER] Nenhuma tool disponível para processar a consulta")
        no_tool_msg = clean_response_text(no_tool_message, max_emojis=2)
        return {"final_response": no_tool_msg, "visualization_data": None}
        
    except Exception as e:
        safe_print(f"[INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao processar resultado\n\nOcorreu um erro ao formatar a resposta: {str(e)}"
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg, "visualization_data": None}

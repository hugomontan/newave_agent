"""Comparison Interpreter para Multi-Deck Agent DECOMP."""
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from decomp_agent.app.config import safe_print
from decomp_agent.app.agents.multi_deck.formatting.registry import format_comparison_response
from shared.utils.text_utils import clean_response_text

def comparison_interpreter_node(state: MultiDeckState) -> dict:
    tool_result = state.get("tool_result")
    tool_used = state.get("tool_used")
    execution_result = state.get("execution_result", {})
    query = state.get("query", "")
    deck_display_names = state.get("deck_display_names", {})
    
    if tool_result:
        # Usar formatter apropriado para formatar a resposta
        try:
            formatted = format_comparison_response(
                tool_result=tool_result,
                tool_used=tool_used or "UnknownTool",
                query=query,
                deck_display_names=deck_display_names
            )
            safe_print(f"[COMPARISON INTERPRETER] Formatted keys: {list(formatted.keys())}")
            safe_print(f"[COMPARISON INTERPRETER] Has comparison_data: {'comparison_data' in formatted}")
            safe_print(f"[COMPARISON INTERPRETER] Final response length: {len(formatted.get('final_response', ''))}")
            
            # format_comparison_response retorna {"final_response": ..., "comparison_data": formatted_dict}
            # onde formatted_dict é o resultado do formatter com comparison_table, chart_data, etc.
            comparison_data = formatted.get("comparison_data")
            if comparison_data:
                safe_print(f"[COMPARISON INTERPRETER] Comparison data keys: {list(comparison_data.keys()) if isinstance(comparison_data, dict) else 'not a dict'}")
            
            return {
                "final_response": clean_response_text(formatted.get("final_response", ""), max_emojis=2),
                "comparison_data": comparison_data
            }
        except Exception as e:
            safe_print(f"[COMPARISON INTERPRETER] Erro ao formatar resposta: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: formatação básica
            response = f"## Comparação Multi-Deck\n\nDados processados com sucesso.\n"
            return {
                "final_response": clean_response_text(response, max_emojis=2),
                "comparison_data": tool_result.get("comparison_data")
            }
    
    # Formatação básica de execução
    success = execution_result.get("success", False)
    stdout = execution_result.get("stdout", "")
    stderr = execution_result.get("stderr", "")
    
    if success:
        response = f"## Resultado da Comparação\n\n{stdout}"
    else:
        response = f"## Erro na Execução\n\n{stderr}"
    
    return {
        "final_response": clean_response_text(response, max_emojis=2),
        "comparison_data": None
    }

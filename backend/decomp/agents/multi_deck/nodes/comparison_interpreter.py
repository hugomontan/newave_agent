"""Comparison Interpreter para Multi-Deck Agent DECOMP."""
from backend.decomp.agents.multi_deck.state import MultiDeckState
from backend.decomp.config import safe_print
from backend.decomp.agents.multi_deck.formatting.registry import format_comparison_response
from backend.core.utils.text_utils import clean_response_text

def comparison_interpreter_node(state: MultiDeckState) -> dict:
    """
    Node que formata os resultados de comparação e gera a resposta final.
    
    Prioridades:
    1. Se tool_result existe: formata resultado da tool usando formatters
    2. Caso contrário: retorna mensagem informando que não há tool disponível
    """
    tool_result = state.get("tool_result")
    tool_used = state.get("tool_used")
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
    
    # Se não há tool_result, retornar mensagem genérica
    safe_print(f"[COMPARISON INTERPRETER DECOMP] Nenhuma tool disponível para processar a consulta de comparação")
    no_tool_msg = """## Não foi encontrado sentido semântico entre o pedido e os dados disponíveis

Não foi possível identificar uma correspondência semântica entre sua consulta e os dados disponíveis no sistema.

Por favor, reformule sua pergunta ou consulte a documentação para ver os tipos de dados que podem ser consultados."""
    no_tool_msg = clean_response_text(no_tool_msg, max_emojis=2)
    return {"final_response": no_tool_msg, "comparison_data": None}

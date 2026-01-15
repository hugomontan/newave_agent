"""Comparison Interpreter para Multi-Deck Agent DECOMP."""
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from decomp_agent.app.config import safe_print
from shared.utils.text_utils import clean_response_text

def comparison_interpreter_node(state: MultiDeckState) -> dict:
    tool_result = state.get("tool_result")
    execution_result = state.get("execution_result", {})
    query = state.get("query", "")
    
    if tool_result:
        # Formatação básica de tool result (formatters serão adicionados depois)
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

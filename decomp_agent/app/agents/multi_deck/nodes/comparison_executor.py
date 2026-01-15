"""Comparison Executor para Multi-Deck Agent DECOMP."""
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from shared.utils.code_executor import execute_python_code
from decomp_agent.app.config import CODE_EXECUTION_TIMEOUT

def comparison_executor_node(state: MultiDeckState) -> dict:
    code = state.get("generated_code", "")
    deck_paths = state.get("deck_paths", {})
    
    if not code or not deck_paths:
        return {
            "execution_result": {"success": False, "stdout": "", "stderr": "Código ou decks não especificados", "return_code": -1},
            "error": "Código ou decks não especificados"
        }
    
    # Usar o primeiro deck como base para execução
    first_deck_path = list(deck_paths.values())[0]
    result = execute_python_code(code, first_deck_path, timeout=CODE_EXECUTION_TIMEOUT)
    
    return {
        "execution_result": result,
        "error": result.get("stderr") if not result.get("success") else None
    }

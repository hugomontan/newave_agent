"""
Node que executa o código Python gerado.
Para Single Deck Agent.
"""
from app.agents.single_deck.state import SingleDeckState
from app.utils.code_executor import execute_python_code


def executor_node(state: SingleDeckState) -> dict:
    """
    Node que executa o código Python gerado.
    
    Args:
        state: Estado do Single Deck Agent
        
    Returns:
        Dict com execution_result e error
    """
    code = state.get("generated_code", "")
    deck_path = state.get("deck_path", "")
    
    if not code:
        return {
            "execution_result": {
                "success": False,
                "stdout": "",
                "stderr": "Nenhum código foi gerado",
                "return_code": -1
            },
            "error": "Nenhum código foi gerado"
        }
    
    if not deck_path:
        return {
            "execution_result": {
                "success": False,
                "stdout": "",
                "stderr": "Caminho do deck não especificado",
                "return_code": -1
            },
            "error": "Caminho do deck não especificado"
        }
    
    result = execute_python_code(code, deck_path)
    
    error = None
    if not result["success"]:
        error = result["stderr"] or "Erro desconhecido na execução"
    
    return {
        "execution_result": result,
        "error": error
    }

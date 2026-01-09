"""
Node que executa o código Python gerado para comparação multi-deck.
Para Multi-Deck Agent.
"""
from app.agents.multi_deck.state import MultiDeckState
from app.utils.code_executor import execute_python_code


def comparison_executor_node(state: MultiDeckState) -> dict:
    """
    Node que executa o código Python gerado para comparação.
    
    Args:
        state: Estado do Multi-Deck Agent
        
    Returns:
        Dict com execution_result e error
    """
    code = state.get("generated_code", "")
    deck_path = state.get("deck_path", "")
    deck_december_path = state.get("deck_december_path", "")
    deck_january_path = state.get("deck_january_path", "")
    
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
    
    # Para comparação, o código pode usar deck_december_path e deck_january_path
    # O executor precisa garantir que esses caminhos estejam disponíveis no ambiente
    # Por enquanto, usamos deck_path como base (o código gerado deve usar os caminhos corretos)
    result = execute_python_code(code, deck_path)
    
    error = None
    if not result["success"]:
        error = result["stderr"] or "Erro desconhecido na execução"
    
    return {
        "execution_result": result,
        "error": error
    }

"""
Node genérico que executa o código Python gerado.
Para Single Deck Agent (NEWAVE e DECOMP).
"""
from typing import Dict, Any, Optional
from backend.core.code_executor import execute_python_code
from backend.core.config import safe_print, CODE_EXECUTION_TIMEOUT


def executor_node(
    state: Dict[str, Any],
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Node genérico que executa o código Python gerado.
    
    Args:
        state: Estado do Single Deck Agent
        timeout: Timeout em segundos (None usa o padrão de CODE_EXECUTION_TIMEOUT)
        
    Returns:
        Dict com execution_result e error
    """
    code = state.get("generated_code", "")
    deck_path = state.get("deck_path", "")
    
    if not code:
        safe_print("[EXECUTOR] Nenhum código para executar")
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
        safe_print("[EXECUTOR] Caminho do deck não especificado")
        return {
            "execution_result": {
                "success": False,
                "stdout": "",
                "stderr": "Caminho do deck não especificado",
                "return_code": -1
            },
            "error": "Caminho do deck não especificado"
        }
    
    # Usar timeout fornecido ou o padrão
    exec_timeout = timeout if timeout is not None else CODE_EXECUTION_TIMEOUT
    
    safe_print(f"[EXECUTOR] Executando código (timeout: {exec_timeout}s)...")
    
    result = execute_python_code(code, deck_path, timeout=exec_timeout)
    
    error = None
    if not result["success"]:
        error = result["stderr"] or "Erro desconhecido na execução"
        safe_print(f"[EXECUTOR] Erro: {error}")
    else:
        safe_print("[EXECUTOR] Código executado com sucesso")
    
    return {
        "execution_result": result,
        "error": error
    }

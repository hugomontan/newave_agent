"""
Executor de código Python compartilhado entre NEWAVE e DECOMP.
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path


ALLOWED_IMPORTS = {
    "inewave",
    "idecomp",
    "pandas", 
    "numpy",
    "datetime",
    "os",
    "pathlib",
}


def validate_code(code: str) -> tuple[bool, str]:
    """
    Valida se o código é seguro para execução.
    Retorna (is_valid, error_message).
    """
    dangerous_patterns = [
        "subprocess",
        "os.system",
        "exec(",
        "eval(",
        "__import__",
        "open(",
        "requests",
        "urllib",
        "socket",
        "shutil.rmtree",
        "os.remove",
        "os.unlink",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in code:
            return False, f"Código contém padrão não permitido: {pattern}"
    
    return True, ""


def execute_python_code(code: str, deck_path: str, timeout: int = 30) -> dict:
    """
    Executa código Python em um subprocess isolado.
    
    Args:
        code: Código Python a ser executado
        deck_path: Caminho do deck
        timeout: Timeout em segundos (padrão: 30)
        
    Returns:
        dict com stdout, stderr e return_code
    """
    is_valid, error_msg = validate_code(code)
    if not is_valid:
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "return_code": -1
        }
    
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=deck_path,
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).parent.parent.parent),
            }
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execução excedeu o timeout de {timeout} segundos",
            "return_code": -2
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -3
        }
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

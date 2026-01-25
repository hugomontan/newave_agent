"""
Utilitário para execução segura de código Python com timeout.
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
from backend.core.config import safe_print


def execute_python_code(
    code: str,
    deck_path: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Executa código Python de forma segura com timeout.
    
    Args:
        code: Código Python a ser executado
        deck_path: Caminho do diretório do deck (usado como working directory)
        timeout: Timeout em segundos (padrão: 30)
        
    Returns:
        Dict com:
        - success: bool - Se a execução foi bem-sucedida
        - stdout: str - Saída padrão
        - stderr: str - Erro padrão
        - return_code: int - Código de retorno
    """
    # Criar arquivo temporário com o código
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Converter deck_path para Path se necessário
        working_dir = Path(deck_path) if deck_path else None
        
        # Executar código com subprocess
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(working_dir) if working_dir and working_dir.exists() else None,
            encoding='utf-8',
            errors='replace'
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        safe_print(f"[CODE EXECUTOR] Timeout após {timeout}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout: código não terminou em {timeout} segundos",
            "return_code": -1
        }
    except Exception as e:
        safe_print(f"[CODE EXECUTOR] Erro ao executar código: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }
    finally:
        # Limpar arquivo temporário
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except Exception:
            pass

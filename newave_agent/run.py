"""
Script para iniciar o servidor da API NEWAVE Agent.

Uso:
    python run.py

O servidor será iniciado em http://localhost:8000
Documentacao da API em http://localhost:8000/docs
"""
import sys
import os
import builtins

# ======================================
# CONFIGURACAO DE ENCODING PARA WINDOWS
# Deve ser executado ANTES de qualquer outro import
# Resolve: OSError: [Errno 22] Invalid argument
# ======================================

# Forcar encoding UTF-8 no Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Patch global do print para Windows (antes de importar uvicorn)
_original_print = builtins.print

def _safe_print(*args, **kwargs):
    """Print seguro que substitui caracteres problematicos no Windows."""
    try:
        _original_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        # Fallback: converter para ASCII com substituicao
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(str(arg).encode('ascii', errors='replace').decode('ascii'))
        try:
            _original_print(*safe_args, **kwargs)
        except Exception:
            pass  # Silenciosamente ignora

if sys.platform == 'win32':
    builtins.print = _safe_print

# ======================================
# Imports originais
# ======================================

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


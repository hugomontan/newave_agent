"""
Script para iniciar o servidor da API NW Multi Agent (NEWAVE + DECOMP).

Uso:
    python run.py

O servidor será iniciado em http://localhost:8000
Documentação da API em http://localhost:8000/docs
"""
import sys
import os
import builtins

# ======================================
# CONFIGURAÇÃO DE ENCODING PARA WINDOWS
# Deve ser executado ANTES de qualquer outro import
# Resolve: OSError: [Errno 22] Invalid argument
# ======================================

# Forçar encoding UTF-8 no Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Desativa buffer do stdout no worker (subprocesso do uvicorn --reload).
    # Sem isso, prints do PRELOAD / tool_router / etc. não aparecem no terminal.
    os.environ['PYTHONUNBUFFERED'] = '1'

# Patch global do print para Windows (antes de importar uvicorn)
_original_print = builtins.print

def _safe_print(*args, **kwargs):
    """Print seguro que substitui caracteres problemáticos no Windows."""
    try:
        # Forçar flush para garantir que aparece no terminal
        kwargs.setdefault('flush', True)
        _original_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        # Fallback: converter para ASCII com substituição
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(str(arg).encode('ascii', errors='replace').decode('ascii'))
        try:
            kwargs.setdefault('flush', True)
            _original_print(*safe_args, **kwargs)
        except Exception:
            pass  # Silenciosamente ignora

if sys.platform == 'win32':
    builtins.print = _safe_print

# Garantir que stdout e stderr não estão sendo redirecionados
if sys.platform == 'win32':
    # Forçar stdout e stderr para o terminal
    if not sys.stdout.isatty():
        sys.stdout = sys.__stdout__
    if not sys.stderr.isatty():
        sys.stderr = sys.__stderr__

# ======================================
# Imports originais
# ======================================

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

"""
Configurações compartilhadas entre newave_agent e decomp_agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env na raiz do projeto
# Tentar encontrar o .env na raiz do projeto (nw_multi)
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback: tentar carregar do diretório atual
    load_dotenv()

# ======================================
# BASE PATHS
# ======================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # nw_multi/
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = ROOT_DIR / "uploads"

# ======================================
# SAFE PRINT PARA WINDOWS
# Usado em módulos que podem ser importados antes do main.py
# ======================================

# Mapeamento de emojis para texto ASCII seguro
_EMOJI_TO_ASCII = {
    '✅': '[OK]',
    '❌': '[ERRO]',
    '⚠️': '[AVISO]',
    '❗': '[AVISO]',
    '❓': '[?]',
    '🔍': '[BUSCA]',
    '📚': '[DOCS]',
    '📖': '[DOC]',
    '📈': '[GRAF]',
    '📋': '[LISTA]',
    '🔧': '[TOOL]',
    '💻': '[CODE]',
    '⚡': '[EXEC]',
    '🧠': '[AI]',
    '🔄': '[RETRY]',
    '🎉': '[SUCESSO]',
    '🏭': '[USINA]',
    '→': '->',
    '←': '<-',
    '↔': '<->',
    '└': ' ',
    '─': '-',
    '├': ' ',
    '│': '|',
}

def safe_print(*args, **kwargs):
    """
    Print seguro que substitui caracteres problemáticos no Windows.
    Evita erros de encoding (OSError: [Errno 22] Invalid argument).
    Sempre força flush=True para garantir que aparece no terminal imediatamente.
    
    Uso:
        from backend.core.config import safe_print
        safe_print("Mensagem com emoji ✅")  # Funciona no Windows
    """
    # Sempre forçar flush para garantir que aparece no terminal
    kwargs.setdefault('flush', True)
    
    try:
        # Primeira tentativa: substituir emojis conhecidos
        safe_args = []
        for arg in args:
            s = str(arg)
            for emoji, ascii_text in _EMOJI_TO_ASCII.items():
                s = s.replace(emoji, ascii_text)
            safe_args.append(s)
        print(*safe_args, **kwargs)
    except (UnicodeEncodeError, OSError):
        # Fallback: converter para ASCII com substituição
        try:
            safe_args = []
            for arg in args:
                s = str(arg)
                # Remover todos os caracteres não-ASCII
                s = s.encode('ascii', errors='replace').decode('ascii')
                safe_args.append(s)
            print(*safe_args, **kwargs)
        except Exception:
            pass  # Silenciosamente ignora se ainda falhar

# Debug mode - controla se prints de debug são exibidos
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def debug_print(*args, **kwargs):
    """
    Print condicional para debug. Só imprime se DEBUG_MODE=True.
    
    Uso:
        from backend.core.config import debug_print
        debug_print("[TOOL] Mensagem de debug")  # Só imprime se DEBUG_MODE=true
    """
    if DEBUG_MODE:
        safe_print(*args, **kwargs)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# RAG settings
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "2000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Executor settings
CODE_EXECUTION_TIMEOUT = int(os.getenv("CODE_EXECUTION_TIMEOUT", "30"))

# Semantic tool matching settings
SEMANTIC_MATCHING_ENABLED = os.getenv("SEMANTIC_MATCHING_ENABLED", "true").lower() == "true"
SEMANTIC_MATCH_THRESHOLD = float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.55"))  # Threshold para ranking (não usado para decisão final)
SEMANTIC_MATCH_MIN_SCORE = float(os.getenv("SEMANTIC_MATCH_MIN_SCORE", "0.4"))  # Score mínimo para executar tool (>= 0.4 sempre executa)
USE_HYBRID_MATCHING = os.getenv("USE_HYBRID_MATCHING", "true").lower() == "true"
QUERY_EXPANSION_ENABLED = os.getenv("QUERY_EXPANSION_ENABLED", "true").lower() == "true"

# Disambiguation settings (baseado em análise empírica de 70 queries)
DISAMBIGUATION_SCORE_DIFF_THRESHOLD = float(os.getenv("DISAMBIGUATION_SCORE_DIFF_THRESHOLD", "0.1"))  # Diferença mediana observada: 0.0931
DISAMBIGUATION_MAX_OPTIONS = int(os.getenv("DISAMBIGUATION_MAX_OPTIONS", "3"))  # Maioria dos conflitos envolve 2-3 tools
DISAMBIGUATION_MIN_SCORE = float(os.getenv("DISAMBIGUATION_MIN_SCORE", "0.4"))  # Score mínimo atual do sistema

# Langfuse (Observability)
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
# Suporta tanto LANGFUSE_BASE_URL quanto LANGFUSE_HOST
LANGFUSE_HOST = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://us.cloud.langfuse.com"

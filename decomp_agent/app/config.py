"""
Configurações do DECOMP Agent.
"""
import os
import sys
import builtins
from pathlib import Path
from dotenv import load_dotenv

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
    
    Uso:
        from app.config import safe_print
        safe_print("Mensagem com emoji ✅")  # Funciona no Windows
    """
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

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis de ambiente do arquivo .env na raiz de decomp_agent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
UPLOADS_DIR = BASE_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma" / "decomp"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

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
SEMANTIC_MATCH_THRESHOLD = float(os.getenv("SEMANTIC_MATCH_THRESHOLD", "0.55"))
SEMANTIC_MATCH_MIN_SCORE = float(os.getenv("SEMANTIC_MATCH_MIN_SCORE", "0.4"))
USE_HYBRID_MATCHING = os.getenv("USE_HYBRID_MATCHING", "true").lower() == "true"
QUERY_EXPANSION_ENABLED = os.getenv("QUERY_EXPANSION_ENABLED", "true").lower() == "true"

# Disambiguation settings
DISAMBIGUATION_SCORE_DIFF_THRESHOLD = float(os.getenv("DISAMBIGUATION_SCORE_DIFF_THRESHOLD", "0.1"))
DISAMBIGUATION_MAX_OPTIONS = int(os.getenv("DISAMBIGUATION_MAX_OPTIONS", "3"))
DISAMBIGUATION_MIN_SCORE = float(os.getenv("DISAMBIGUATION_MIN_SCORE", "0.4"))

# Langfuse (Observability)
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://us.cloud.langfuse.com"

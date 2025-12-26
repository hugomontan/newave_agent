import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "docs"
UPLOADS_DIR = BASE_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

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


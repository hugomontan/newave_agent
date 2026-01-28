"""
Configurações específicas do DESSEM Agent.
"""
from pathlib import Path

from backend.core.config import *  # noqa: F401,F403
from backend.core.config import DATA_DIR


# Diretórios base de dados para o DESSEM
DESSEM_DATA_DIR = DATA_DIR / "dessem"
DESSEM_DECKS_DIR = DESSEM_DATA_DIR / "decks"
DESSEM_DOCS_DIR = DESSEM_DATA_DIR / "docs"
DESSEM_CHROMA_DIR = DESSEM_DATA_DIR / "chroma"

# Diretório compartilhado de uploads (mesmo padrão de newave/decomp)
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


# Garantir que os diretórios existam
for _dir in [UPLOADS_DIR, DESSEM_DATA_DIR, DESSEM_DECKS_DIR, DESSEM_DOCS_DIR, DESSEM_CHROMA_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


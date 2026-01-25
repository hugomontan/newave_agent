"""
Configurações específicas do DECOMP Agent.
"""
from pathlib import Path
from dotenv import load_dotenv
from backend.core.config import *

# Base paths
from backend.core.config import DATA_DIR

DECOMP_DATA_DIR = DATA_DIR / "decomp"
DECOMP_DECKS_DIR = DECOMP_DATA_DIR / "decks"
DECOMP_DOCS_DIR = DECOMP_DATA_DIR / "docs"
DECOMP_CHROMA_DIR = DECOMP_DATA_DIR / "chroma"
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DECOMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
DECOMP_DECKS_DIR.mkdir(parents=True, exist_ok=True)
DECOMP_DOCS_DIR.mkdir(parents=True, exist_ok=True)
DECOMP_CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Todas as configurações compartilhadas são importadas de shared.config via "from backend.core.config import *"
# Apenas configurações específicas do DECOMP permanecem aqui

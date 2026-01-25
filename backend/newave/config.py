"""
Configurações específicas do NEWAVE Agent.
"""
from pathlib import Path
from dotenv import load_dotenv
from backend.core.config import *

# Base paths
from backend.core.config import DATA_DIR

NEWAVE_DATA_DIR = DATA_DIR / "newave"
NEWAVE_DECKS_DIR = NEWAVE_DATA_DIR / "decks"
NEWAVE_DOCS_DIR = NEWAVE_DATA_DIR / "docs"
NEWAVE_CHROMA_DIR = NEWAVE_DATA_DIR / "chroma"
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
NEWAVE_DATA_DIR.mkdir(parents=True, exist_ok=True)
NEWAVE_DECKS_DIR.mkdir(parents=True, exist_ok=True)
NEWAVE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
NEWAVE_CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Todas as configurações compartilhadas são importadas de shared.config via "from backend.core.config import *"
# Apenas configurações específicas do NEWAVE permanecem aqui


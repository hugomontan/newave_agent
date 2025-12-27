"""
Utilitário para carregar e extrair decks da pasta decks/.
"""
import zipfile
from pathlib import Path
from app.config import BASE_DIR

DECKS_DIR = BASE_DIR / "decks"
DECK_DECEMBER = "NW202512"
DECK_JANUARY = "NW202601"

def load_deck(deck_name: str) -> Path:
    """
    Extrai e retorna caminho do deck.
    
    Args:
        deck_name: Nome do deck (ex: "NW202512")
        
    Returns:
        Path do diretório extraído
    """
    zip_path = DECKS_DIR / f"{deck_name}.zip"
    extract_path = DECKS_DIR / deck_name
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Deck {deck_name}.zip não encontrado em {DECKS_DIR}")
    
    # Extrair se ainda não foi extraído
    if not extract_path.exists():
        extract_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Se extraiu em uma subpasta, mover arquivos para o nível superior
        extracted_items = list(extract_path.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            inner_dir = extracted_items[0]
            for item in inner_dir.iterdir():
                import shutil
                shutil.move(str(item), str(extract_path / item.name))
            inner_dir.rmdir()
    
    return extract_path

def get_december_deck_path() -> Path:
    """Retorna caminho do deck de dezembro."""
    return load_deck(DECK_DECEMBER)

def get_january_deck_path() -> Path:
    """Retorna caminho do deck de janeiro."""
    return load_deck(DECK_JANUARY)


"""
Utilitário para carregar e extrair decks DECOMP da pasta decks/.
Suporta descoberta dinâmica de N decks.
"""
import zipfile
import re
from pathlib import Path
from typing import List, Dict, Optional, TypedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from decomp_agent.app.config import BASE_DIR

DECKS_DIR = BASE_DIR / "decks"

# Mapeamento de mês para nome em português
MONTH_NAMES = {
    "01": "Janeiro",
    "02": "Fevereiro", 
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro"
}


class DeckInfo(TypedDict):
    """Informações de um deck DECOMP disponível."""
    name: str  # Nome do deck (ex: "DC202501")
    display_name: str  # Nome amigável (ex: "Janeiro 2025")
    year: int  # Ano (ex: 2025)
    month: int  # Mês (ex: 1)
    zip_path: str  # Caminho do arquivo .zip
    extracted_path: Optional[str]  # Caminho extraído (se já extraído)


def parse_deck_name(deck_name: str) -> Optional[Dict[str, any]]:
    """
    Extrai período do nome do deck DECOMP.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501" ou "DECOMP202501")
        
    Returns:
        Dict com year, month, display_name ou None se inválido
    """
    # Tentar padrão DC{YYYY}{MM}
    match = re.match(r'^DC(\d{4})(\d{2})$', deck_name)
    if not match:
        # Tentar padrão DECOMP{YYYY}{MM}
        match = re.match(r'^DECOMP(\d{4})(\d{2})$', deck_name)
    
    if not match:
        return None
    
    year = int(match.group(1))
    month_str = match.group(2)
    month = int(month_str)
    
    if month < 1 or month > 12:
        return None
    
    month_name = MONTH_NAMES.get(month_str, f"Mês {month}")
    display_name = f"{month_name} {year}"
    
    return {
        "year": year,
        "month": month,
        "display_name": display_name
    }


def is_decomp_deck(deck_path: Path) -> bool:
    """
    Verifica se um diretório contém um deck DECOMP válido.
    
    Args:
        deck_path: Caminho do diretório do deck
        
    Returns:
        True se contém dadger.rvx (arquivo principal DECOMP)
    """
    if not deck_path.is_dir():
        return False
    
    # Verificar se contém dadger.rvx (arquivo principal DECOMP)
    dadger_file = deck_path / "dadger.rvx"
    return dadger_file.exists()


def list_available_decks() -> List[DeckInfo]:
    """
    Escaneia a pasta decks/ e lista todos os decks DECOMP disponíveis.
    
    Returns:
        Lista de DeckInfo ordenada cronologicamente (mais antigo primeiro)
    """
    decks: List[DeckInfo] = []
    
    if not DECKS_DIR.exists():
        return decks
    
    # Buscar todos os arquivos .zip que seguem o padrão DC{YYYY}{MM} ou DECOMP{YYYY}{MM}
    for zip_file in DECKS_DIR.glob("DC*.zip"):
        deck_name = zip_file.stem  # Remove extensão .zip
        parsed = parse_deck_name(deck_name)
        
        if parsed is None:
            continue
        
        # Verificar se já foi extraído
        extracted_path = DECKS_DIR / deck_name
        
        deck_info: DeckInfo = {
            "name": deck_name,
            "display_name": parsed["display_name"],
            "year": parsed["year"],
            "month": parsed["month"],
            "zip_path": str(zip_file),
            "extracted_path": str(extracted_path) if extracted_path.exists() else None
        }
        decks.append(deck_info)
    
    # Também buscar padrão DECOMP{YYYY}{MM}.zip
    for zip_file in DECKS_DIR.glob("DECOMP*.zip"):
        deck_name = zip_file.stem
        parsed = parse_deck_name(deck_name)
        
        if parsed is None:
            continue
        
        extracted_path = DECKS_DIR / deck_name
        
        deck_info: DeckInfo = {
            "name": deck_name,
            "display_name": parsed["display_name"],
            "year": parsed["year"],
            "month": parsed["month"],
            "zip_path": str(zip_file),
            "extracted_path": str(extracted_path) if extracted_path.exists() else None
        }
        decks.append(deck_info)
    
    # Ordenar cronologicamente (mais antigo primeiro)
    decks.sort(key=lambda d: (d["year"], d["month"]))
    
    return decks


def get_deck_by_name(deck_name: str) -> Optional[DeckInfo]:
    """
    Busca informações de um deck específico pelo nome.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501")
        
    Returns:
        DeckInfo ou None se não encontrado
    """
    decks = list_available_decks()
    for deck in decks:
        if deck["name"] == deck_name:
            return deck
    return None


def load_deck(deck_name: str) -> Path:
    """
    Extrai e retorna caminho do deck DECOMP.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501")
        
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
    
    # Verificar se é um deck DECOMP válido
    if not is_decomp_deck(extract_path):
        raise ValueError(f"Deck {deck_name} não contém dadger.rvx (não é um deck DECOMP válido)")
    
    return extract_path


def load_multiple_decks(deck_names: List[str], max_workers: int = 4) -> Dict[str, Path]:
    """
    Carrega múltiplos decks DECOMP em paralelo.
    
    Args:
        deck_names: Lista de nomes dos decks a carregar
        max_workers: Número máximo de workers paralelos
        
    Returns:
        Dict mapeando nome do deck para seu Path extraído
    """
    results: Dict[str, Path] = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_deck = {
            executor.submit(load_deck, name): name 
            for name in deck_names
        }
        
        for future in as_completed(future_to_deck):
            deck_name = future_to_deck[future]
            try:
                path = future.result()
                results[deck_name] = path
            except Exception as e:
                print(f"Erro ao carregar deck {deck_name}: {e}")
                raise
    
    return results


def get_deck_path(deck_name: str) -> Path:
    """
    Retorna o caminho de um deck, carregando-o se necessário.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501")
        
    Returns:
        Path do diretório do deck
    """
    return load_deck(deck_name)


def get_deck_display_name(deck_name: str) -> str:
    """
    Retorna o nome amigável de um deck.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501")
        
    Returns:
        Nome amigável (ex: "Janeiro 2025")
    """
    parsed = parse_deck_name(deck_name)
    if parsed:
        return parsed["display_name"]
    return deck_name


def get_deck_paths_dict(deck_names: List[str]) -> Dict[str, str]:
    """
    Retorna um dicionário com os caminhos de múltiplos decks.
    
    Args:
        deck_names: Lista de nomes dos decks
        
    Returns:
        Dict mapeando nome do deck para seu caminho (string)
    """
    paths = load_multiple_decks(deck_names)
    return {name: str(path) for name, path in paths.items()}


def get_deck_display_names_dict(deck_names: List[str]) -> Dict[str, str]:
    """
    Retorna um dicionário com os nomes amigáveis de múltiplos decks.
    
    Args:
        deck_names: Lista de nomes dos decks
        
    Returns:
        Dict mapeando nome do deck para seu nome amigável
    """
    return {name: get_deck_display_name(name) for name in deck_names}

"""
Utilitário para carregar e extrair decks DESSEM da pasta de dados.

O padrão assumido de nomes de arquivos é:
- DS{YYYY}{MM}.zip, por exemplo: DS202501.zip

Esta implementação é propositalmente simples e segue o mesmo estilo
do `backend.newave.utils.deck_loader`, mas adaptada para o diretório
DESSEM.
"""

import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from backend.dessem.config import DESSEM_DECKS_DIR, DESSEM_DATA_DIR
from backend.core.config import ROOT_DIR


def _find_decks_dir() -> Path:
    """
    Encontra o diretório de decks DESSEM, procurando em vários locais possíveis.

    Ordem:
    1) data/dessem/decks
    2) data/dessem
    3) ROOT_DIR/decks (compatibilidade)
    """
    if DESSEM_DECKS_DIR.exists():
        zip_files = list(DESSEM_DECKS_DIR.glob("DS*.zip"))
        if zip_files:
            return DESSEM_DECKS_DIR

        nested = DESSEM_DECKS_DIR / "decks"
        if nested.exists() and nested.is_dir():
            nested_zips = list(nested.glob("DS*.zip"))
            if nested_zips:
                return nested
        return DESSEM_DECKS_DIR

    if DESSEM_DATA_DIR.exists() and DESSEM_DATA_DIR.is_dir():
        zip_files = list(DESSEM_DATA_DIR.glob("DS*.zip"))
        if zip_files:
            return DESSEM_DATA_DIR

    fallback_locations = [
        ROOT_DIR / "decks",
        Path(__file__).resolve().parent.parent.parent.parent / "decks",
    ]
    for location in fallback_locations:
        if location.exists() and location.is_dir():
            return location

    return DESSEM_DECKS_DIR


DECKS_DIR = _find_decks_dir()


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
    "12": "Dezembro",
}


class DeckInfo(TypedDict):
    """Informações de um deck DESSEM disponível."""

    name: str
    display_name: str
    year: int
    month: int
    zip_path: str
    extracted_path: Optional[str]


def parse_deck_name(deck_name: str) -> Optional[Dict[str, object]]:
    """
    Extrai ano, mês e nome amigável do deck DESSEM.
    Espera padrão DS{YYYY}{MM}, ex: DS202501.
    """
    match = re.match(r"^DS(\d{4})(\d{2})$", deck_name)
    if not match:
        return None

    year = int(match.group(1))
    month_str = match.group(2)
    month = int(month_str)

    if month < 1 or month > 12:
        return None

    month_name = MONTH_NAMES.get(month_str, f"Mês {month}")
    display_name = f"{month_name} {year}"

    return {"year": year, "month": month, "display_name": display_name}


def list_available_decks() -> List[DeckInfo]:
    """
    Lista todos os decks DESSEM disponíveis.

    Procura por arquivos DS{YYYY}{MM}.zip no diretório de decks.
    """
    decks: List[DeckInfo] = []
    decks_dir = _find_decks_dir()

    if not decks_dir.exists():
        return decks

    zip_files = list(decks_dir.glob("DS*.zip"))
    for zip_file in zip_files:
        deck_name = zip_file.stem
        parsed = parse_deck_name(deck_name)
        if parsed is None:
            continue

        extracted_path = decks_dir / deck_name
        info: DeckInfo = {
            "name": deck_name,
            "display_name": parsed["display_name"],
            "year": parsed["year"],
            "month": parsed["month"],
            "zip_path": str(zip_file),
            "extracted_path": str(extracted_path) if extracted_path.exists() else None,
        }
        decks.append(info)

    decks.sort(key=lambda d: (d["year"], d["month"]))
    return decks


def get_deck_by_name(deck_name: str) -> Optional[DeckInfo]:
    """Retorna informações de um deck DESSEM específico, se existir."""
    for deck in list_available_decks():
        if deck["name"] == deck_name:
            return deck
    return None


def load_deck(deck_name: str) -> Path:
    """
    Extrai e retorna o caminho do deck DESSEM.

    Args:
        deck_name: Nome do deck, ex: DS202501
    """
    decks_dir = _find_decks_dir()
    zip_path = decks_dir / f"{deck_name}.zip"
    extract_path = decks_dir / deck_name

    if not zip_path.exists():
        raise FileNotFoundError(f"Deck {deck_name}.zip não encontrado em {decks_dir}")

    if not extract_path.exists():
        extract_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # Se extraiu em subpasta única, promover conteúdo
        extracted_items = list(extract_path.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            inner_dir = extracted_items[0]
            for item in inner_dir.iterdir():
                import shutil

                shutil.move(str(item), str(extract_path / item.name))
            inner_dir.rmdir()

    return extract_path


def load_multiple_decks(deck_names: List[str], max_workers: int = 4) -> Dict[str, Path]:
    """Carrega múltiplos decks DESSEM em paralelo."""
    results: Dict[str, Path] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_deck = {executor.submit(load_deck, name): name for name in deck_names}
        for future in as_completed(future_to_deck):
            name = future_to_deck[future]
            path = future.result()
            results[name] = path

    return results


def get_deck_path(deck_name: str) -> Path:
    """Retorna o caminho extraído de um deck DESSEM, carregando se necessário."""
    return load_deck(deck_name)


def get_deck_display_name(deck_name: str) -> str:
    """Nome amigável (mês/ano) para um deck DESSEM."""
    parsed = parse_deck_name(deck_name)
    if parsed:
        return parsed["display_name"]  # type: ignore[no-any-return]
    return deck_name


def get_deck_paths_dict(deck_names: List[str]) -> Dict[str, str]:
    """Dicionário nome → caminho para vários decks DESSEM."""
    paths = load_multiple_decks(deck_names)
    return {name: str(path) for name, path in paths.items()}


def get_deck_display_names_dict(deck_names: List[str]) -> Dict[str, str]:
    """Dicionário nome → nome amigável para vários decks DESSEM."""
    return {name: get_deck_display_name(name) for name in deck_names}


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
    name: str  # Nome do deck (ex: "DC202501-sem1")
    display_name: str  # Nome amigável (ex: "Janeiro 2025 - Semana 1")
    year: int  # Ano (ex: 2025)
    month: int  # Mês (ex: 1)
    week: Optional[int]  # Semana (ex: 1, 2, 3, 4, 5) ou None se não semanal
    zip_path: str  # Caminho do arquivo .zip
    extracted_path: Optional[str]  # Caminho extraído (se já extraído)


def parse_deck_name(deck_name: str) -> Optional[Dict[str, any]]:
    """
    Extrai período do nome do deck DECOMP.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501", "DC202501-sem1", "DECOMP202501")
        
    Returns:
        Dict com year, month, week (opcional), display_name ou None se inválido
    """
    # Tentar padrão DC{YYYY}{MM}-sem{N}
    match = re.match(r'^DC(\d{4})(\d{2})-sem(\d+)$', deck_name)
    week = None
    if match:
        year = int(match.group(1))
        month_str = match.group(2)
        month = int(month_str)
        week = int(match.group(3))
    else:
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
    
    if week is not None:
        display_name = f"{month_name} {year} - Semana {week}"
    else:
        display_name = f"{month_name} {year}"
    
    result = {
        "year": year,
        "month": month,
        "display_name": display_name
    }
    
    if week is not None:
        result["week"] = week
    
    return result


def is_decomp_deck(deck_path: Path) -> bool:
    """
    Verifica se um diretório contém um deck DECOMP válido.
    
    Args:
        deck_path: Caminho do diretório do deck
        
    Returns:
        True se contém dadger.rvx, dadger.rv0 ou dadger.rv2 (arquivo principal DECOMP)
    """
    if not deck_path.is_dir():
        return False
    
    # Verificar se contém dadger.rvx, dadger.rv0 ou dadger.rv2 (arquivo principal DECOMP)
    # Alguns decks usam .rvx, outros .rv0, outros .rv2
    dadger_rvx = deck_path / "dadger.rvx"
    dadger_rv0 = deck_path / "dadger.rv0"
    dadger_rv2 = deck_path / "dadger.rv2"
    return dadger_rvx.exists() or dadger_rv0.exists() or dadger_rv2.exists()


def find_first_semestre_zip(month_dir: Path) -> Optional[Path]:
    """
    Encontra o primeiro arquivo ZIP de semestre disponível em uma pasta de mês.
    
    Args:
        month_dir: Caminho da pasta do mês (ex: decks/DC202504/)
        
    Returns:
        Path do primeiro ZIP encontrado (sem1, sem2, etc.) ou None
    """
    # Buscar por ordem: sem1, sem2, sem3, sem4, sem5
    for sem_num in range(1, 6):
        zip_file = month_dir / f"{month_dir.name}-sem{sem_num}.zip"
        if zip_file.exists():
            return zip_file
    return None


def list_available_decks() -> List[DeckInfo]:
    """
    Escaneia a pasta decks/ e lista todos os decks DECOMP disponíveis.
    
    Estrutura esperada:
    - decks/DC{YYYY}{MM}/DC{YYYY}{MM}-sem{N}.zip (sem1, sem2, sem3, sem4, sem5)
    
    Returns:
        Lista de DeckInfo ordenada cronologicamente (mais antigo primeiro, depois por semana)
    """
    decks: List[DeckInfo] = []
    
    if not DECKS_DIR.exists():
        return decks
    
    # Buscar pastas DC{YYYY}{MM}/ dentro de decks/
    for month_dir in DECKS_DIR.iterdir():
        if not month_dir.is_dir():
            continue
        
        # Ignorar pastas de extração
        if month_dir.name.endswith("_extracted"):
            continue
        
        # Verificar se o nome da pasta segue o padrão DC{YYYY}{MM}
        month_name = month_dir.name
        month_parsed = parse_deck_name(month_name)
        
        if month_parsed is None:
            continue
        
        # Buscar TODOS os decks semanais dentro da pasta
        for sem_num in range(1, 6):
            zip_file = month_dir / f"{month_name}-sem{sem_num}.zip"
            if zip_file.exists():
                deck_name = f"{month_name}-sem{sem_num}"
                parsed = parse_deck_name(deck_name)
                
                if parsed is None:
                    continue
                
                # O caminho extraído deve incluir a semana no nome
                extracted_path = DECKS_DIR / f"{deck_name}_extracted"
                
                deck_info: DeckInfo = {
                    "name": deck_name,
                    "display_name": parsed["display_name"],
                    "year": parsed["year"],
                    "month": parsed["month"],
                    "week": parsed.get("week"),
                    "zip_path": str(zip_file),
                    "extracted_path": str(extracted_path) if extracted_path.exists() else None
                }
                decks.append(deck_info)
        
        # Se não encontrou nenhum ZIP semanal, tentar ZIP direto na pasta (compatibilidade)
        zip_file = month_dir / f"{month_name}.zip"
        if zip_file.exists():
            parsed = parse_deck_name(month_name)
            if parsed is not None:
                extracted_path = DECKS_DIR / f"{month_name}_extracted"
                
                deck_info: DeckInfo = {
                    "name": month_name,
                    "display_name": parsed["display_name"],
                    "year": parsed["year"],
                    "month": parsed["month"],
                    "week": parsed.get("week"),
                    "zip_path": str(zip_file),
                    "extracted_path": str(extracted_path) if extracted_path.exists() else None
                }
                decks.append(deck_info)
    
    # Também buscar ZIPs diretos na raiz de decks/ (compatibilidade)
    for zip_file in DECKS_DIR.glob("DC*.zip"):
        deck_name = zip_file.stem
        parsed = parse_deck_name(deck_name)
        
        if parsed is None:
            continue
        
        # Ignorar se já está em uma pasta (evitar duplicatas)
        if any(d["name"] == deck_name for d in decks):
            continue
        
        extracted_path = DECKS_DIR / f"{deck_name}_extracted"
        
        deck_info: DeckInfo = {
            "name": deck_name,
            "display_name": parsed["display_name"],
            "year": parsed["year"],
            "month": parsed["month"],
            "week": parsed.get("week"),
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
        
        extracted_path = DECKS_DIR / f"{deck_name}_extracted"
        
        deck_info: DeckInfo = {
            "name": deck_name,
            "display_name": parsed["display_name"],
            "year": parsed["year"],
            "month": parsed["month"],
            "week": parsed.get("week"),
            "zip_path": str(zip_file),
            "extracted_path": str(extracted_path) if extracted_path.exists() else None
        }
        decks.append(deck_info)
    
    # Remover duplicatas
    seen = set()
    unique_decks = []
    for deck in decks:
        if deck["name"] not in seen:
            seen.add(deck["name"])
            unique_decks.append(deck)
    
    # Ordenar cronologicamente (mais antigo primeiro, depois por semana)
    unique_decks.sort(key=lambda d: (d["year"], d["month"], d.get("week") or 0))
    
    return unique_decks


def get_deck_by_name(deck_name: str) -> Optional[DeckInfo]:
    """
    Busca informações de um deck específico pelo nome.
    
    Args:
        deck_name: Nome do deck (ex: "DC202501-sem1" ou "DC202501")
        
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
    
    Estrutura esperada:
    - decks/DC{YYYY}{MM}/DC{YYYY}{MM}-sem{N}.zip
    
    Args:
        deck_name: Nome do deck (ex: "DC202501-sem1" ou "DC202501")
        
    Returns:
        Path do diretório extraído
    """
    import shutil
    
    zip_path = None
    
    # Verificar se o nome contém semana (ex: DC202501-sem1)
    if "-sem" in deck_name:
        # Extrair o nome do mês (DC202501) e o número da semana (1)
        parts = deck_name.split("-sem")
        if len(parts) == 2:
            month_name = parts[0]
            week_num = parts[1]
            month_dir = DECKS_DIR / month_name
            if month_dir.exists() and month_dir.is_dir():
                zip_path = month_dir / f"{month_name}-sem{week_num}.zip"
    
    # Se não encontrou, tentar como pasta do mês
    if zip_path is None or not zip_path.exists():
        month_dir = DECKS_DIR / deck_name
        if month_dir.exists() and month_dir.is_dir():
            # Tentar encontrar primeiro semestre disponível
            zip_path = find_first_semestre_zip(month_dir)
            if zip_path:
                # Atualizar deck_name para incluir a semana encontrada
                deck_name = f"{deck_name}-sem{zip_path.stem.split('-sem')[1]}"
    
    # Se ainda não encontrou, tentar ZIP direto na raiz
    if zip_path is None or not zip_path.exists():
        zip_path = DECKS_DIR / f"{deck_name}.zip"
    
    # Se ainda não encontrou, tentar dentro da subpasta com todos os semestres possíveis
    if not zip_path.exists():
        parts = deck_name.split("-sem")
        if len(parts) == 1:
            month_name = parts[0]
            month_dir = DECKS_DIR / month_name
            if month_dir.exists():
                # Tentar todos os semestres possíveis
                for sem_num in range(1, 6):
                    potential_zip = month_dir / f"{month_name}-sem{sem_num}.zip"
                    if potential_zip.exists():
                        zip_path = potential_zip
                        deck_name = f"{month_name}-sem{sem_num}"
                        break
    
    if not zip_path or not zip_path.exists():
        raise FileNotFoundError(
            f"Deck {deck_name} não encontrado. "
            f"Procurado em: {DECKS_DIR / deck_name} e {DECKS_DIR / f'{deck_name}.zip'}"
        )
    
    # O diretório de extração deve incluir a semana no nome para evitar conflitos
    extract_path = DECKS_DIR / f"{deck_name}_extracted"
    
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
                shutil.move(str(item), str(extract_path / item.name))
            inner_dir.rmdir()
    
    # Verificar se é um deck DECOMP válido
    if not is_decomp_deck(extract_path):
        raise ValueError(f"Deck {deck_name} não contém dadger.rvx, dadger.rv0 ou dadger.rv2 (não é um deck DECOMP válido)")
    
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

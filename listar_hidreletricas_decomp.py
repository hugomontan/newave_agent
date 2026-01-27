"""
Lista todas as usinas hidrelétricas do sistema consideradas no modelo DECOMP (Bloco UH).

Uso:
    python listar_hidreletricas_decomp.py [--deck NOME] [--output ARQUIVO]

Exemplos:
    python listar_hidreletricas_decomp.py
    python listar_hidreletricas_decomp.py --deck DC202501-sem1
    python listar_hidreletricas_decomp.py --output hidreletricas_decomp.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Garantir que o projeto está no path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from backend.decomp.utils.dadger_cache import get_cached_dadger
from backend.decomp.utils.deck_loader import (
    list_available_decks,
    get_deck_path,
)
from backend.core.config import safe_print, DATA_DIR


def _mapear_nomes_hidr(deck_path: str, codigos_usinas: set) -> dict[int, str]:
    """Busca nomes no HIDR.DAT para os códigos do bloco UH."""
    mapeamento: dict[int, str] = {}
    deck = Path(deck_path)

    hidr_paths = [
        deck / "hidr.dat",
        deck / "HIDR.DAT",
    ]
    newave = DATA_DIR / "newave" / "decks"
    if newave.exists():
        try:
            dirs = [d for d in newave.iterdir() if d.is_dir()]
            dirs.sort(key=lambda d: d.name, reverse=True)
            for d in dirs[:3]:
                hidr_paths.extend([d / "HIDR.DAT", d / "hidr.dat"])
        except Exception:
            pass

    for hidr_path in hidr_paths:
        if not hidr_path.exists():
            continue
        try:
            from inewave.newave import Hidr

            hidr = Hidr.read(str(hidr_path))
            if hidr.cadastro is None or hidr.cadastro.empty:
                continue
            for idx, row in hidr.cadastro.iterrows():
                cod = None
                if isinstance(idx, (int, float)) and idx > 0:
                    try:
                        cod = int(idx)
                    except (ValueError, TypeError):
                        pass
                if cod is None:
                    for col in [
                        "codigo_usina",
                        "codigo",
                        "codigo_usina_hidr",
                        "numero_usina",
                        "numero",
                    ]:
                        if col in row.index and pd.notna(row[col]):
                            try:
                                cod = int(row[col])
                                break
                            except (ValueError, TypeError):
                                continue
                nome = None
                for col in ["nome_usina", "nome", "nome_da_usina", "usina", "nome_do_posto"]:
                    if col in row.index and pd.notna(row[col]):
                        v = str(row[col]).strip()
                        if v and v not in ("nan", "", "none"):
                            nome = v
                            break
                if cod and cod > 0 and nome and cod in codigos_usinas:
                    mapeamento[cod] = nome
            if mapeamento:
                break
        except Exception:
            continue

    return mapeamento


def listar_hidreletricas(deck_path: str) -> pd.DataFrame:
    """
    Obtém todas as usinas hidrelétricas do Bloco UH do deck.

    Args:
        deck_path: Caminho do diretório do deck DECOMP

    Returns:
        DataFrame com colunas: codigo, nome_decomp
    """
    dadger = get_cached_dadger(deck_path)
    if dadger is None:
        return pd.DataFrame()

    uh_df = dadger.uh(df=True)
    codigos: set[int] = set()
    if uh_df is not None and not (isinstance(uh_df, pd.DataFrame) and uh_df.empty):
        if "codigo_usina" in uh_df.columns:
            codigos = set(uh_df["codigo_usina"].dropna().astype(int).unique())

    if not codigos:
        return pd.DataFrame()

    mapeamento = _mapear_nomes_hidr(deck_path, codigos)
    rows = []
    for c in sorted(codigos):
        nome = mapeamento.get(c, f"Usina {c}")
        rows.append({"codigo": c, "nome_decomp": nome})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Lista todas as usinas hidrelétricas do DECOMP (Bloco UH)."
    )
    ap.add_argument(
        "--deck",
        type=str,
        default=None,
        help="Nome do deck (ex: DC202501-sem1). Se omitido, usa o primeiro disponível.",
    )
    ap.add_argument(
        "--output",
        type=str,
        default=None,
        help="Arquivo CSV de saída. Padrão: hidreletricas_decomp.csv na raiz do projeto.",
    )
    args = ap.parse_args()

    decks = list_available_decks()
    if not decks:
        safe_print("[HIDRELETRICAS] Nenhum deck DECOMP encontrado.")
        sys.exit(1)

    if args.deck:
        match = [d for d in decks if d["name"] == args.deck]
        if not match:
            safe_print(f"[HIDRELETRICAS] Deck '{args.deck}' nao encontrado.")
            sys.exit(1)
        deck_info = match[0]
    else:
        deck_info = decks[0]

    deck_path = get_deck_path(deck_info["name"])
    if deck_path is None:
        safe_print("[HIDRELETRICAS] Nao foi possivel carregar o deck.")
        sys.exit(1)

    safe_print(f"[HIDRELETRICAS] Deck: {deck_info['name']}")
    df = listar_hidreletricas(str(deck_path))
    if df.empty:
        safe_print("[HIDRELETRICAS] Nenhuma usina hidrelétrica encontrada no Bloco UH.")
        sys.exit(1)

    out_path = Path(args.output) if args.output else ROOT / "hidreletricas_decomp.csv"
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")

    safe_print(f"[HIDRELETRICAS] {len(df)} usinas hidrelétricas listadas.")
    safe_print(f"[HIDRELETRICAS] Salvo em: {out_path}")


if __name__ == "__main__":
    main()

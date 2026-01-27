"""
Lista todas as usinas térmicas do sistema consideradas no modelo DECOMP (Bloco CT).

Uso:
    python listar_termicas_decomp.py [--deck NOME] [--output ARQUIVO]

Exemplos:
    python listar_termicas_decomp.py
    python listar_termicas_decomp.py --deck DC202501-sem1
    python listar_termicas_decomp.py --output termicas_decomp.csv
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
from backend.core.config import safe_print


def listar_termicas(deck_path: str) -> pd.DataFrame:
    """
    Obtém todas as usinas térmicas do Bloco CT do deck.

    Args:
        deck_path: Caminho do diretório do deck DECOMP

    Returns:
        DataFrame com colunas: codigo, nome_decomp, submercado
    """
    dadger = get_cached_dadger(deck_path)
    if dadger is None:
        return pd.DataFrame()

    ct_df = dadger.ct(estagio=1, df=True)
    if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
        return pd.DataFrame()

    cols = ["codigo_usina", "nome_usina"]
    if "codigo_submercado" in ct_df.columns:
        cols.append("codigo_submercado")
    available = [c for c in cols if c in ct_df.columns]
    if "codigo_usina" not in available or "nome_usina" not in available:
        return pd.DataFrame()

    df = ct_df[available].drop_duplicates()
    df = df.dropna(subset=["nome_usina"])
    df = df[
        (df["nome_usina"].astype(str).str.strip() != "")
        & (df["nome_usina"].astype(str).str.lower() != "nan")
    ]

    out = df.rename(columns={"codigo_usina": "codigo", "nome_usina": "nome_decomp"})
    if "codigo_submercado" in out.columns:
        out = out.rename(columns={"codigo_submercado": "submercado"})
    return out.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Lista todas as usinas térmicas do DECOMP (Bloco CT)."
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
        help="Arquivo CSV de saída. Padrão: termicas_decomp.csv na raiz do projeto.",
    )
    args = ap.parse_args()

    decks = list_available_decks()
    if not decks:
        safe_print("[TERMICAS] Nenhum deck DECOMP encontrado.")
        sys.exit(1)

    if args.deck:
        match = [d for d in decks if d["name"] == args.deck]
        if not match:
            safe_print(f"[TERMICAS] Deck '{args.deck}' nao encontrado.")
            sys.exit(1)
        deck_info = match[0]
    else:
        deck_info = decks[-1]

    deck_path = get_deck_path(deck_info["name"])
    if deck_path is None:
        safe_print("[TERMICAS] Nao foi possivel carregar o deck.")
        sys.exit(1)

    safe_print(f"[TERMICAS] Deck: {deck_info['name']}")
    df = listar_termicas(str(deck_path))
    if df.empty:
        safe_print("[TERMICAS] Nenhuma usina termelétrica encontrada no Bloco CT.")
        sys.exit(1)

    out_path = Path(args.output) if args.output else ROOT / "termicas_decomp.csv"
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")

    safe_print(f"[TERMICAS] {len(df)} usinas termelétricas listadas.")
    safe_print(f"[TERMICAS] Salvo em: {out_path}")


if __name__ == "__main__":
    main()

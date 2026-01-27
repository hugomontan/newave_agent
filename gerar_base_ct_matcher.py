"""
Gera o CSV base do thermal matcher (Bloco CT): códigos e nomes do deck,
com nome_completo vazio para você preencher.

Esse CSV é a base para o DecompThermalPlantMatcher das tools térmicas do DECOMP.
Saída: backend/decomp/data/deparatermicas_decomp.csv

Uso:
    python gerar_base_ct_matcher.py [--deck NOME] [--output ARQUIVO]

Exemplos:
    python gerar_base_ct_matcher.py
    python gerar_base_ct_matcher.py --deck DC202601-sem3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from backend.decomp.utils.dadger_cache import get_cached_dadger
from backend.decomp.utils.deck_loader import list_available_decks, get_deck_path
from backend.core.config import safe_print

# Destino padrão: base do thermal matcher DECOMP
DEFAULT_OUTPUT = ROOT / "backend" / "decomp" / "data" / "deparatermicas_decomp.csv"


def listar_ct(deck_path: str) -> pd.DataFrame:
    """Extrai codigo + nome_usina do Bloco CT (estágio 1)."""
    dadger = get_cached_dadger(deck_path)
    if dadger is None:
        return pd.DataFrame()

    ct_df = dadger.ct(estagio=1, df=True)
    if ct_df is None or (isinstance(ct_df, pd.DataFrame) and ct_df.empty):
        return pd.DataFrame()

    if "codigo_usina" not in ct_df.columns or "nome_usina" not in ct_df.columns:
        return pd.DataFrame()

    df = ct_df[["codigo_usina", "nome_usina"]].drop_duplicates()
    df = df.dropna(subset=["nome_usina"])
    df = df[
        (df["nome_usina"].astype(str).str.strip() != "")
        & (df["nome_usina"].astype(str).str.lower() != "nan")
    ]
    return df.rename(columns={"codigo_usina": "codigo", "nome_usina": "nome_decomp"}).reset_index(
        drop=True
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Gera CSV base do thermal matcher (CT): codigo, nome_decomp, nome_completo (vazio para preencher)."
    )
    ap.add_argument(
        "--deck",
        type=str,
        default=None,
        help="Deck (ex: DC202601-sem3). Se omitido, usa o mais recente.",
    )
    ap.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"CSV de saída. Padrão: {DEFAULT_OUTPUT.relative_to(ROOT)}",
    )
    args = ap.parse_args()

    decks = list_available_decks()
    if not decks:
        safe_print("[BASE CT] Nenhum deck DECOMP encontrado.")
        sys.exit(1)

    if args.deck:
        match = [d for d in decks if d["name"] == args.deck]
        if not match:
            safe_print(f"[BASE CT] Deck '{args.deck}' nao encontrado.")
            sys.exit(1)
        deck_info = match[0]
    else:
        deck_info = decks[-1]

    deck_path = get_deck_path(deck_info["name"])
    if deck_path is None:
        safe_print("[BASE CT] Nao foi possivel carregar o deck.")
        sys.exit(1)

    safe_print(f"[BASE CT] Deck: {deck_info['name']}")
    df = listar_ct(str(deck_path))
    if df.empty:
        safe_print("[BASE CT] Nenhuma usina no Bloco CT.")
        sys.exit(1)

    df["nome_completo"] = ""
    df["arquivo_fonte"] = "CT"
    df = df[["codigo", "nome_decomp", "nome_completo", "arquivo_fonte"]]

    out_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")

    safe_print(f"[BASE CT] {len(df)} usinas escritas em: {out_path}")
    safe_print("[BASE CT] Preencha a coluna 'nome_completo' e use este arquivo como base do thermal matcher (DECOMP).")


if __name__ == "__main__":
    main()

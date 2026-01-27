"""
Teste do Bloco CT (DECOMP) usando o mapa base de térmicas do NEWAVE.

Usa o matcher DECOMP com CSV no formato NEWAVE (deparatermicas / thermal_plants_reference)
como fonte de aliases. Os códigos continuam vindo do deck (Bloco CT).

Uso:
    python -m tests.test_ct_newave_map
    python tests/test_ct_newave_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Mapa base NEWAVE: raiz do projeto (deparatermicas ou thermal_plants_reference)
NEWAVE_THERMAL_MAP_CANDIDATES = [
    ROOT / "deparatermicas.csv",
    ROOT / "thermal_plants_reference.csv",
]


def _find_newave_map() -> Path | None:
    for p in NEWAVE_THERMAL_MAP_CANDIDATES:
        if p.exists():
            return p
    return None


def _load_ct_data(deck_path: str):
    import pandas as pd
    from backend.decomp.utils.dadger_cache import get_cached_dadger

    dadger = get_cached_dadger(deck_path)
    if dadger is None:
        return None
    ct = dadger.ct(estagio=1, df=True)
    if ct is None or (isinstance(ct, pd.DataFrame) and ct.empty):
        return None
    df = ct[["codigo_usina", "nome_usina"]].drop_duplicates()
    df = df.dropna(subset=["nome_usina"])
    return [{"codigo_usina": r["codigo_usina"], "nome_usina": r["nome_usina"]} for _, r in df.iterrows()]


def run():
    from backend.decomp.utils.deck_loader import list_available_decks, get_deck_path
    from backend.decomp.utils.thermal_plant_matcher import DecompThermalPlantMatcher

    map_path = _find_newave_map()
    if not map_path:
        print("[TEST CT NEWAVE MAP] Erro: nenhum mapa base NEWAVE encontrado.")
        print(f"  Procurado: {[str(p) for p in NEWAVE_THERMAL_MAP_CANDIDATES]}")
        return 1

    decks = list_available_decks()
    if not decks:
        print("[TEST CT NEWAVE MAP] Erro: nenhum deck DECOMP encontrado.")
        return 1

    deck_info = decks[-1]
    deck_path = get_deck_path(deck_info["name"])
    if deck_path is None:
        print("[TEST CT NEWAVE MAP] Erro: nao foi possivel carregar o deck.")
        return 1

    data = _load_ct_data(str(deck_path))
    if not data:
        print("[TEST CT NEWAVE MAP] Erro: Bloco CT vazio ou indisponivel.")
        return 1

    matcher = DecompThermalPlantMatcher(csv_path=str(map_path))

    queries = [
        "qual o cvu de gna ii",
        "qual o cvu de cubatao",
        "cvu angra 1",
        "cvu termorio",
    ]
    results = []
    for q in queries:
        code = matcher.extract_plant_from_query(q, data, "usina", 0.5)
        names = {d["codigo_usina"]: d["nome_usina"] for d in data}
        nome = names.get(code, "?") if code is not None else "?"
        results.append((q, code, nome))
        print(f"  {q!r} -> codigo={code}, nome={nome}")

    ok = sum(1 for _, c, _ in results if c is not None)
    print(f"\n[TEST CT NEWAVE MAP] Deck: {deck_info['name']}")
    print(f"[TEST CT NEWAVE MAP] Mapa: {map_path.name}")
    print(f"[TEST CT NEWAVE MAP] Queries: {ok}/{len(queries)} com usina identificada")
    return 0 if ok == len(queries) else 1


if __name__ == "__main__":
    sys.exit(run())

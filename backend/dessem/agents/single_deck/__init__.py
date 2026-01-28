"""
Re-exports do Single Deck Agent DESSEM.

O grafo principal está em `backend.dessem.agent`, este módulo
existe apenas para manter a mesma estrutura de pastas de NEWAVE/DECOMP.
"""

from backend.dessem.agent import (
    create_single_deck_agent,
    get_single_deck_agent,
    run_query,
    run_query_stream,
)

__all__ = [
    "create_single_deck_agent",
    "get_single_deck_agent",
    "run_query",
    "run_query_stream",
]


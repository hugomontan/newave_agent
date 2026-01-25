"""
Re-exports do Single Deck Agent DECOMP.
O código principal está em backend.decomp.agent
"""
from backend.decomp.agent import (
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

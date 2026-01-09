"""
Multi-Deck Agent - Agent especializado para comparações entre decks.
"""

from .graph import (
    create_multi_deck_agent,
    get_multi_deck_agent,
    run_query,
    run_query_stream,
)
from .state import MultiDeckState
from .agent import MultiDeckAgent

__all__ = [
    "create_multi_deck_agent",
    "get_multi_deck_agent",
    "run_query",
    "run_query_stream",
    "MultiDeckState",
    "MultiDeckAgent",
]


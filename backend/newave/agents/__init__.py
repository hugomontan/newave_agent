"""
Agents module - Modularizado em single_deck e multi_deck.
"""

# Exportar apenas os estados dos novos módulos
from backend.newave.state import SingleDeckState
from backend.newave.agents.multi_deck.state import MultiDeckState

__all__ = [
    "SingleDeckState",
    "MultiDeckState",
]

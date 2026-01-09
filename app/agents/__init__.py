"""
Agents module - Modularizado em single_deck e multi_deck.
"""

# Exportar apenas os estados dos novos módulos
from app.agents.single_deck.state import SingleDeckState
from app.agents.multi_deck.state import MultiDeckState

__all__ = [
    "SingleDeckState",
    "MultiDeckState",
]

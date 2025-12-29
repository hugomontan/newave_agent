"""
Módulo de formatadores especializados para comparação multi-deck.
Cada tool tem seu próprio formatador que gera visualizações otimizadas.
"""
from app.comparison.registry import get_formatter_for_tool

__all__ = ['get_formatter_for_tool']


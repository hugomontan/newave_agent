"""
Módulos de visualização separados e modulares para formatters do single deck.
Cada visualização é um módulo independente que pode ser reutilizado.
"""

from .volume_inicial_visualization import create_volume_inicial_visualization

__all__ = [
    "create_volume_inicial_visualization",
]

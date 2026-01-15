"""
Módulo de formatação para comparações multi-deck.
Estrutura reorganizada para melhor separação de responsabilidades.

Estrutura:
- base.py: Interface base ComparisonFormatter
- registry.py: Registry de formatadores e função format_comparison_response consolidada
- data_formatters/: Formatadores que geram estruturas de dados (tabelas, gráficos)
- text_formatters/: Formatadores que geram texto markdown (simple, llm_structured, llm_free)
"""

from .base import ComparisonFormatter
from .registry import get_formatter_for_tool, format_comparison_response

__all__ = [
    "ComparisonFormatter",
    "get_formatter_for_tool",
    "format_comparison_response",
]

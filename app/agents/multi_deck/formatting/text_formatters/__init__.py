"""
Formatadores de texto para comparações multi-deck.
Geram texto markdown a partir de estruturas de dados formatadas.
"""

from .simple import (
    format_clast_simple_comparison,
    format_carga_simple_comparison,
    format_limites_intercambio_simple_comparison,
    format_gtmin_simple_comparison,
    format_volumes_iniciais_simple_comparison,
    generate_fallback_comparison_response,
)
from .llm_structured import format_with_llm_structured
from .llm_free import format_with_llm_free

__all__ = [
    "format_clast_simple_comparison",
    "format_carga_simple_comparison",
    "format_limites_intercambio_simple_comparison",
    "format_gtmin_simple_comparison",
    "format_volumes_iniciais_simple_comparison",
    "generate_fallback_comparison_response",
    "format_with_llm_structured",
    "format_with_llm_free",
]

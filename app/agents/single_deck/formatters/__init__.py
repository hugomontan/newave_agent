"""
Formatters para single deck.
"""

from .base import SingleDeckFormatter
from .generic_formatter import GenericSingleDeckFormatter
# Formatters agora estão em data_formatters/ (modularização completa)
from .data_formatters import (
    ClastSingleDeckFormatter,
    CargaMensalSingleDeckFormatter,
    CadicSingleDeckFormatter,
    VazoesSingleDeckFormatter,
    DsvaguaSingleDeckFormatter,
    LimitesIntercambioSingleDeckFormatter,
    CadastroHidrSingleDeckFormatter,
    CadastroTermSingleDeckFormatter,
    ConfhdSingleDeckFormatter,
    UsinasNaoSimuladasSingleDeckFormatter,
    ModifOperacaoSingleDeckFormatter,
)

__all__ = [
    "SingleDeckFormatter",
    "GenericSingleDeckFormatter",
    "ClastSingleDeckFormatter",
    "CargaMensalSingleDeckFormatter",
    "CadicSingleDeckFormatter",
    "VazoesSingleDeckFormatter",
    "DsvaguaSingleDeckFormatter",
    "LimitesIntercambioSingleDeckFormatter",
    "CadastroHidrSingleDeckFormatter",
    "CadastroTermSingleDeckFormatter",
    "ConfhdSingleDeckFormatter",
    "UsinasNaoSimuladasSingleDeckFormatter",
    "ModifOperacaoSingleDeckFormatter",
]

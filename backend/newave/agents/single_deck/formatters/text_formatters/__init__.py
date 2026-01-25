"""
Text formatters para single deck.
Funções simples de formatação de texto sem uso de LLM.
"""

from .simple import (
    format_clast_simple,
    format_carga_mensal_simple,
    format_cadic_simple,
    format_vazoes_simple,
    format_dsvagua_simple,
    format_limites_intercambio_simple,
    format_cadastro_hidr_simple,
    format_cadastro_term_simple,
    format_confhd_simple,
    format_usinas_nao_simuladas_simple,
    format_modif_operacao_simple,
    format_restricao_eletrica_simple,
)

__all__ = [
    "format_clast_simple",
    "format_carga_mensal_simple",
    "format_cadic_simple",
    "format_vazoes_simple",
    "format_dsvagua_simple",
    "format_limites_intercambio_simple",
    "format_cadastro_hidr_simple",
    "format_cadastro_term_simple",
    "format_confhd_simple",
    "format_usinas_nao_simuladas_simple",
    "format_modif_operacao_simple",
    "format_restricao_eletrica_simple",
]

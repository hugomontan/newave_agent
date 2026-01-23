"""
Registry de formatters para single deck.
Atribui formatter baseado na tool executada usando can_format() e get_priority().
"""

import os
import json as json_module
from typing import Dict, Any, Optional
from newave_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from newave_agent.app.tools.base import NEWAVETool

# Formatters específicos do single deck (modularização completa - 1 por tool)
from newave_agent.app.agents.single_deck.formatters.data_formatters import (
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
    RestricaoEletricaSingleDeckFormatter,
)

# Formatter genérico (fallback)
from newave_agent.app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
from shared.utils.debug import write_debug_log

# Lista de formatters ordenada por prioridade (maior primeiro)
SINGLE_DECK_FORMATTERS = [
    ClastSingleDeckFormatter(),
    CargaMensalSingleDeckFormatter(),
    CadicSingleDeckFormatter(),
    VazoesSingleDeckFormatter(),
    DsvaguaSingleDeckFormatter(),
    LimitesIntercambioSingleDeckFormatter(),
    CadastroHidrSingleDeckFormatter(),
    CadastroTermSingleDeckFormatter(),
    UsinasNaoSimuladasSingleDeckFormatter(),
    ModifOperacaoSingleDeckFormatter(),
    RestricaoEletricaSingleDeckFormatter(),
    ConfhdSingleDeckFormatter(),
]

def get_formatter_for_tool(
    tool: NEWAVETool,
    tool_result: Dict[str, Any]
) -> SingleDeckFormatter:
    """
    Retorna formatter apropriado para uma tool no modo single deck.
    
    Estratégia:
    1. Tenta obter formatter da própria tool (get_single_deck_formatter())
    2. Se não houver, usa can_format() e get_priority() para selecionar o melhor formatter
    3. Se não encontrar, usa formatter genérico
    
    Args:
        tool: Instância da tool executada
        tool_result: Resultado da execução (pode conter formatter)
        
    Returns:
        Formatter apropriado
    """
    from newave_agent.app.config import safe_print
    
    tool_name = tool.get_name()
    
    # Prioridade 1: Formatter retornado pela tool no resultado
    if "formatter_single_deck" in tool_result:
        formatter = tool_result["formatter_single_deck"]
        if formatter is not None:
            safe_print(f"[SINGLE DECK REGISTRY] Formatter obtido do resultado da tool")
            return formatter
    
    # Prioridade 2: Formatter obtido via método da tool (se existir)
    if hasattr(tool, 'get_single_deck_formatter'):
        try:
            formatter = tool.get_single_deck_formatter()
            if formatter is not None:
                safe_print(f"[SINGLE DECK REGISTRY] Formatter obtido via método da tool")
                return formatter
        except Exception as e:
            safe_print(f"[SINGLE DECK REGISTRY] Erro ao obter formatter da tool: {e}")
    
    # Prioridade 3: Usar can_format() e get_priority() para selecionar o melhor formatter
    # Ordenar formatters por prioridade (maior primeiro)
    sorted_formatters = sorted(
        SINGLE_DECK_FORMATTERS,
        key=lambda f: f.get_priority(),
        reverse=True
    )
    
    for formatter in sorted_formatters:
        if formatter.can_format(tool_name, tool_result):
            safe_print(f"[SINGLE DECK REGISTRY] Formatter selecionado: {formatter.__class__.__name__} (prioridade: {formatter.get_priority()})")
            return formatter
    
    # Fallback: formatter genérico
    safe_print(f"[SINGLE DECK REGISTRY] Usando formatter genérico (fallback)")
    return GenericSingleDeckFormatter()

"""
Registry de formatters para single deck.
Atribui formatter baseado na tool executada.
"""

from typing import Dict, Any, Optional
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.tools.base import NEWAVETool

# Formatters específicos do single deck
from app.agents.single_deck.formatters.clast_formatter import ClastSingleDeckFormatter
from app.agents.single_deck.formatters.carga_formatter import CargaSingleDeckFormatter

# Formatter genérico (fallback)
from app.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter


def get_formatter_for_tool(
    tool: NEWAVETool,
    tool_result: Dict[str, Any]
) -> SingleDeckFormatter:
    """
    Retorna formatter apropriado para uma tool no modo single deck.
    
    Estratégia:
    1. Tenta obter formatter da própria tool (get_single_deck_formatter())
    2. Se não houver, tenta mapear pelo nome da tool
    3. Se não encontrar, usa formatter genérico
    
    Args:
        tool: Instância da tool executada
        tool_result: Resultado da execução (pode conter formatter)
        
    Returns:
        Formatter apropriado
    """
    from app.config import safe_print
    
    # Prioridade 1: Formatter retornado pela tool no resultado
    if "formatter_single_deck" in tool_result:
        formatter = tool_result["formatter_single_deck"]
        if formatter is not None:
            safe_print(f"[SINGLE DECK REGISTRY] Formatter obtido do resultado da tool")
            return formatter
    
    # Prioridade 2: Formatter obtido via método da tool
    formatter = tool.get_single_deck_formatter()
    if formatter is not None:
        safe_print(f"[SINGLE DECK REGISTRY] Formatter obtido via método da tool")
        return formatter
    
    # Prioridade 3: Mapeamento por nome da tool
    tool_name = tool.get_name()
    formatter_map = {
        "ClastValoresTool": ClastSingleDeckFormatter(),
        "CargaMensalTool": CargaSingleDeckFormatter(),
        # Adicionar outros mapeamentos conforme necessário
    }
    
    if tool_name in formatter_map:
        safe_print(f"[SINGLE DECK REGISTRY] Formatter mapeado por nome: {tool_name}")
        return formatter_map[tool_name]
    
    # Fallback: formatter genérico
    safe_print(f"[SINGLE DECK REGISTRY] Usando formatter genérico (fallback)")
    return GenericSingleDeckFormatter()

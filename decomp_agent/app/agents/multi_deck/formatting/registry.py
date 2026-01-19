"""
Registry de formatadores de comparação.
Mapeia tools para formatadores apropriados e fornece função consolidada para formatação.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List, Optional
from .base import ComparisonFormatter, DeckData


# Importar formatadores
from decomp_agent.app.agents.multi_deck.formatting.data_formatters import (
    UHComparisonFormatter,
    DisponibilidadeComparisonFormatter,
    InflexibilidadeComparisonFormatter,
    CVUComparisonFormatter,
    VolumeInicialComparisonFormatter,
)

# Lista de formatadores (em ordem de prioridade - mais específicos primeiro)
FORMATTERS: List[ComparisonFormatter] = [
    VolumeInicialComparisonFormatter(),  # Prioridade 95 - muito específico
    DisponibilidadeComparisonFormatter(),
    InflexibilidadeComparisonFormatter(),
    CVUComparisonFormatter(),
    UHComparisonFormatter(),  # Prioridade 10 - genérico, deve vir por último
]


def get_formatter_for_tool(
    tool_name: str, 
    result_structure: Dict[str, Any]
) -> ComparisonFormatter:
    """
    Retorna o formatador mais apropriado para uma tool específica.
    
    Args:
        tool_name: Nome da tool (ex: "UHUsinasHidrelétricasTool")
        result_structure: Estrutura do resultado da tool
        
    Returns:
        Formatador apropriado (ou formatter genérico como fallback)
    """
    candidates = [
        f for f in FORMATTERS 
        if f.can_format(tool_name, result_structure)
    ]
    
    if candidates:
        # Retornar o formatador com maior prioridade
        return max(candidates, key=lambda f: f.get_priority())
    
    # TODO: Criar LLMFreeFormatter como fallback
    # Por enquanto, retornar None e tratar no código chamador
    return None


def convert_legacy_result_to_decks_data(
    tool_result: Dict[str, Any],
    deck_display_names: Optional[Dict[str, str]] = None
) -> List[DeckData]:
    """
    Converte resultado legado (deck_1/deck_2) para formato List[DeckData].
    
    Args:
        tool_result: Resultado da tool (pode ter deck_1/deck_2 ou decks)
        deck_display_names: Mapeamento de nomes dos decks
        
    Returns:
        Lista de DeckData ordenados cronologicamente
    """
    decks_data = []
    
    # Verificar se há erro sem dados de decks
    if not tool_result.get("success", True) and "decks" not in tool_result:
        # Se há erro e não há decks, retornar lista vazia (será tratado no formatador)
        return []
    
    # Verificar formato novo (decks lista)
    if "decks" in tool_result:
        decks_list = tool_result["decks"]
        if not decks_list:  # Lista vazia
            return []
        for deck_info in decks_list:
            deck_name = deck_info.get("name", "")
            display_name = deck_display_names.get(deck_name, deck_name) if deck_display_names else deck_name
            result = deck_info.get("result", {})
            success = deck_info.get("success", True)
            error = deck_info.get("error")
            
            decks_data.append(DeckData(
                name=deck_name,
                display_name=display_name,
                result=result,
                success=success,
                error=error
            ))
    # Formato legado (deck_1/deck_2)
    elif "deck_1" in tool_result and "deck_2" in tool_result:
        deck1 = tool_result["deck_1"]
        deck2 = tool_result["deck_2"]
        
        name1 = deck1.get("name", "Deck 1")
        name2 = deck2.get("name", "Deck 2")
        display1 = deck_display_names.get(name1, name1) if deck_display_names else name1
        display2 = deck_display_names.get(name2, name2) if deck_display_names else name2
        
        decks_data.append(DeckData(
            name=name1,
            display_name=display1,
            result=deck1,
            success=deck1.get("success", True),
            error=deck1.get("error")
        ))
        decks_data.append(DeckData(
            name=name2,
            display_name=display2,
            result=deck2,
            success=deck2.get("success", True),
            error=deck2.get("error")
        ))
    
    return decks_data


def format_comparison_response(
    tool_result: Dict[str, Any], 
    tool_used: str, 
    query: str,
    deck_display_names: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Formata a resposta para o frontend quando é uma comparação multi-deck.
    
    Args:
        tool_result: Resultado da tool de comparação
        tool_used: Nome da tool usada
        query: Query original do usuário
        deck_display_names: Mapeamento de nomes dos decks
        
    Returns:
        Dict com final_response formatado e comparison_data
    """
    # Verificar se há erro explícito antes de converter
    if not tool_result.get("success", True) and "error" in tool_result:
        error_msg = tool_result.get("error", "Erro desconhecido")
        return {
            "final_response": f"## Erro na Comparação\n\n{error_msg}",
            "comparison_data": {
                "tool_name": tool_used,
                "query": query,
                "error": error_msg
            }
        }
    
    # Converter para formato de List[DeckData]
    decks_data = convert_legacy_result_to_decks_data(tool_result, deck_display_names)
    
    if not decks_data:
        # Verificar se há mensagem de erro no resultado original
        error_msg = tool_result.get("error", "Não foi possível obter dados de comparação.")
        return {
            "final_response": f"## Erro na Comparação\n\n{error_msg}",
            "comparison_data": {
                "tool_name": tool_used,
                "query": query,
                "error": error_msg
            }
        }
    
    # Obter formatter apropriado
    # Tentar usar tool_name do resultado se tool_used não estiver disponível ou não corresponder
    tool_name_to_use = tool_used
    if "tool_name" in tool_result:
        tool_name_to_use = tool_result.get("tool_name", tool_used)
    
    formatter = get_formatter_for_tool(tool_name_to_use, decks_data[0].result if decks_data else {})
    
    if formatter is None:
        # Fallback: formatação básica
        from decomp_agent.app.config import safe_print
        safe_print(f"[FORMATTER REGISTRY] Nenhum formatter encontrado para tool: {tool_name_to_use} (tool_used: {tool_used})")
        safe_print(f"[FORMATTER REGISTRY] Result structure keys: {list(decks_data[0].result.keys()) if decks_data else []}")
        return {
            "final_response": f"## Comparação Multi-Deck\n\n{len(decks_data)} decks comparados.",
            "comparison_data": tool_result
        }
    
    # Formatar usando o formatter
    formatted = formatter.format_multi_deck_comparison(decks_data, tool_used, query)
    
    return {
        "final_response": formatted.get("final_response", ""),
        "comparison_data": formatted
    }

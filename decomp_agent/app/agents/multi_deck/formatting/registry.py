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
    InflexibilidadeComparisonFormatter,
    CVUComparisonFormatter,
    VolumeInicialComparisonFormatter,
    DPComparisonFormatter,
    PQComparisonFormatter,
    CargaAndeComparisonFormatter,
    LimitesIntercambioComparisonFormatter,
    RestricoesEletricasComparisonFormatter,
    RestricoesVazaoHQComparisonFormatter,
    GLComparisonFormatter,
)

# Lista de formatadores (em ordem de prioridade - mais específicos primeiro)
# IMPORTANTE: Ordem importa quando há mesma prioridade - verificar tool_name primeiro
FORMATTERS: List[ComparisonFormatter] = [
    VolumeInicialComparisonFormatter(),  # Prioridade 95 - muito específico
    GLComparisonFormatter(),  # Prioridade 85 - específico para gerações GNL (GL) - ANTES de RestricoesVazaoHQ
    LimitesIntercambioComparisonFormatter(),  # Prioridade 85 - específico para limites de intercâmbio
    RestricoesEletricasComparisonFormatter(),  # Prioridade 85 - específico para restrições elétricas
    RestricoesVazaoHQComparisonFormatter(),  # Prioridade 85 - específico para restrições de vazão
    CargaAndeComparisonFormatter(),  # Prioridade 10 - específico para Carga ANDE
    DPComparisonFormatter(),  # Prioridade 10 - específico para DP
    PQComparisonFormatter(),  # Prioridade 10 - específico para PQ
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
    from decomp_agent.app.config import safe_print
    safe_print(f"[GET FORMATTER FOR TOOL] Buscando formatter para tool_name: {tool_name}")
    safe_print(f"[GET FORMATTER FOR TOOL] Total de formatters disponíveis: {len(FORMATTERS)}")
    
    candidates = []
    for formatter in FORMATTERS:
        can_format_result = formatter.can_format(tool_name, result_structure)
        safe_print(f"[GET FORMATTER FOR TOOL] {formatter.__class__.__name__}.can_format({tool_name}) = {can_format_result}")
        if can_format_result:
            candidates.append(formatter)
    
    safe_print(f"[GET FORMATTER FOR TOOL] Candidatos encontrados: {len(candidates)} - {[c.__class__.__name__ for c in candidates]}")
    
    if candidates:
        # Se houver múltiplos candidatos, priorizar:
        # 1. Maior prioridade
        # 2. Se empate, preferir o que corresponde ao tool_name (verificar primeiro na lista)
        max_priority = max(f.get_priority() for f in candidates)
        priority_candidates = [f for f in candidates if f.get_priority() == max_priority]
        
        safe_print(f"[GET FORMATTER FOR TOOL] Prioridade máxima: {max_priority}")
        safe_print(f"[GET FORMATTER FOR TOOL] Candidatos com prioridade máxima: {len(priority_candidates)} - {[c.__class__.__name__ for c in priority_candidates]}")
        
        # Se há empate de prioridade, verificar qual corresponde melhor ao tool_name
        if len(priority_candidates) > 1:
            tool_name_lower = tool_name.lower() if tool_name else ""
            safe_print(f"[GET FORMATTER FOR TOOL] Múltiplos candidatos com mesma prioridade, verificando match por nome...")
            # Verificar se algum candidato corresponde explicitamente ao tool_name
            for candidate in priority_candidates:
                candidate_name = candidate.__class__.__name__.lower()
                # GLComparisonFormatter para GL tools
                if "glcomparison" in candidate_name and ("gl" in tool_name_lower or "gnl" in tool_name_lower):
                    safe_print(f"[GET FORMATTER FOR TOOL] ✅ Selecionado {candidate.__class__.__name__} por match GL/GNL")
                    return candidate
                # RestricoesVazaoHQComparisonFormatter para vazao tools
                if "vazao" in candidate_name and ("vazao" in tool_name_lower or "hq" in tool_name_lower):
                    safe_print(f"[GET FORMATTER FOR TOOL] ✅ Selecionado {candidate.__class__.__name__} por match vazao/HQ")
                    return candidate
        
        # Retornar o primeiro candidato com maior prioridade (ordem na lista importa)
        selected = priority_candidates[0]
        safe_print(f"[GET FORMATTER FOR TOOL] ✅ Selecionado {selected.__class__.__name__} (primeiro com prioridade máxima)")
        return selected
    
    # TODO: Criar LLMFreeFormatter como fallback
    # Por enquanto, retornar None e tratar no código chamador
    safe_print(f"[GET FORMATTER FOR TOOL] ❌ Nenhum formatter encontrado para {tool_name}")
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
    from decomp_agent.app.config import safe_print
    
    tool_name_to_use = tool_used
    if "tool_name" in tool_result:
        tool_name_from_result = tool_result.get("tool_name", tool_used)
        safe_print(f"[FORMATTER REGISTRY] tool_name encontrado no resultado: {tool_name_from_result}")
        tool_name_to_use = tool_name_from_result
    
    # Preparar result_structure para can_format
    # Pode ser o resultado de um deck individual OU a estrutura completa do tool_result
    result_structure_for_check = {}
    if decks_data and len(decks_data) > 0:
        # Usar o resultado do primeiro deck (que tem os dados GL)
        result_structure_for_check = decks_data[0].result
        safe_print(f"[FORMATTER REGISTRY] Usando result_structure do primeiro deck. Keys: {list(result_structure_for_check.keys()) if isinstance(result_structure_for_check, dict) else 'not a dict'}")
    elif "decks" in tool_result:
        # Se não há decks_data mas há decks no tool_result, usar a estrutura completa
        result_structure_for_check = tool_result
        safe_print(f"[FORMATTER REGISTRY] Usando tool_result completo como result_structure. Keys: {list(result_structure_for_check.keys()) if isinstance(result_structure_for_check, dict) else 'not a dict'}")
    
    safe_print(f"[FORMATTER REGISTRY] Buscando formatter - tool_name_to_use: {tool_name_to_use}, tool_used: {tool_used}")
    formatter = get_formatter_for_tool(tool_name_to_use, result_structure_for_check)
    
    safe_print(f"[FORMATTER REGISTRY] Formatter selecionado: {formatter.__class__.__name__ if formatter else 'None'}")
    safe_print(f"[FORMATTER REGISTRY] tool_name_to_use: {tool_name_to_use}, tool_used: {tool_used}")
    
    if formatter is None:
        # Fallback: formatação básica
        safe_print(f"[FORMATTER REGISTRY] Nenhum formatter encontrado para tool: {tool_name_to_use} (tool_used: {tool_used})")
        safe_print(f"[FORMATTER REGISTRY] Result structure keys: {list(decks_data[0].result.keys()) if decks_data else []}")
        return {
            "final_response": f"## Comparação Multi-Deck\n\n{len(decks_data)} decks comparados.",
            "comparison_data": tool_result
        }
    
    # Formatar usando o formatter
    # Extrair kwargs adicionais do tool_result (ex: tipo_filtrado e tipo_encontrado para PQ)
    extra_kwargs = {}
    if "tipo_filtrado" in tool_result:
        extra_kwargs["tipo_filtrado"] = tool_result.get("tipo_filtrado")
    # IMPORTANTE: tipo_encontrado tem prioridade sobre tipo_filtrado (é o tipo REAL nos dados)
    if "tipo_encontrado" in tool_result:
        extra_kwargs["tipo_encontrado"] = tool_result.get("tipo_encontrado")
        safe_print(f"[FORMATTER REGISTRY] tipo_encontrado (REAL): {extra_kwargs['tipo_encontrado']}")
    elif "tipo_filtrado" in tool_result:
        safe_print(f"[FORMATTER REGISTRY] tipo_filtrado (query): {extra_kwargs['tipo_filtrado']}")
    
    formatted = formatter.format_multi_deck_comparison(decks_data, tool_used, query, **extra_kwargs)
    
    safe_print(f"[FORMATTER REGISTRY] Formatter retornou: keys={list(formatted.keys())}")
    
    # Garantir que tool_name está presente no comparison_data
    if "tool_name" not in formatted:
        formatted["tool_name"] = tool_name_to_use
        safe_print(f"[FORMATTER REGISTRY] Adicionado tool_name ao comparison_data: {tool_name_to_use}")
    
    return {
        "final_response": formatted.get("final_response", ""),
        "comparison_data": formatted
    }

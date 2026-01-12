"""
Registry de formatadores de comparação.
Mapeia tools para formatadores apropriados e fornece função consolidada para formatação.
"""
from typing import Dict, Any
from .base import ComparisonFormatter
from .data_formatters.temporal_formatters import (
    ClastComparisonFormatter,
    CargaComparisonFormatter,
    VazoesComparisonFormatter,
    UsinasNaoSimuladasFormatter,
    LimitesIntercambioComparisonFormatter,
)
from .data_formatters.diff_formatters import (
    DiffComparisonFormatter,
)
from .data_formatters.cadastro_formatters import (
    CadastroComparisonFormatter,
)
from .data_formatters.table_formatters import (
    TableComparisonFormatter,
)
from .data_formatters.llm_free_formatters import (
    LLMFreeFormatter,
)
from .data_formatters.gtmin_formatters import (
    MudancasGeracoesTermicasFormatter,
)
from .data_formatters.volume_inicial_formatters import (
    VariacaoVolumesIniciaisFormatter,
)


# Lista de formatadores (em ordem de prioridade - mais específicos primeiro)
FORMATTERS = [
    VariacaoVolumesIniciaisFormatter(),  # Alta prioridade - muito específico para volumes iniciais
    MudancasGeracoesTermicasFormatter(),  # Alta prioridade - muito específico para GTMIN
    ClastComparisonFormatter(),
    CargaComparisonFormatter(),
    VazoesComparisonFormatter(),
    UsinasNaoSimuladasFormatter(),
    LimitesIntercambioComparisonFormatter(),
    DiffComparisonFormatter(),
    CadastroComparisonFormatter(),
    TableComparisonFormatter(),
    LLMFreeFormatter(),  # Fallback - sempre deve ser o último
]


def get_formatter_for_tool(
    tool_name: str, 
    result_structure: Dict[str, Any]
) -> ComparisonFormatter:
    """
    Retorna o formatador mais apropriado para uma tool específica.
    
    Args:
        tool_name: Nome da tool (ex: "ClastValoresTool")
        result_structure: Estrutura do resultado da tool (para verificar campos disponíveis)
        
    Returns:
        Formatador apropriado (ou LLMFreeFormatter como fallback)
    """
    candidates = [
        f for f in FORMATTERS 
        if f.can_format(tool_name, result_structure)
    ]
    
    if candidates:
        # Retornar o formatador com maior prioridade
        return max(candidates, key=lambda f: f.get_priority())
    
    # Fallback para LLMFreeFormatter se nenhum formatador pode processar
    return LLMFreeFormatter()


def format_comparison_response(
    tool_result: Dict[str, Any], 
    tool_used: str, 
    query: str
) -> Dict[str, Any]:
    """
    Formata a resposta para o frontend quando é uma comparação multi-deck.
    Usa formatadores especializados por tool para gerar visualizações otimizadas.
    
    Args:
        tool_result: Resultado da tool de comparação (já contém deck_1, deck_2)
        tool_used: Nome da tool usada
        query: Query original do usuário
        
    Returns:
        Dict com final_response formatado e comparison_data
    """
    from app.config import safe_print
    
    # Limpar query se vier de disambiguation (remover tag __DISAMBIG__)
    if query.startswith("__DISAMBIG__:"):
        try:
            parts = query.split(":", 2)
            if len(parts) == 3:
                query = parts[2].strip()  # Usar apenas a query original
                safe_print(f"[FORMAT COMPARISON] Query limpa de disambiguation: {query}")
        except Exception as e:
            safe_print(f"[FORMAT COMPARISON] ⚠️ Erro ao limpar query de disambiguation: {e}")
    from .text_formatters.simple import (
        format_clast_simple_comparison,
        format_carga_simple_comparison,
        format_limites_intercambio_simple_comparison,
        format_gtmin_simple_comparison,
        format_volumes_iniciais_simple_comparison,
        generate_fallback_comparison_response
    )
    from .text_formatters.llm_structured import format_with_llm_structured
    from .text_formatters.llm_free import format_with_llm_free
    
    # Verificar se há dados de comparação
    if not tool_result.get("deck_1") and not tool_result.get("deck_2"):
        return {
            "final_response": "## Erro na Comparação\n\nNão foi possível obter dados de comparação.",
            "comparison_data": None
        }
    
    deck_1_name = tool_result.get("deck_1", {}).get("name", "Deck 1")
    deck_2_name = tool_result.get("deck_2", {}).get("name", "Deck 2")
    
    # Verificar se ambos os decks tiveram sucesso
    deck_1_success = tool_result.get("deck_1", {}).get("success", False)
    deck_2_success = tool_result.get("deck_2", {}).get("success", False)
    
    if not deck_1_success or not deck_2_success:
        # Se houve erro, retornar mensagem de erro sem chamar LLM
        response_parts = []
        response_parts.append(f"## Erro na Comparação\n\n")
        if not deck_1_success:
            error_1 = tool_result.get("deck_1", {}).get("error", "Erro desconhecido")
            response_parts.append(f"- **{deck_1_name}**: {error_1}\n")
        if not deck_2_success:
            error_2 = tool_result.get("deck_2", {}).get("error", "Erro desconhecido")
            response_parts.append(f"- **{deck_2_name}**: {error_2}\n")
        
        final_response = "".join(response_parts)
        return {
            "final_response": final_response,
            "comparison_data": {
                "deck_1": tool_result.get("deck_1", {}),
                "deck_2": tool_result.get("deck_2", {}),
                "tool_name": tool_used,
                "query": query
            }
        }
    
    # Obter formatador apropriado
    deck_1_result = tool_result.get("deck_1", {}).get("full_result", {})
    formatter = get_formatter_for_tool(tool_used, deck_1_result)
    
    safe_print(f"[INTERPRETER] [COMPARISON] Usando formatador: {formatter.__class__.__name__}")
    
    # Formatar comparação usando o formatador
    deck_1_full = tool_result.get("deck_1", {}).get("full_result", {})
    deck_2_full = tool_result.get("deck_2", {}).get("full_result", {})
    
    # Passar nomes dos decks se o formatter aceitar (usando inspect para verificar assinatura)
    import inspect
    sig = inspect.signature(formatter.format_comparison)
    format_kwargs = {
        "result_dec": deck_1_full,
        "result_jan": deck_2_full,
        "tool_name": tool_used,
        "query": query
    }
    
    # Se o formatter aceita deck_1_name e deck_2_name, passar
    if "deck_1_name" in sig.parameters:
        format_kwargs["deck_1_name"] = deck_1_name
    if "deck_2_name" in sig.parameters:
        format_kwargs["deck_2_name"] = deck_2_name
    
    formatted = formatter.format_comparison(**format_kwargs)
    
    visualization_type = formatted.get("visualization_type", "llm_free")
    safe_print(f"[INTERPRETER] [COMPARISON] Visualization type: {visualization_type}")
    
    # Construir comparison_data com estrutura formatada
    comparison_data = {
        "deck_1": tool_result.get("deck_1", {}),
        "deck_2": tool_result.get("deck_2", {}),
        "comparison_table": formatted.get("comparison_table"),
        "chart_data": formatted.get("chart_data"),
        "visualization_type": visualization_type,
        "chart_config": formatted.get("chart_config"),
        "tool_name": tool_used,
        "query": query,
    }
    
    # Adicionar dados específicos do formatador
    if formatted.get("diff_categories"):
        comparison_data["diff_categories"] = formatted.get("diff_categories")
    if formatted.get("cards"):
        comparison_data["cards"] = formatted.get("cards")
    if formatted.get("charts_by_par"):
        comparison_data["charts_by_par"] = formatted.get("charts_by_par")
    if formatted.get("comparison_by_type"):
        comparison_data["comparison_by_type"] = formatted.get("comparison_by_type")
    if formatted.get("comparison_by_usina"):
        comparison_data["comparison_by_usina"] = formatted.get("comparison_by_usina")
    if formatted.get("comparison_by_ree"):
        comparison_data["comparison_by_ree"] = formatted.get("comparison_by_ree")
    if formatted.get("stats"):
        comparison_data["stats"] = formatted.get("stats")
    
    # Para ClastValoresTool, CargaMensalTool, CadicTool e LimitesIntercambioTool, retornar apenas tabela e gráfico (sem LLM)
    if tool_used == "ClastValoresTool":
        safe_print(f"[INTERPRETER] [COMPARISON] ClastValoresTool - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data presente: {formatted.get('chart_data') is not None}")
        if formatted.get('chart_data'):
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data labels: {formatted.get('chart_data', {}).get('labels', [])}")
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data datasets: {len(formatted.get('chart_data', {}).get('datasets', []))}")
        final_response = format_clast_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name
        )
    elif tool_used in ["CargaMensalTool", "CadicTool"]:
        tool_label = "Carga Mensal" if tool_used == "CargaMensalTool" else "Carga Adicional"
        safe_print(f"[INTERPRETER] [COMPARISON] {tool_used} - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data presente: {formatted.get('chart_data') is not None}")
        if formatted.get('chart_data'):
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data labels: {len(formatted.get('chart_data', {}).get('labels', []))}")
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data datasets: {len(formatted.get('chart_data', {}).get('datasets', []))}")
        final_response = format_carga_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name,
            tool_label
        )
    elif tool_used == "LimitesIntercambioTool":
        safe_print(f"[INTERPRETER] [COMPARISON] LimitesIntercambioTool - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] charts_by_par presente: {formatted.get('charts_by_par') is not None}")
        if formatted.get('charts_by_par'):
            safe_print(f"[INTERPRETER] [COMPARISON] charts_by_par: {len(formatted.get('charts_by_par', {}))} pares")
        final_response = format_limites_intercambio_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name
        )
    elif tool_used == "MudancasGeracoesTermicasTool":
        safe_print(f"[INTERPRETER] [COMPARISON] MudancasGeracoesTermicasTool - formato simplificado (apenas tabela)")
        final_response = format_gtmin_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name
        )
    elif tool_used == "VariacaoVolumesIniciaisTool":
        safe_print(f"[INTERPRETER] [COMPARISON] VariacaoVolumesIniciaisTool - formato simplificado com introdução")
        final_response = format_volumes_iniciais_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name,
            formatted.get("stats", {})
        )
    else:
        # Gerar resposta do LLM baseada no tipo de visualização
        try:
            safe_print(f"[INTERPRETER] [COMPARISON] Gerando interpretação com LLM (tipo: {visualization_type})...")
            
            # Escolher prompt baseado no tipo de visualização
            if visualization_type in ["diff_list", "llm_free"]:
                final_response = format_with_llm_free(
                    deck_1_full, deck_2_full, tool_used, query,
                    deck_1_name, deck_2_name, formatted
                )
            else:
                final_response = format_with_llm_structured(
                    deck_1_full, deck_2_full, tool_used, query,
                    deck_1_name, deck_2_name, formatted
                )
            
        except Exception as e:
            safe_print(f"[INTERPRETER] [ERRO] Erro ao gerar interpretação com LLM: {e}")
            import traceback
            traceback.print_exc()
            # Fallback para resposta padrão
            final_response = generate_fallback_comparison_response(
                query, deck_1_name, deck_2_name, tool_used, formatted.get("comparison_table")
            )
    
    # Debug: verificar se chart_data está presente
    safe_print(f"[INTERPRETER] [COMPARISON] Retornando comparison_data com chart_data: {comparison_data.get('chart_data') is not None}")
    if comparison_data.get('chart_data'):
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data final - labels: {len(comparison_data.get('chart_data', {}).get('labels', []))}, datasets: {len(comparison_data.get('chart_data', {}).get('datasets', []))}")
    
    return {
        "final_response": final_response,
        "comparison_data": comparison_data
    }

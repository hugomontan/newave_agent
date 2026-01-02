"""
Formatadores simples para comparações (sem uso de LLM).
"""

from typing import List, Dict, Any


def format_clast_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str
) -> str:
    """
    Formata resposta simples para ClastValoresTool: apenas título.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de CVU\n\nNenhum dado disponível para comparação."
    
    # Verificar formato da tabela (CVU simplificado ou formato genérico)
    first_item = comparison_table[0] if comparison_table else {}
    is_cvu_format = "data" in first_item and "deck_1" in first_item and "deck_2" in first_item
    
    if is_cvu_format:
        # Apenas título - a tabela será renderizada pelo componente ComparisonView
        return "## Comparação de CVU\n"
    else:
        # Apenas título - a tabela será renderizada pelo componente ComparisonView
        return "## Comparação de Custos\n"


def format_carga_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    tool_label: str = "Carga Mensal"
) -> str:
    """
    Formata resposta simples para CargaMensalTool e CadicTool: apenas título.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Baseado no formato de CVU.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        tool_label: Label da tool ("Carga Mensal" ou "Carga Adicional")
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return f"## Comparação de {tool_label}\n\nNenhum dado disponível para comparação."
    
    # Apenas título - a tabela será renderizada pelo componente ComparisonView
    return f"## Comparação de {tool_label}\n"


def generate_fallback_comparison_response(
    query: str,
    deck_1_name: str,
    deck_2_name: str,
    tool_used: str,
    differences
) -> str:
    """
    Gera resposta de comparacao de fallback quando LLM falha.
    Segue o formato descritivo com resultado claro, sem conclusoes automaticas.
    """
    response_parts = []
    response_parts.append(f"## Analise Comparativa\n\n")
    
    # Resultado claro
    response_parts.append(f"### Resultado\n\n")
    
    if differences and len(differences) > 0:
        response_parts.append(f"Foram encontradas **{len(differences)} diferencas** entre {deck_1_name} e {deck_2_name}.\n\n")
        
        response_parts.append(f"### Diferencas Encontradas\n\n")
        # Mostrar top 5 diferencas
        sorted_diffs = sorted(differences, key=lambda x: abs(x.get("difference_percent", 0)), reverse=True)
        for diff in sorted_diffs[:5]:
            period = diff.get("period", "N/A")
            val_1 = diff.get("deck_1_value", 0)
            val_2 = diff.get("deck_2_value", 0)
            diff_percent = diff.get("difference_percent", 0)
            response_parts.append(f"- **{period}**: {val_1:.2f} -> {val_2:.2f} ({diff_percent:+.2f}%)\n")
        
        if len(differences) > 5:
            response_parts.append(f"\n*... e mais {len(differences) - 5} diferencas*\n")
        
        # Removido: conclusao automatica - o LLM deve ter liberdade para interpretar
    else:
        response_parts.append(f"Os dados sao **IDENTICOS** entre {deck_1_name} e {deck_2_name}.\n\n")
        response_parts.append(f"### Diferencas Encontradas\n\n")
        response_parts.append(f"Nenhuma diferenca encontrada.\n\n")
        # Removido: conclusao automatica - o LLM deve ter liberdade para interpretar
    
    return "".join(response_parts)


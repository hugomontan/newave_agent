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
    Formata resposta simples para ClastValoresTool: título + informação de validação.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        
    Returns:
        String markdown com título e informação de validação (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de CVU\n\nNenhum dado disponível para comparação."
    
    # Verificar formato da tabela (CVU simplificado ou formato genérico)
    first_item = comparison_table[0] if comparison_table else {}
    is_cvu_format = "data" in first_item and "deck_1" in first_item and "deck_2" in first_item
    
    # Extrair informação de validação (classe_info) se disponível
    classe_info = first_item.get("classe_info")
    
    if is_cvu_format:
        # Título + informação de validação
        response = "## Comparação de CVU\n"
        if classe_info:
            response += f"\n**Custos de Classe - Nome da usina:** {classe_info}\n"
        return response
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


def format_limites_intercambio_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str
) -> str:
    """
    Formata resposta simples para LimitesIntercambioTool: apenas título.
    A tabela e os gráficos são renderizados pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de Limites de Intercâmbio\n\nNenhum dado disponível para comparação."
    
    # Apenas título - a tabela será renderizada pelo componente ComparisonView
    return "## Comparação de Limites de Intercâmbio\n"


def format_vazao_minima_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str
) -> str:
    """
    Formata resposta simples para MudancasVazaoMinimaTool: apenas título.
    A tabela é renderizada pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de Mudanças de Vazão Mínima\n\nNenhum dado disponível para comparação."
    
    # Apenas título - a tabela será renderizada pelo componente ComparisonView
    return "## Comparação de Mudanças de Vazão Mínima\n"


def format_gtmin_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str
) -> str:
    """
    Formata resposta simples para MudancasGeracoesTermicasTool: apenas título.
    A tabela é renderizada pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Mudanças em Gerações Térmicas\n\nNenhuma mudança encontrada entre os decks."
    
    # Apenas título - a tabela será renderizada pelo componente ComparisonView
    return "## Mudanças em Gerações Térmicas\n"


def format_volumes_iniciais_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    stats: Dict[str, Any] = None
) -> str:
    """
    Formata resposta para VariacaoVolumesIniciaisTool: título + introdução curta gerada por LLM.
    A tabela é renderizada pelo componente ComparisonView no frontend.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1
        deck_2_name: Nome do deck 2
        stats: Estatísticas da comparação (opcional)
        
    Returns:
        String markdown com título e introdução curta
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
    
    if not comparison_table:
        return "## Variação de Volumes Iniciais\n\nNenhuma mudança encontrada entre os decks."
    
    # Gerar introdução curta usando LLM
    try:
        stats = stats or {}
        total_mudancas = stats.get("total_mudancas", len(comparison_table))
        tipos_mudanca = stats.get("tipos_mudanca", {})
        mudancas_por_ree = stats.get("mudancas_por_ree", {})
        
        # Preparar resumo das estatísticas
        stats_summary = f"Total de mudanças: {total_mudancas}\n"
        if tipos_mudanca:
            stats_summary += f"Aumentos: {tipos_mudanca.get('aumento', 0)}, "
            stats_summary += f"Reduções: {tipos_mudanca.get('reducao', 0)}, "
            stats_summary += f"Inclusões: {tipos_mudanca.get('novo', 0)}, "
            stats_summary += f"Exclusões: {tipos_mudanca.get('remocao', 0)}\n"
        
        if mudancas_por_ree:
            stats_summary += f"Mudanças por REE: {len(mudancas_por_ree)} REEs afetados\n"
        
        # Top 5 mudanças por magnitude
        top_mudancas = sorted(comparison_table, key=lambda x: abs(x.get("magnitude", 0)), reverse=True)[:5]
        top_summary = "Principais mudanças:\n"
        for mudanca in top_mudancas:
            nome = mudanca.get("nome_usina", "N/A")
            magnitude = mudanca.get("magnitude", 0)
            tipo = mudanca.get("tipo_mudanca", "N/A")
            top_summary += f"- {nome}: {magnitude:.2f}% ({tipo})\n"
        
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em análise de dados do setor elétrico brasileiro.
            
Sua tarefa é gerar uma introdução CURTA e OBJETIVA (2-3 frases) sobre a variação de volumes iniciais entre dois decks.

REGRAS:
- Seja conciso e direto
- Apenas apresente um resumo geral dos dados
- Não liste usinas específicas (a tabela já mostra isso)
- Foque em padrões gerais (ex: "maioria das mudanças são aumentos", "concentradas em alguns REEs")
- Use linguagem técnica mas acessível
- Máximo 3 frases"""),
            ("human", """Gere uma introdução curta sobre a variação de volumes iniciais entre {deck_1_name} e {deck_2_name}.

Estatísticas:
{stats_summary}

{top_summary}

Gere apenas a introdução (2-3 frases), sem título. Comece diretamente com o conteúdo.""")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "deck_1_name": deck_1_name,
            "deck_2_name": deck_2_name,
            "stats_summary": stats_summary,
            "top_summary": top_summary
        })
        
        introduction = getattr(response, 'content', '').strip()
        if introduction:
            safe_print(f"[INTERPRETER] [COMPARISON] Introdução gerada: {len(introduction)} caracteres")
            return f"## Variação de Volumes Iniciais\n\n{introduction}\n"
        else:
            safe_print(f"[INTERPRETER] [COMPARISON] LLM não retornou introdução, usando fallback")
            return "## Variação de Volumes Iniciais\n"
            
    except Exception as e:
        safe_print(f"[INTERPRETER] [COMPARISON] Erro ao gerar introdução: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: apenas título
        return "## Variação de Volumes Iniciais\n"


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
    
    if differences and len(differences) > 0:
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
        # Removido: seção "Resultado" e mensagem "Os dados são IDENTICOS" - não é necessário mostrar essa informação
        response_parts.append(f"### Diferencas Encontradas\n\n")
        response_parts.append(f"Nenhuma diferenca encontrada.\n\n")
        # Removido: conclusao automatica - o LLM deve ter liberdade para interpretar
    
    return "".join(response_parts)

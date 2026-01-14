"""
Formatadores simples para single deck (sem uso de LLM).
Retornam apenas títulos em Markdown - tabelas e gráficos são renderizados no frontend.
"""

from typing import List, Dict, Any


def format_clast_simple(table_data: List[Dict[str, Any]], is_cvu: bool = False, titulo: str = None) -> str:
    """
    Formata resposta simples para ClastValoresTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        is_cvu: Se True, trata como CVU
        titulo: Título personalizado (opcional)
        
    Returns:
        String markdown com título (sem tabela, renderizada no frontend)
    """
    if titulo:
        return f"## {titulo}\n"
    
    if is_cvu:
        return "## Custo Variável Unitário (CVU)\n"
    return "## Custos de Classes Térmicas\n"


def format_carga_mensal_simple(table_data: List[Dict[str, Any]], titulo: str = None) -> str:
    """
    Formata resposta simples para CargaMensalTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        titulo: Título personalizado (opcional)
        
    Returns:
        String markdown com título
    """
    if titulo:
        return f"## {titulo}\n"
    return "## Carga Mensal\n"


def format_cadic_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para CadicTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Carga Adicional\n"


def format_vazoes_simple(table_data: List[Dict[str, Any]], title_suffix: str = "") -> str:
    """
    Formata resposta simples para VazoesTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        title_suffix: Sufixo para o título (ex: " - FURNAS (Posto 6)")
        
    Returns:
        String markdown com título
    """
    return f"## Vazões Históricas{title_suffix}\n"


def format_dsvagua_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para DsvaguaTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Desvios de Água\n"


def format_limites_intercambio_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para LimitesIntercambioTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Limites de Intercâmbio\n"


def format_cadastro_hidr_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para HidrCadastroTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Cadastro de Hidrelétrica\n"


def format_cadastro_term_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para TermCadastroTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Cadastro de Termelétrica\n"


def format_confhd_simple(table_data: List[Dict[str, Any]]) -> str:
    """
    Formata resposta simples para ConfhdTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        
    Returns:
        String markdown com título
    """
    return "## Configuração de Hidrelétrica\n"


def format_usinas_nao_simuladas_simple(table_data: List[Dict[str, Any]], titulo: str = None) -> str:
    """
    Formata resposta simples para UsinasNaoSimuladasTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        titulo: Título personalizado (opcional)
        
    Returns:
        String markdown com título
    """
    if titulo:
        return f"## {titulo}\n"
    return "## Usinas Não Simuladas\n"


def format_modif_operacao_simple(
    tables_by_tipo: Dict[str, List[Dict[str, Any]]],
    filtros: Dict[str, Any] = None,
    stats_geral: Dict[str, Any] = None,
    titulo: str = None
) -> str:
    """
    Formata resposta simples para ModifOperacaoTool.
    Retorna apenas título/resumo - tabelas são renderizadas pelo frontend.
    
    Args:
        tables_by_tipo: Dicionário com dados agrupados por tipo de modificação
        filtros: Informações sobre filtros aplicados
        stats_geral: Estatísticas gerais
        titulo: Título personalizado (opcional)
        
    Returns:
        String markdown formatada (apenas título, sem tabelas)
    """
    if titulo:
        return f"## {titulo}\n"
    return "## Modificações Hídricas\n"


def format_restricao_eletrica_simple(table_data: List[Dict[str, Any]], query: str = None) -> str:
    """
    Formata resposta simples para RestricaoEletricaTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        query: Query original do usuário (para personalizar título)
        
    Returns:
        String markdown com título
    """
    # Detectar se a query menciona uma restrição específica
    if query:
        query_lower = query.lower()
        # Verificar se há nomes de restrições nos dados
        restricoes_unicas = set()
        for row in table_data:
            restricao = row.get("restricao", "")
            if restricao:
                restricoes_unicas.add(restricao)
        
        # Se há apenas uma restrição, usar no título
        if len(restricoes_unicas) == 1:
            restricao_nome = list(restricoes_unicas)[0]
            return f"## Restrições Elétricas - {restricao_nome}\n"
    
    return "## Restrições Elétricas\n"

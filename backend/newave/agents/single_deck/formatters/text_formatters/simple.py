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


def format_cadic_simple(table_data: List[Dict[str, Any]], tool_result: Dict[str, Any] = None, query: str = "") -> str:
    """
    Formata resposta simples para CadicTool.
    Retorna apenas título - tabelas e gráficos são renderizados pelo frontend.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        tool_result: Resultado completo da tool (opcional, para obter filtros)
        query: Query original do usuário (opcional, para fallback de detecção)
        
    Returns:
        String markdown com apenas título
    """
    # Extrair informações para título personalizado (opcional)
    razoes_unicas = set()
    subsistemas_unicos = {}
    
    if table_data and len(table_data) > 0:
        for record in table_data:
            # Extrair razões únicas
            if 'razao' in record and record['razao']:
                razoes_unicas.add(str(record['razao']).strip())
            
            # Extrair subsistemas únicos
            if 'codigo_submercado' in record and record['codigo_submercado'] is not None:
                cod = record['codigo_submercado']
                nome = record.get('submercado') or record.get('nome_submercado') or f"Subsistema {cod}"
                if cod not in subsistemas_unicos:
                    subsistemas_unicos[cod] = nome
    
    # Construir título simples
    titulo_parts = []
    
    if razoes_unicas:
        razoes_lista = sorted(list(razoes_unicas))
        if len(razoes_lista) == 1:
            titulo_parts.append(f"Carga Adicional - {razoes_lista[0]}")
        else:
            razoes_str = ", ".join(razoes_lista)
            titulo_parts.append(f"Carga Adicional - {razoes_str}")
    elif subsistemas_unicos:
        subsistemas_lista = sorted(list(subsistemas_unicos.items()))
        if len(subsistemas_lista) == 1:
            _, nome = subsistemas_lista[0]
            titulo_parts.append(f"Carga Adicional - {nome}")
        else:
            nomes = [nome for _, nome in subsistemas_lista]
            nomes_str = ", ".join(nomes)
            titulo_parts.append(f"Carga Adicional - {nomes_str}")
    
    # Fallback para filtros se não encontrou dados reais
    if not titulo_parts and tool_result:
        filtros = tool_result.get("filtros")
        if filtros and isinstance(filtros, dict) and len(filtros) > 0:
            if filtros.get("razao"):
                razao = filtros["razao"]
                titulo_parts.append(f"Carga Adicional - {razao}")
            elif filtros.get("subsistema"):
                subsistema = filtros["subsistema"]
                nome_sub = subsistema.get("nome", f"Subsistema {subsistema.get('codigo', 'N/A')}")
                titulo_parts.append(f"Carga Adicional - {nome_sub}")
    
    # Retornar apenas título
    if titulo_parts:
        return f"## {titulo_parts[0]}\n"
    else:
        return "## Cargas e Ofertas Adicionais\n"


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


def format_dsvagua_simple(table_data: List[Dict[str, Any]], nome_usina: str = None) -> str:
    """
    Formata resposta simples para DsvaguaTool.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        nome_usina: Nome da usina (opcional, para personalizar título)
        
    Returns:
        String markdown com título
    """
    if nome_usina:
        return f"## Desvios de Água - {nome_usina}\n"
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


def format_expt_operacao_simple(
    tables_by_tipo: Dict[str, List[Dict[str, Any]]],
    filtros: Dict[str, Any] = None,
    titulo: str = None
) -> str:
    """
    Formata resposta simples para ExptOperacaoTool.
    Retorna apenas título - tabelas são renderizadas pelo frontend.
    
    Args:
        tables_by_tipo: Dicionário com dados agrupados por tipo de modificação
        filtros: Informações sobre filtros aplicados (para obter nome da usina)
        titulo: Título personalizado (opcional)
        
    Returns:
        String markdown formatada (apenas título, sem tabelas)
    """
    if titulo:
        return f"## {titulo}\n"
    
    # Obter nome da usina dos filtros
    nome_usina = "USINA"
    if filtros and 'usina' in filtros:
        nome_usina = filtros['usina'].get('nome', 'USINA')
    
    return f"## Dados de Operação Térmica - {nome_usina}\n"

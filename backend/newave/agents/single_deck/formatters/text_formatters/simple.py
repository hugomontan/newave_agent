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
    Formata resposta simples para CadicTool com confirmação textual.
    Extrai informações reais dos dados retornados para construir a confirmação.
    
    Args:
        table_data: Lista de dicionários com dados tabulares
        tool_result: Resultado completo da tool (opcional, para obter filtros)
        query: Query original do usuário (opcional, para fallback de detecção)
        
    Returns:
        String markdown com título e confirmação
    """
    response_parts = []
    
    # ETAPA 1: Extrair informações reais dos dados retornados (prioridade máxima)
    razoes_unicas = set()
    subsistemas_unicos = {}
    valores_positivos = 0
    valores_negativos = 0
    
    if table_data and len(table_data) > 0:
        for record in table_data:
            # Extrair razões únicas
            if 'razao' in record and record['razao']:
                razoes_unicas.add(str(record['razao']).strip())
            
            # Extrair subsistemas únicos (código e nome)
            if 'codigo_submercado' in record and record['codigo_submercado'] is not None:
                cod = record['codigo_submercado']
                # Priorizar 'submercado' (nome processado), depois 'nome_submercado', depois fallback
                nome = record.get('submercado') or record.get('nome_submercado') or f"Subsistema {cod}"
                if cod not in subsistemas_unicos:
                    subsistemas_unicos[cod] = nome
            
            # Contar valores positivos (cargas) e negativos (ofertas)
            if 'valor' in record and record['valor'] is not None:
                try:
                    valor = float(record['valor'])
                    if valor > 0:
                        valores_positivos += 1
                    elif valor < 0:
                        valores_negativos += 1
                except (ValueError, TypeError):
                    pass
    
    # ETAPA 2: Construir título e confirmação baseado nos dados reais
    confirmacao_parts = []
    titulo_parts = []
    
    # Determinar tipo (carga, oferta ou ambos)
    tem_cargas = valores_positivos > 0
    tem_ofertas = valores_negativos > 0
    tipo_dados = None
    if tem_cargas and not tem_ofertas:
        tipo_dados = "carga"
    elif tem_ofertas and not tem_cargas:
        tipo_dados = "oferta"
    # Se tem ambos ou nenhum, não especificar tipo
    
    # Construir confirmação baseada em razões (prioridade 1)
    if razoes_unicas:
        razoes_lista = sorted(list(razoes_unicas))
        if len(razoes_lista) == 1:
            razao = razoes_lista[0]
            if tipo_dados == "carga":
                confirmacao_parts.append(f"**Carga adicional da razão {razao}**")
                titulo_parts.append(f"Carga Adicional - {razao}")
            elif tipo_dados == "oferta":
                confirmacao_parts.append(f"**Oferta adicional da razão {razao}**")
                titulo_parts.append(f"Oferta Adicional - {razao}")
            else:
                confirmacao_parts.append(f"**Cargas e ofertas adicionais da razão {razao}**")
                titulo_parts.append(f"Carga Adicional - {razao}")
        else:
            # Múltiplas razões
            razoes_str = ", ".join(razoes_lista)
            if tipo_dados == "carga":
                confirmacao_parts.append(f"**Cargas adicionais das razões: {razoes_str}**")
                titulo_parts.append(f"Carga Adicional - {razoes_str}")
            elif tipo_dados == "oferta":
                confirmacao_parts.append(f"**Ofertas adicionais das razões: {razoes_str}**")
                titulo_parts.append(f"Oferta Adicional - {razoes_str}")
            else:
                confirmacao_parts.append(f"**Cargas e ofertas adicionais das razões: {razoes_str}**")
                titulo_parts.append(f"Carga Adicional - {razoes_str}")
    
    # Construir confirmação baseada em subsistemas (prioridade 2, se não tiver razão)
    elif subsistemas_unicos:
        subsistemas_lista = sorted(list(subsistemas_unicos.items()))
        if len(subsistemas_lista) == 1:
            cod, nome = subsistemas_lista[0]
            if tipo_dados == "carga":
                confirmacao_parts.append(f"**Cargas adicionais do {nome}**")
                titulo_parts.append(f"Carga Adicional - {nome}")
            elif tipo_dados == "oferta":
                confirmacao_parts.append(f"**Ofertas adicionais do {nome}**")
                titulo_parts.append(f"Oferta Adicional - {nome}")
            else:
                confirmacao_parts.append(f"**Cargas e ofertas adicionais do {nome}**")
                titulo_parts.append(f"Carga Adicional - {nome}")
        else:
            # Múltiplos subsistemas
            nomes = [nome for _, nome in subsistemas_lista]
            nomes_str = ", ".join(nomes)
            if tipo_dados == "carga":
                confirmacao_parts.append(f"**Cargas adicionais dos subsistemas: {nomes_str}**")
                titulo_parts.append(f"Carga Adicional - {nomes_str}")
            elif tipo_dados == "oferta":
                confirmacao_parts.append(f"**Ofertas adicionais dos subsistemas: {nomes_str}**")
                titulo_parts.append(f"Oferta Adicional - {nomes_str}")
            else:
                confirmacao_parts.append(f"**Cargas e ofertas adicionais dos subsistemas: {nomes_str}**")
                titulo_parts.append(f"Carga Adicional - {nomes_str}")
    
    # ETAPA 3: Adicionar informações de período dos dados reais (se disponível)
    if tool_result and tool_result.get("summary"):
        summary = tool_result["summary"]
        periodo_info = summary.get("periodo_coberto")
        if periodo_info:
            ano_inicio = periodo_info.get("ano_inicio")
            ano_fim = periodo_info.get("ano_fim")
            if ano_inicio and ano_fim:
                if ano_inicio == ano_fim:
                    confirmacao_parts.append(f"no ano {ano_inicio}")
                else:
                    confirmacao_parts.append(f"no período {ano_inicio} a {ano_fim}")
            elif ano_inicio:
                confirmacao_parts.append(f"no ano {ano_inicio}")
    
    # ETAPA 4: Fallback para filtros se não encontrou dados reais
    if not confirmacao_parts and tool_result:
        filtros = tool_result.get("filtros")
        if filtros and isinstance(filtros, dict) and len(filtros) > 0:
            if filtros.get("razao"):
                razao = filtros["razao"]
                tipo = filtros.get("tipo")
                if tipo == "carga":
                    confirmacao_parts.append(f"**Carga adicional da razão {razao}**")
                    titulo_parts.append(f"Carga Adicional - {razao}")
                elif tipo == "oferta":
                    confirmacao_parts.append(f"**Oferta adicional da razão {razao}**")
                    titulo_parts.append(f"Oferta Adicional - {razao}")
                else:
                    confirmacao_parts.append(f"**Cargas e ofertas adicionais da razão {razao}**")
                    titulo_parts.append(f"Carga Adicional - {razao}")
            
            if filtros.get("subsistema") and not confirmacao_parts:
                subsistema = filtros["subsistema"]
                nome_sub = subsistema.get("nome", f"Subsistema {subsistema.get('codigo', 'N/A')}")
                confirmacao_parts.append(f"**Cargas e ofertas adicionais do {nome_sub}**")
                titulo_parts.append(f"Carga Adicional - {nome_sub}")
    
    # ETAPA 5: Construir título e mensagem final
    if titulo_parts:
        titulo = "## " + titulo_parts[0] + "\n\n"
    else:
        titulo = "## Cargas e Ofertas Adicionais\n\n"
    
    response_parts.append(titulo)
    
    # Construir mensagem final - SEMPRE mostrar pelo menos uma mensagem
    if confirmacao_parts:
        confirmacao = " ".join(confirmacao_parts) + "."
        response_parts.append(f"{confirmacao}\n\n")
    else:
        # Sem dados específicos - mostrar mensagem genérica (sempre aparece)
        response_parts.append("**Cargas e ofertas adicionais** do sistema.\n\n")
    
    # Adicionar estatísticas se disponíveis
    if tool_result and tool_result.get("summary"):
        summary = tool_result["summary"]
        stats_parts = []
        
        if summary.get("total_registros"):
            stats_parts.append(f"- Total de registros: {summary['total_registros']}")
        
        if summary.get("subsistemas"):
            stats_parts.append(f"- Subsistemas: {summary['subsistemas']}")
        
        if summary.get("periodo_coberto"):
            periodo = summary["periodo_coberto"]
            if periodo.get("ano_inicio") and periodo.get("ano_fim"):
                if periodo["ano_inicio"] == periodo["ano_fim"]:
                    stats_parts.append(f"- Ano: {periodo['ano_inicio']}")
                else:
                    stats_parts.append(f"- Período: {periodo['ano_inicio']} a {periodo['ano_fim']}")
        
        if stats_parts:
            response_parts.append("### Resumo\n\n")
            response_parts.append("\n".join(stats_parts))
            response_parts.append("\n\n")
    
    # Garantir retorno final
    final_response = "".join(response_parts)
    if not final_response or not final_response.strip():
        # Fallback absoluto
        return "## Cargas e Ofertas Adicionais\n\n**Cargas e ofertas adicionais** do sistema.\n\n"
    
    return final_response


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

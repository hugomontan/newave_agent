"""
Formatadores simples para comparações (sem uso de LLM).
Suporta N decks para comparação dinâmica.
"""

from typing import List, Dict, Any, Optional


def _get_deck_names_summary(deck_names: Optional[List[str]] = None, deck_1_name: str = "", deck_2_name: str = "") -> str:
    """
    Gera string resumida dos nomes dos decks para títulos.
    
    Args:
        deck_names: Lista de nomes de decks (para N decks)
        deck_1_name: Nome do primeiro deck (fallback para dois decks)
        deck_2_name: Nome do último deck (fallback para dois decks)
        
    Returns:
        String resumida (ex: "Jan-2025 a Dez-2025" ou "Jan-2025 vs Jan-2026")
    """
    if deck_names and len(deck_names) > 2:
        return f"{deck_names[0]} a {deck_names[-1]}"
    elif deck_names and len(deck_names) == 2:
        return f"{deck_names[0]} vs {deck_names[1]}"
    elif deck_names and len(deck_names) == 1:
        return deck_names[0]
    else:
        return f"{deck_1_name} vs {deck_2_name}"


def format_clast_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para ClastValoresTool: título + informação de validação.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback para dois decks)
        deck_2_name: Nome do deck 2 (fallback para dois decks)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com título e informação de validação (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de CVU\n\nNenhum dado disponível para comparação."
    
    # Verificar formato da tabela (CVU simplificado ou formato genérico)
    first_item = comparison_table[0] if comparison_table else {}
    
    # Novo formato N-decks: cada deck é uma coluna separada
    is_n_deck_format = any(key.startswith("deck_") for key in first_item.keys() if key not in ["data", "ano"])
    is_cvu_format = "data" in first_item and ("deck_1" in first_item or is_n_deck_format)
    
    # Extrair informação de validação (classe_info) se disponível
    classe_info = first_item.get("classe_info")
    
    # Gerar título com informação de decks
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    n_decks = len(deck_names) if deck_names else 2
    
    if is_cvu_format:
        # Título + informação de validação
        if n_decks > 2:
            response = f"## Evolução Histórica de CVU ({deck_summary})\n"
        else:
            response = "## Comparação de CVU\n"
        if classe_info:
            response += f"\n**Custos de Classe - Nome da usina:** {classe_info}\n"
        return response
    else:
        # Apenas título - a tabela será renderizada pelo componente ComparisonView
        if n_decks > 2:
            return f"## Evolução Histórica de Custos ({deck_summary})\n"
        return "## Comparação de Custos\n"


def format_carga_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    tool_label: str = "Carga Mensal",
    deck_names: Optional[List[str]] = None,
    tool_result: Optional[Dict[str, Any]] = None
) -> str:
    """
    Formata resposta simples para CargaMensalTool e CadicTool: título com informações extraídas dos dados.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        tool_label: Label da tool ("Carga Mensal" ou "Carga Adicional")
        deck_names: Lista de nomes de decks (para N decks)
        tool_result: Resultado completo da tool (opcional, para extrair informações reais)
        
    Returns:
        String markdown com título e confirmação baseada nos dados reais
    """
    if not comparison_table:
        return f"## Comparação de {tool_label}\n\nNenhum dado disponível para comparação."
    
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    # ETAPA 1: Extrair informações reais dos dados retornados (prioridade máxima)
    razoes_unicas = set()
    subsistemas_unicos = {}
    valores_positivos = 0
    valores_negativos = 0
    
    # Extrair de tool_result (dados originais) se disponível
    if tool_result:
        # Verificar formato N-decks (decks lista) ou legado (deck_1, deck_2)
        decks_list = tool_result.get("decks", [])
        if not decks_list:
            # Formato legado: criar lista a partir de deck_1 e deck_2
            deck_1 = tool_result.get("deck_1", {})
            deck_2 = tool_result.get("deck_2", {})
            if deck_1:
                decks_list.append(deck_1)
            if deck_2:
                decks_list.append(deck_2)
        
        # Extrair dados de todos os decks
        for deck in decks_list:
            # Obter full_result ou result
            deck_data = deck.get("full_result") or deck.get("result") or deck
            if not isinstance(deck_data, dict):
                continue
            
            # Extrair dados brutos
            data_list = deck_data.get("data", [])
            if not data_list and deck_data.get("dados_por_submercado"):
                # Se dados estão por submercado, extrair de lá
                for sub_data in deck_data.get("dados_por_submercado", {}).values():
                    if isinstance(sub_data, dict):
                        data_list.extend(sub_data.get("dados", []))
            
            # Processar cada registro
            for record in data_list:
                if not isinstance(record, dict):
                    continue
                
                # Extrair razões únicas (CadicTool)
                if 'razao' in record and record['razao']:
                    razoes_unicas.add(str(record['razao']).strip())
                
                # Extrair subsistemas únicos
                nome_sub = record.get('nome_submercado') or record.get('submercado')
                cod = record.get('codigo_submercado')
                if nome_sub or cod:
                    if cod:
                        if cod not in subsistemas_unicos:
                            subsistemas_unicos[cod] = nome_sub or f"Subsistema {cod}"
                    elif nome_sub:
                        # Se não tem código, usar nome como chave
                        if nome_sub not in subsistemas_unicos.values():
                            subsistemas_unicos[nome_sub] = nome_sub
                
                # Contar valores positivos (cargas) e negativos (ofertas)
                valor = record.get('valor')
                if valor is not None:
                    try:
                        valor_float = float(valor)
                        if valor_float > 0:
                            valores_positivos += 1
                        elif valor_float < 0:
                            valores_negativos += 1
                    except (ValueError, TypeError):
                        pass
    
    # ETAPA 2: Construir título e confirmação baseado nos dados reais
    titulo_parts = []
    confirmacao_parts = []
    
    # Determinar tipo (carga, oferta ou ambos)
    tem_cargas = valores_positivos > 0
    tem_ofertas = valores_negativos > 0
    tipo_dados = None
    if tem_cargas and not tem_ofertas:
        tipo_dados = "carga"
    elif tem_ofertas and not tem_cargas:
        tipo_dados = "oferta"
    
    # Construir confirmação baseada em razões (prioridade 1) - apenas para CadicTool
    if razoes_unicas and tool_label == "Carga Adicional":
        razoes_lista = sorted(list(razoes_unicas))
        if len(razoes_lista) == 1:
            razao = razoes_lista[0]
            if tipo_dados == "carga":
                titulo_parts.append(f"Carga Adicional - {razao}")
                confirmacao_parts.append(f"**Carga adicional da razão {razao}**")
            elif tipo_dados == "oferta":
                titulo_parts.append(f"Oferta Adicional - {razao}")
                confirmacao_parts.append(f"**Oferta adicional da razão {razao}**")
            else:
                titulo_parts.append(f"Carga Adicional - {razao}")
                confirmacao_parts.append(f"**Cargas e ofertas adicionais da razão {razao}**")
        else:
            # Múltiplas razões
            razoes_str = ", ".join(razoes_lista)
            if tipo_dados == "carga":
                titulo_parts.append(f"Carga Adicional - {razoes_str}")
                confirmacao_parts.append(f"**Cargas adicionais das razões: {razoes_str}**")
            elif tipo_dados == "oferta":
                titulo_parts.append(f"Oferta Adicional - {razoes_str}")
                confirmacao_parts.append(f"**Ofertas adicionais das razões: {razoes_str}**")
            else:
                titulo_parts.append(f"Carga Adicional - {razoes_str}")
                confirmacao_parts.append(f"**Cargas e ofertas adicionais das razões: {razoes_str}**")
    
    # Construir confirmação baseada em subsistemas (prioridade 2, se não tiver razão)
    elif subsistemas_unicos:
        subsistemas_lista = sorted(list(subsistemas_unicos.items()))
        if len(subsistemas_lista) == 1:
            cod, nome = subsistemas_lista[0]
            if tipo_dados == "carga":
                titulo_parts.append(f"{tool_label} - {nome}")
                confirmacao_parts.append(f"**Cargas adicionais do {nome}**")
            elif tipo_dados == "oferta":
                titulo_parts.append(f"{tool_label} - {nome}")
                confirmacao_parts.append(f"**Ofertas adicionais do {nome}**")
            else:
                titulo_parts.append(f"{tool_label} - {nome}")
                confirmacao_parts.append(f"**Cargas e ofertas adicionais do {nome}**")
        else:
            # Múltiplos subsistemas
            nomes = [nome for _, nome in subsistemas_lista]
            nomes_str = ", ".join(nomes)
            if tipo_dados == "carga":
                titulo_parts.append(f"{tool_label} - {nomes_str}")
                confirmacao_parts.append(f"**Cargas adicionais dos subsistemas: {nomes_str}**")
            elif tipo_dados == "oferta":
                titulo_parts.append(f"{tool_label} - {nomes_str}")
                confirmacao_parts.append(f"**Ofertas adicionais dos subsistemas: {nomes_str}**")
            else:
                titulo_parts.append(f"{tool_label} - {nomes_str}")
                confirmacao_parts.append(f"**Cargas e ofertas adicionais dos subsistemas: {nomes_str}**")
    
    # ETAPA 3: Construir resposta final
    response_parts = []
    
    if titulo_parts:
        titulo_base = titulo_parts[0]
        if n_decks > 2:
            response_parts.append(f"## Evolução Histórica de {titulo_base} ({deck_summary})\n\n")
        else:
            response_parts.append(f"## Comparação de {titulo_base}\n\n")
    else:
        # Fallback para título genérico
        if n_decks > 2:
            response_parts.append(f"## Evolução Histórica de {tool_label} ({deck_summary})\n\n")
        else:
            response_parts.append(f"## Comparação de {tool_label}\n\n")
    
    # Adicionar confirmação se disponível
    if confirmacao_parts:
        confirmacao = " ".join(confirmacao_parts) + "."
        response_parts.append(f"{confirmacao}\n\n")
    
    return "".join(response_parts)


def format_limites_intercambio_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para LimitesIntercambioTool: apenas título.
    A tabela e os gráficos são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        return "## Comparação de Limites de Intercâmbio\n\nNenhum dado disponível para comparação."
    
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    if n_decks > 2:
        return f"## Evolução Histórica de Limites de Intercâmbio ({deck_summary})\n"
    return "## Comparação de Limites de Intercâmbio\n"


def format_vazao_minima_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para MudancasVazaoMinimaTool: apenas título.
    A tabela é renderizada pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    if not comparison_table:
        if n_decks > 2:
            return f"## Evolução de Mudanças de Vazão Mínima\n\nNão houveram mudanças registradas no período {deck_summary}."
        return f"## Comparação de Mudanças de Vazão Mínima\n\nNão houveram mudanças registradas do deck {deck_1_name} para o deck {deck_2_name}."
    
    if n_decks > 2:
        return f"## Evolução de Mudanças de Vazão Mínima ({deck_summary})\n"
    return "## Comparação de Mudanças de Vazão Mínima\n"


def format_gtmin_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para MudancasGeracoesTermicasTool: apenas título.
    A tabela é renderizada pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título (sem tabela, pois será renderizada pelo componente)
    """
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    if not comparison_table:
        if n_decks > 2:
            return f"## Evolução de Gerações Térmicas\n\nNenhuma mudança encontrada no período {deck_summary}."
        return "## Mudanças em Gerações Térmicas\n\nNenhuma mudança encontrada entre os decks."
    
    if n_decks > 2:
        return f"## Evolução de Gerações Térmicas ({deck_summary})\n"
    return "## Mudanças em Gerações Térmicas\n"


def format_vazoes_dsvagua_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    tool_name: str = "VazoesTool",
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para VazoesTool e DsvaguaTool: apenas título.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        tool_name: Nome da tool ("VazoesTool" ou "DsvaguaTool")
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com título (sem tabela, pois será renderizada pelo componente)
    """
    if not comparison_table:
        tool_label = "Vazões Históricas" if tool_name == "VazoesTool" else "Desvios de Água"
        return f"## Comparação de {tool_label}\n\nNenhum dado disponível para comparação."
    
    # Gerar título com informação de decks
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    n_decks = len(deck_names) if deck_names else 2
    
    if tool_name == "DsvaguaTool":
        tool_label = "Desvios de Água"
    else:
        tool_label = "Vazões Históricas"
    
    if n_decks > 2:
        return f"## Comparação de {tool_label} ({deck_summary})\n"
    return f"## Comparação de {tool_label}\n"


def format_usinas_nao_simuladas_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta simples para UsinasNaoSimuladasTool: apenas título.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título
    """
    if not comparison_table:
        return "## Comparação de Geração de Usinas Não Simuladas\n\nNenhum dado disponível para comparação."
    
    # Gerar título com informação de decks
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    n_decks = len(deck_names) if deck_names else 2
    
    if n_decks > 2:
        return f"## Comparação de Geração de Usinas Não Simuladas ({deck_summary})\n"
    return "## Comparação de Geração de Usinas Não Simuladas\n"


def format_reservatorio_inicial_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta para VariacaoReservatorioInicialTool: apenas título.
    A tabela e o gráfico são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título
    """
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    if not comparison_table:
        return "## Volume Inicial Percentual por Usina\n\nNenhum dado disponível."
    
    if n_decks > 2:
        return f"## Evolução do Volume Inicial Percentual por Usina ({deck_summary})"
    return "## Volume Inicial Percentual por Usina"


def format_restricao_eletrica_simple_comparison(
    comparison_table: List[Dict[str, Any]],
    deck_1_name: str,
    deck_2_name: str,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Formata resposta para RestricaoEletricaTool: apenas título.
    A tabela e os gráficos são renderizados pelo componente ComparisonView no frontend.
    Suporta N decks para comparação dinâmica.
    
    Args:
        comparison_table: Lista de dicionários com dados da comparação
        deck_1_name: Nome do deck 1 (fallback)
        deck_2_name: Nome do deck 2 (fallback)
        deck_names: Lista de nomes de decks (para N decks)
        
    Returns:
        String markdown com apenas o título
    """
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    if not comparison_table:
        return "## Restrições Elétricas\n\nNenhum dado disponível."
    
    # Detectar se há apenas uma restrição
    restricoes_unicas = set()
    for row in comparison_table:
        restricao = row.get("restricao", "")
        if restricao:
            restricoes_unicas.add(restricao)
    
    if len(restricoes_unicas) == 1:
        restricao_nome = list(restricoes_unicas)[0]
        if n_decks > 2:
            return f"## Restrições Elétricas - {restricao_nome} ({deck_summary})\n"
        return f"## Restrições Elétricas - {restricao_nome}\n"
    
    if n_decks > 2:
        return f"## Restrições Elétricas ({deck_summary})\n"
    return "## Restrições Elétricas\n"


def generate_fallback_comparison_response(
    query: str,
    deck_1_name: str,
    deck_2_name: str,
    tool_used: str,
    differences,
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Gera resposta de comparacao de fallback quando LLM falha.
    Segue o formato descritivo com resultado claro, sem conclusoes automaticas.
    Suporta N decks para comparação dinâmica.
    
    Args:
        query: Query original do usuário
        deck_1_name: Nome do primeiro deck (fallback)
        deck_2_name: Nome do último deck (fallback)
        tool_used: Nome da tool utilizada
        differences: Lista de diferenças encontradas
        deck_names: Lista de nomes de decks (para N decks)
    """
    n_decks = len(deck_names) if deck_names else 2
    deck_summary = _get_deck_names_summary(deck_names, deck_1_name, deck_2_name)
    
    response_parts = []
    
    if n_decks > 2:
        response_parts.append(f"## Análise Histórica ({deck_summary})\n\n")
    else:
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
    else:
        response_parts.append(f"### Diferencas Encontradas\n\n")
        response_parts.append(f"Nenhuma diferenca encontrada.\n\n")
    
    return "".join(response_parts)

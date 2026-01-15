"""
Registry de formatadores de comparação.
Mapeia tools para formatadores apropriados e fornece função consolidada para formatação.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List, Optional
from .base import ComparisonFormatter, DeckData, convert_legacy_result_to_decks_data
from .data_formatters.temporal_formatters import (
    ClastComparisonFormatter,
    CargaComparisonFormatter,
    VazoesComparisonFormatter,
    UsinasNaoSimuladasFormatter,
    LimitesIntercambioComparisonFormatter,
    RestricaoEletricaComparisonFormatter,
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
from .data_formatters.vazao_minima_formatters import (
    MudancasVazaoMinimaFormatter,
)
from .data_formatters.variacao_reservatorio_inicial_formatters import (
    VariacaoReservatorioInicialFormatter,
)


# Lista de formatadores (em ordem de prioridade - mais específicos primeiro)
FORMATTERS = [
    VariacaoReservatorioInicialFormatter(),  # Alta prioridade - muito específico para reservatório inicial por usina
    MudancasGeracoesTermicasFormatter(),  # Alta prioridade - muito específico para GTMIN
    MudancasVazaoMinimaFormatter(),  # Alta prioridade - muito específico para VAZMIN/VAZMINT
    ClastComparisonFormatter(),
    CargaComparisonFormatter(),
    VazoesComparisonFormatter(),
    UsinasNaoSimuladasFormatter(),
    RestricaoEletricaComparisonFormatter(),  # Restrições elétricas
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
    query: str,
    deck_display_names: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Formata a resposta para o frontend quando é uma comparação multi-deck.
    Usa formatadores especializados por tool para gerar visualizações otimizadas.
    Suporta N decks para comparação dinâmica.
    
    Args:
        tool_result: Resultado da tool de comparação (pode ter deck_1/deck_2 ou decks lista)
        tool_used: Nome da tool usada
        query: Query original do usuário
        deck_display_names: Mapeamento de nomes dos decks (opcional)
        
    Returns:
        Dict com final_response formatado e comparison_data
    """
    from newave_agent.app.config import safe_print
    
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
        format_vazao_minima_simple_comparison,
        format_reservatorio_inicial_simple_comparison,
        format_vazoes_dsvagua_simple_comparison,
        format_usinas_nao_simuladas_simple_comparison,
        format_restricao_eletrica_simple_comparison,
        generate_fallback_comparison_response
    )
    from .text_formatters.llm_structured import format_with_llm_structured
    from .text_formatters.llm_free import format_with_llm_free
    
    # Converter para formato de List[DeckData]
    decks_data = convert_legacy_result_to_decks_data(tool_result, deck_display_names)
    
    # IMPORTANTE: Extrair tool_used correto do resultado (prioridade sobre parâmetro)
    # O tool_result pode ter tool_used correto mesmo que o parâmetro esteja errado
    safe_print(f"[INTERPRETER] [COMPARISON] 🔍 Verificando tool_used - Parâmetro recebido: {tool_used}")
    safe_print(f"[INTERPRETER] [COMPARISON] 🔍 Campos no tool_result: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'N/A'}")
    
    tool_used_from_result = tool_result.get("tool_used")
    if tool_used_from_result:
        safe_print(f"[INTERPRETER] [COMPARISON] ✅ Tool usada extraída do resultado: {tool_used_from_result} (substituindo parâmetro: {tool_used})")
        tool_used = tool_used_from_result
    else:
        # Tentar extrair do primeiro deck
        if decks_data and len(decks_data) > 0:
            first_deck_result = decks_data[0].result
            if isinstance(first_deck_result, dict):
                tool_from_deck = first_deck_result.get("tool")
                if tool_from_deck:
                    safe_print(f"[INTERPRETER] [COMPARISON] ✅ Tool usada extraída do primeiro deck: {tool_from_deck} (substituindo parâmetro: {tool_used})")
                    tool_used = tool_from_deck
                else:
                    safe_print(f"[INTERPRETER] [COMPARISON] ⚠️ Campo 'tool' não encontrado no primeiro deck. Campos disponíveis: {list(first_deck_result.keys())}")
        else:
            safe_print(f"[INTERPRETER] [COMPARISON] ⚠️ Nenhum deck disponível para extrair tool_used")
    
    safe_print(f"[INTERPRETER] [COMPARISON] ✅ Tool usada final para formatação: {tool_used}")
    
    safe_print(f"[INTERPRETER] [COMPARISON] Decks convertidos: {len(decks_data)}")
    for idx, deck in enumerate(decks_data):
        safe_print(f"[INTERPRETER] [COMPARISON]   Deck {idx+1}: {deck.display_name} - success={deck.success}, error={deck.error}")
        if deck.result:
            safe_print(f"[INTERPRETER] [COMPARISON]     Campos no result: {list(deck.result.keys()) if isinstance(deck.result, dict) else 'N/A'}")
            if isinstance(deck.result, dict):
                data_count = len(deck.result.get("data", []))
                dados_por_sub = deck.result.get("dados_por_submercado", {})
                safe_print(f"[INTERPRETER] [COMPARISON]     data: {data_count} registros")
                safe_print(f"[INTERPRETER] [COMPARISON]     dados_por_submercado: {len(dados_por_sub) if isinstance(dados_por_sub, dict) else 0} submercados")
    
    # Verificar se há dados de comparação
    if not decks_data:
        if not tool_result.get("deck_1") and not tool_result.get("deck_2") and not tool_result.get("decks"):
            return {
                "final_response": "## Erro na Comparação\n\nNão foi possível obter dados de comparação.",
                "comparison_data": None
            }
    
    # Verificar erros em TODOS os decks (não apenas primeiro e último)
    failed_decks = [d for d in decks_data if not d.success]
    if failed_decks:
        # Se algum deck falhou, retornar mensagem de erro listando TODOS os decks com erro
        response_parts = []
        response_parts.append(f"## Erro na Comparação\n\n")
        for failed_deck in failed_decks:
            error_msg = failed_deck.error or "Erro desconhecido"
            response_parts.append(f"- **{failed_deck.display_name}**: {error_msg}\n")
        
        # Se TODOS os decks falharam, retornar erro completo
        if len(failed_decks) == len(decks_data):
            final_response = "".join(response_parts)
            return {
                "final_response": final_response,
                "comparison_data": {
                    "deck_1": tool_result.get("deck_1", {}),
                    "deck_2": tool_result.get("deck_2", {}),
                    "decks": tool_result.get("decks", []),
                    "tool_name": tool_used,
                    "query": query
                }
            }
        # Se apenas alguns decks falharam, FILTRAR os que falharam e continuar apenas com os bem-sucedidos
        safe_print(f"[INTERPRETER] [COMPARISON] ⚠️ {len(failed_decks)} de {len(decks_data)} decks falharam. Continuando apenas com os {len(decks_data) - len(failed_decks)} decks bem-sucedidos.")
        # Filtrar apenas os decks que tiveram sucesso
        decks_data = [d for d in decks_data if d.success]
    
    # Extrair nomes para compatibilidade (primeiro e último)
    if decks_data and len(decks_data) >= 2:
        deck_1_name = decks_data[0].display_name
        deck_2_name = decks_data[-1].display_name
    else:
        deck_1_name = tool_result.get("deck_1", {}).get("name", "Deck 1")
        deck_2_name = tool_result.get("deck_2", {}).get("name", "Deck 2")
    
    # Obter formatador apropriado
    # IMPORTANTE: Precisamos usar o resultado ORIGINAL da tool, não o resultado processado
    # O resultado original tem campos como dados_estruturais, dados_conjunturais, etc.
    if decks_data and len(decks_data) > 0:
        # decks_data[0].result já é o full_result preservado do MultiDeckComparisonTool
        deck_1_result = decks_data[0].result
        safe_print(f"[INTERPRETER] [COMPARISON] Usando resultado do primeiro deck para selecionar formatador")
        safe_print(f"[INTERPRETER] [COMPARISON] Tipo do resultado: {type(deck_1_result)}")
        safe_print(f"[INTERPRETER] [COMPARISON] Campos disponíveis no resultado: {list(deck_1_result.keys()) if isinstance(deck_1_result, dict) else 'N/A'}")
        if isinstance(deck_1_result, dict):
            # Verificar se tem dados_estruturais ou dados_conjunturais dentro
            if "dados_estruturais" in deck_1_result:
                dados_estrut = deck_1_result.get('dados_estruturais', [])
                safe_print(f"[INTERPRETER] [COMPARISON] ✅ dados_estruturais encontrado: {len(dados_estrut) if isinstance(dados_estrut, list) else 'N/A'} registros")
            if "dados_conjunturais" in deck_1_result:
                dados_conj = deck_1_result.get('dados_conjunturais', [])
                safe_print(f"[INTERPRETER] [COMPARISON] ✅ dados_conjunturais encontrado: {len(dados_conj) if isinstance(dados_conj, list) else 'N/A'} registros")
            # Verificar se tem full_result aninhado (problema antigo)
            if "full_result" in deck_1_result and isinstance(deck_1_result.get("full_result"), dict):
                safe_print(f"[INTERPRETER] [COMPARISON] ⚠️ AVISO: full_result aninhado detectado! Isso indica que a correção não foi aplicada corretamente.")
                nested_full = deck_1_result.get("full_result")
                if "dados_estruturais" in nested_full:
                    safe_print(f"[INTERPRETER] [COMPARISON]   dados_estruturais está dentro de full_result (deveria estar no nível superior)")
                if "dados_conjunturais" in nested_full:
                    safe_print(f"[INTERPRETER] [COMPARISON]   dados_conjunturais está dentro de full_result (deveria estar no nível superior)")
    else:
        deck_1_result = tool_result.get("deck_1", {}).get("full_result", tool_result.get("deck_1", {}))
        safe_print(f"[INTERPRETER] [COMPARISON] Usando deck_1 legado para selecionar formatador")
        safe_print(f"[INTERPRETER] [COMPARISON] Campos disponíveis no resultado: {list(deck_1_result.keys()) if isinstance(deck_1_result, dict) else 'N/A'}")
    
    # Debug: verificar quais formatadores podem processar
    safe_print(f"[INTERPRETER] [COMPARISON] Verificando formatadores para tool: {tool_used}")
    for fmt in FORMATTERS:
        can_format = fmt.can_format(tool_used, deck_1_result)
        safe_print(f"[INTERPRETER] [COMPARISON]   {fmt.__class__.__name__}: can_format={can_format}")
    
    formatter = get_formatter_for_tool(tool_used, deck_1_result)
    
    safe_print(f"[INTERPRETER] [COMPARISON] Usando formatador: {formatter.__class__.__name__}")
    safe_print(f"[INTERPRETER] [COMPARISON] Decks para comparar: {len(decks_data)}")
    
    # Validar se temos decks suficientes para comparação
    if len(decks_data) < 2:
        failed_deck_names = [d.display_name for d in decks_data if not d.success]
        if failed_deck_names:
            error_msg = f"## Erro na Comparação\n\nApenas {len(decks_data)} deck(s) disponível(is) para comparação. Os seguintes decks falharam:\n\n"
            for name in failed_deck_names:
                error_msg += f"- **{name}**: Falha ao processar\n"
            return {
                "final_response": error_msg,
                "comparison_data": {
                    "deck_1": tool_result.get("deck_1", {}),
                    "deck_2": tool_result.get("deck_2", {}),
                    "decks": tool_result.get("decks", []),
                    "tool_name": tool_used,
                    "query": query,
                    "error": "Menos de 2 decks disponíveis para comparação"
                }
            }
        else:
            return {
                "final_response": f"## Erro na Comparação\n\nApenas {len(decks_data)} deck(s) disponível(is) para comparação. É necessário pelo menos 2 decks.",
                "comparison_data": {
                    "deck_1": tool_result.get("deck_1", {}),
                    "deck_2": tool_result.get("deck_2", {}),
                    "decks": tool_result.get("decks", []),
                    "tool_name": tool_used,
                    "query": query,
                    "error": "Menos de 2 decks disponíveis para comparação"
                }
            }
    
    # Formatar comparação usando o novo método format_multi_deck_comparison
    deck_1_full = tool_result.get("deck_1", {}).get("full_result", {})
    deck_2_full = tool_result.get("deck_2", {}).get("full_result", {})
    
    # Usar format_multi_deck_comparison se temos decks_data
    if decks_data:
        formatted = formatter.format_multi_deck_comparison(decks_data, tool_used, query)
    else:
        # Fallback para método legado
        import inspect
        sig = inspect.signature(formatter.format_comparison)
        format_kwargs = {
            "result_dec": deck_1_full,
            "result_jan": deck_2_full,
            "tool_name": tool_used,
            "query": query
        }
        if "deck_1_name" in sig.parameters:
            format_kwargs["deck_1_name"] = deck_1_name
        if "deck_2_name" in sig.parameters:
            format_kwargs["deck_2_name"] = deck_2_name
        formatted = formatter.format_comparison(**format_kwargs)
    
    visualization_type = formatted.get("visualization_type", "llm_free")
    safe_print(f"[INTERPRETER] [COMPARISON] Visualization type: {visualization_type}")
    
    # Construir comparison_data com estrutura formatada (suporte N decks)
    deck_names = [d.name for d in decks_data] if decks_data else []
    deck_displays = [d.display_name for d in decks_data] if decks_data else [deck_1_name, deck_2_name]
    
    comparison_data = {
        # Campos legados para compatibilidade
        "deck_1": tool_result.get("deck_1", {}),
        "deck_2": tool_result.get("deck_2", {}),
        "deck_1_name": deck_1_name,
        "deck_2_name": deck_2_name,
        # Novos campos para N decks
        "deck_names": deck_names,
        "deck_displays": deck_displays,
        "deck_count": len(deck_displays),
        # Lista completa de dados brutos para N decks
        "decks_raw": [{
            "deck_name": d.name,  # DeckData usa 'name', não 'deck_name'
            "display_name": d.display_name,
            "data": d.result.get("data", []) if d.result else []
        } for d in decks_data] if decks_data else None,
        # Dados formatados
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
    if formatted.get("charts_by_restricao"):
        comparison_data["charts_by_restricao"] = formatted.get("charts_by_restricao")
    if formatted.get("comparison_by_type"):
        comparison_data["comparison_by_type"] = formatted.get("comparison_by_type")
    if formatted.get("comparison_by_usina"):
        comparison_data["comparison_by_usina"] = formatted.get("comparison_by_usina")
    if formatted.get("comparison_by_ree"):
        comparison_data["comparison_by_ree"] = formatted.get("comparison_by_ree")
    if formatted.get("stats"):
        comparison_data["stats"] = formatted.get("stats")
    if formatted.get("matrix_data"):
        matrix_data_value = formatted.get("matrix_data")
        safe_print(f"[INTERPRETER] [COMPARISON] Adicionando matrix_data ao comparison_data: {len(matrix_data_value) if isinstance(matrix_data_value, list) else 'N/A'} registros")
        if isinstance(matrix_data_value, list) and len(matrix_data_value) > 0:
            safe_print(f"[INTERPRETER] [COMPARISON] Primeiro registro matrix_data: {matrix_data_value[0]}")
        comparison_data["matrix_data"] = matrix_data_value
    
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
            tool_label,
            deck_names=deck_displays,  # Passar lista de decks para suporte N-deck
            tool_result=tool_result  # Passar tool_result para extrair informações reais
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
            deck_2_name,
            deck_names=deck_displays
        )
    elif tool_used == "MudancasVazaoMinimaTool":
        safe_print(f"[INTERPRETER] [COMPARISON] MudancasVazaoMinimaTool - formato simplificado (apenas tabela)")
        final_response = format_vazao_minima_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name
        )
    elif tool_used == "VariacaoReservatorioInicialTool":
        safe_print(f"[INTERPRETER] [COMPARISON] VariacaoReservatorioInicialTool - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data presente: {formatted.get('chart_data') is not None}")
        if formatted.get('chart_data'):
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data labels: {formatted.get('chart_data', {}).get('labels', [])}")
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data datasets: {len(formatted.get('chart_data', {}).get('datasets', []))}")
        final_response = format_reservatorio_inicial_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name
        )
    elif tool_used in ["VazoesTool", "DsvaguaTool"]:
        safe_print(f"[INTERPRETER] [COMPARISON] {tool_used} - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data presente: {formatted.get('chart_data') is not None}")
        if formatted.get('chart_data'):
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data labels: {len(formatted.get('chart_data', {}).get('labels', []))}")
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data datasets: {len(formatted.get('chart_data', {}).get('datasets', []))}")
        final_response = format_vazoes_dsvagua_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name,
            tool_used,
            deck_names=deck_displays
        )
    elif tool_used == "UsinasNaoSimuladasTool":
        safe_print(f"[INTERPRETER] [COMPARISON] UsinasNaoSimuladasTool - formato simplificado (apenas tabela e gráfico)")
        safe_print(f"[INTERPRETER] [COMPARISON] chart_data presente: {formatted.get('chart_data') is not None}")
        if formatted.get('chart_data'):
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data labels: {len(formatted.get('chart_data', {}).get('labels', []))}")
            safe_print(f"[INTERPRETER] [COMPARISON] chart_data datasets: {len(formatted.get('chart_data', {}).get('datasets', []))}")
        final_response = format_usinas_nao_simuladas_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name,
            deck_names=deck_displays
        )
    elif tool_used == "RestricaoEletricaTool":
        safe_print(f"[INTERPRETER] [COMPARISON] RestricaoEletricaTool - formato simplificado (apenas tabela e gráficos)")
        safe_print(f"[INTERPRETER] [COMPARISON] charts_by_restricao presente: {formatted.get('charts_by_restricao') is not None}")
        if formatted.get('charts_by_restricao'):
            safe_print(f"[INTERPRETER] [COMPARISON] charts_by_restricao: {len(formatted.get('charts_by_restricao', {}))} restrições")
        final_response = format_restricao_eletrica_simple_comparison(
            formatted.get("comparison_table", []),
            deck_1_name,
            deck_2_name,
            deck_names=deck_displays
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
    
    # Debug adicional para VariacaoReservatorioInicialTool
    if tool_used == "VariacaoReservatorioInicialTool":
        safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] VariacaoReservatorioInicialTool - comparison_data keys: {list(comparison_data.keys())}")
        safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] visualization_type: {comparison_data.get('visualization_type')}")
        safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] tool_name: {comparison_data.get('tool_name')}")
        safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] comparison_table length: {len(comparison_data.get('comparison_table', []))}")
        safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] chart_data presente: {comparison_data.get('chart_data') is not None}")
        if comparison_data.get('comparison_by_type'):
            safe_print(f"[INTERPRETER] [COMPARISON] [DEBUG] comparison_by_type keys: {list(comparison_data.get('comparison_by_type', {}).keys())}")
    
    return {
        "final_response": final_response,
        "comparison_data": comparison_data
    }

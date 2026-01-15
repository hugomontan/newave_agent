"""
Funções para sumarizar dados de decks para uso em comparações.
Suporta N decks para comparação dinâmica.
"""

from typing import Dict, Any, List, Optional
import json


def summarize_deck_data(deck_info: Dict[str, Any]) -> str:
    """
    Gera um resumo dos dados de um deck para passar ao LLM.
    Funciona com qualquer estrutura de dados (por periodo, por usina, por tipo, etc).
    """
    if not deck_info:
        return "Sem dados disponiveis"
    
    summary_parts = []
    
    # Resultado completo (principal fonte de dados)
    full_result = deck_info.get("full_result", {})
    
    if not full_result:
        return "Sem dados disponiveis"
    
    # Verificar se houve sucesso
    if not full_result.get("success", False):
        error = full_result.get("error", "Erro desconhecido")
        return f"ERRO: {error}"
    
    # Extrair dados de diferentes formatos possiveis
    # 1. dados_por_tipo (ModifOperacaoTool, etc)
    dados_por_tipo = full_result.get("dados_por_tipo", {})
    if dados_por_tipo:
        summary_parts.append("=== DADOS POR TIPO ===")
        for tipo, dados in dados_por_tipo.items():
            if isinstance(dados, list):
                summary_parts.append(f"\n[{tipo}] - {len(dados)} registros:")
                # Mostrar primeiros registros
                for record in dados[:5]:
                    summary_parts.append(f"  {json.dumps(record, ensure_ascii=False, default=str)}")
                if len(dados) > 5:
                    summary_parts.append(f"  ... e mais {len(dados) - 5} registros")
    
    # 2. dados_estruturais / dados_conjunturais (ClastValoresTool)
    for key in ["dados_estruturais", "dados_conjunturais"]:
        dados = full_result.get(key, [])
        if dados:
            summary_parts.append(f"\n=== {key.upper()} === ({len(dados)} registros)")
            for record in dados[:10]:
                summary_parts.append(f"  {json.dumps(record, ensure_ascii=False, default=str)}")
            if len(dados) > 10:
                summary_parts.append(f"  ... e mais {len(dados) - 10} registros")
    
    # 3. dados_expansoes (ExptOperacaoTool)
    dados_expansoes = full_result.get("dados_expansoes", [])
    if dados_expansoes:
        summary_parts.append(f"\n=== DADOS EXPANSOES === ({len(dados_expansoes)} registros)")
        for record in dados_expansoes[:10]:
            summary_parts.append(f"  {json.dumps(record, ensure_ascii=False, default=str)}")
        if len(dados_expansoes) > 10:
            summary_parts.append(f"  ... e mais {len(dados_expansoes) - 10} registros")
    
    # 4. data (formato padrao)
    data = full_result.get("data", [])
    if data and not dados_por_tipo and not dados_expansoes:
        summary_parts.append(f"\n=== DADOS === ({len(data)} registros)")
        for record in data[:10]:
            summary_parts.append(f"  {json.dumps(record, ensure_ascii=False, default=str)}")
        if len(data) > 10:
            summary_parts.append(f"  ... e mais {len(data) - 10} registros")
    
    # 5. Estatisticas gerais
    for key in ["stats_geral", "summary", "filtros"]:
        if key in full_result and full_result[key]:
            summary_parts.append(f"\n{key}: {json.dumps(full_result[key], ensure_ascii=False, default=str)}")
    
    return "\n".join(summary_parts) if summary_parts else "Sem dados disponiveis"


def summarize_multiple_decks(
    deck_results: List[Dict[str, Any]],
    deck_names: Optional[List[str]] = None
) -> str:
    """
    Gera um resumo combinado de múltiplos decks para passar ao LLM.
    
    Args:
        deck_results: Lista de resultados de cada deck
        deck_names: Lista de nomes de decks correspondentes
        
    Returns:
        String com resumo combinado de todos os decks
    """
    if not deck_results:
        return "Sem dados disponíveis"
    
    summary_parts = []
    summary_parts.append(f"=== ANÁLISE DE {len(deck_results)} DECKS ===\n")
    
    for i, result in enumerate(deck_results):
        name = deck_names[i] if deck_names and i < len(deck_names) else f"Deck {i+1}"
        summary_parts.append(f"\n--- {name} ---")
        
        deck_summary = summarize_deck_data({"full_result": result})
        # Limitar tamanho para não sobrecarregar o contexto
        if len(deck_summary) > 500:
            deck_summary = deck_summary[:500] + "..."
        summary_parts.append(deck_summary)
    
    # Adicionar estatísticas comparativas se possível
    if len(deck_results) >= 2:
        summary_parts.append("\n\n=== VISÃO COMPARATIVA ===")
        
        # Tentar extrair métricas comuns para comparação
        try:
            first_result = deck_results[0]
            last_result = deck_results[-1]
            
            # Verificar se há dados_estruturais (CVU)
            if "dados_estruturais" in first_result and "dados_estruturais" in last_result:
                first_data = first_result.get("dados_estruturais", [])
                last_data = last_result.get("dados_estruturais", [])
                summary_parts.append(f"\nDados estruturais: {len(first_data)} registros (primeiro) vs {len(last_data)} registros (último)")
            
            # Verificar se há dados_por_tipo (Modif)
            if "dados_por_tipo" in first_result and "dados_por_tipo" in last_result:
                first_tipos = set(first_result.get("dados_por_tipo", {}).keys())
                last_tipos = set(last_result.get("dados_por_tipo", {}).keys())
                
                added_tipos = last_tipos - first_tipos
                removed_tipos = first_tipos - last_tipos
                
                if added_tipos:
                    summary_parts.append(f"\nTipos adicionados: {', '.join(added_tipos)}")
                if removed_tipos:
                    summary_parts.append(f"\nTipos removidos: {', '.join(removed_tipos)}")
                    
        except Exception:
            pass  # Ignorar erros na análise comparativa
    
    return "\n".join(summary_parts)


def summarize_differences(differences) -> str:
    """
    Gera um resumo das diferencas para passar ao LLM.
    Retorna mensagem informativa se nao houver diferencas pre-calculadas.
    """
    if differences is None:
        return "(Diferencas nao pre-calculadas - compare os dados brutos de cada deck acima)"
    
    if not differences:
        return "Nenhuma diferenca encontrada nos dados temporais"
    
    summary_parts = []
    summary_parts.append(f"Total de {len(differences)} diferencas encontradas:\n")
    
    # Ordenar por diferenca percentual absoluta (maiores primeiro)
    sorted_diffs = sorted(differences, key=lambda x: abs(x.get("difference_percent", 0)), reverse=True)
    
    # Mostrar top 10 diferencas mais significativas
    for diff in sorted_diffs[:10]:
        period = diff.get("period", "N/A")
        val_1 = diff.get("deck_1_value", 0)
        val_2 = diff.get("deck_2_value", 0)
        diff_nominal = diff.get("difference", 0)
        diff_percent = diff.get("difference_percent", 0)
        
        summary_parts.append(
            f"- {period}: Deck1={val_1:.2f}, Deck2={val_2:.2f}, "
            f"Diff={diff_nominal:+.2f} ({diff_percent:+.2f}%)"
        )
    
    if len(differences) > 10:
        summary_parts.append(f"\n... e mais {len(differences) - 10} diferencas")
    
    return "\n".join(summary_parts)

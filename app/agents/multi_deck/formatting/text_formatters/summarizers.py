"""
Funções para sumarizar dados de decks para uso em comparações.
"""

from typing import Dict, Any
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

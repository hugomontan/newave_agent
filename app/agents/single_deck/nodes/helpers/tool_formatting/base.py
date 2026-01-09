"""
Formatação base de respostas de tools.
Para Single Deck Agent.
"""

from typing import Dict, Any
# Importações serão feitas dentro das funções para evitar imports circulares


def _format_generic_tool_response(tool_result: dict, tool_used: str) -> str:
    """
    Formata uma resposta genérica estruturada para tools sem formatter específico.
    Evita retornar dados crus.
    """
    response_parts = []
    response_parts.append(f"## ✅ Dados Processados\n\n")
    response_parts.append(f"*Processado pela tool: **{tool_used}***\n\n")
    
    # Resumo estruturado
    summary_text = format_tool_response_summary(tool_result, tool_used)
    if summary_text:
        # Remover a linha de status se existir
        summary_lines = summary_text.split('\n')
        summary_clean = [line for line in summary_lines if not line.startswith('Status:')]
        if summary_clean:
            response_parts.append("### Resumo\n\n")
            response_parts.append("\n".join(summary_clean).strip())
            response_parts.append("\n\n")
    
    # Tentar formatar dados principais se existirem
    data = tool_result.get("data", [])
    if data and isinstance(data, list) and len(data) > 0:
        response_parts.append("### Dados\n\n")
        response_parts.append(f"*Total de registros: {len(data)}*\n\n")
        
        # Tentar criar tabela se os dados tiverem estrutura similar
        if len(data) > 0 and isinstance(data[0], dict):
            # Pegar primeiras colunas disponíveis
            sample = data[0]
            cols = list(sample.keys())[:6]  # Limitar a 6 colunas
            
            if cols:
                response_parts.append("| " + " | ".join(cols) + " |\n")
                response_parts.append("|" + "|".join(["---"] * len(cols)) + "|\n")
                
                # Mostrar até 20 registros
                for record in data[:20]:
                    row = [str(record.get(col, ''))[:50] for col in cols]
                    response_parts.append("| " + " | ".join(row) + " |\n")
                
                if len(data) > 20:
                    response_parts.append(f"\n*Exibindo 20 de {len(data)} registros. Todos os dados estão disponíveis no JSON.*\n")
    
    # Outros campos importantes
    for key in ["dados_por_tipo", "dados_por_submercado", "dados_estruturais", "dados_conjunturais"]:
        if key in tool_result and tool_result[key]:
            value = tool_result[key]
            if isinstance(value, list) and len(value) > 0:
                response_parts.append(f"\n### {key.replace('_', ' ').title()}\n\n")
                response_parts.append(f"*Total: {len(value)} registros*\n\n")
            elif isinstance(value, dict) and len(value) > 0:
                response_parts.append(f"\n### {key.replace('_', ' ').title()}\n\n")
                response_parts.append(f"*Total: {len(value)} itens*\n\n")
    
    response_parts.append("\n---\n\n")
    response_parts.append("*Dados processados diretamente usando tool pré-programada.*\n")
    
    return "".join(response_parts)


def format_tool_response(tool_result: dict, tool_used: str) -> dict:
    """
    Formata o resultado de uma tool em resposta Markdown (método original, usado como base).
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        Dict com final_response formatado
    """
    if not tool_result.get("success"):
        # Caso especial: quando a tool requer escolha do usuário (ex: VAZMIN não encontrado, mas VAZMINT existe)
        if tool_result.get("requires_user_choice") and tool_result.get("choice_message"):
            choice_message = tool_result.get("choice_message")
            alternative_type = tool_result.get("alternative_type", "")
            
            response = f"## {choice_message}\n\n"
            
            return {
                "final_response": response,
                "requires_user_choice": True,
                "alternative_type": alternative_type,
                "original_error": tool_result.get("error")
            }
        
        error = tool_result.get("error", "Erro desconhecido")
        return {
            "final_response": f"## ❌ Erro na Tool {tool_used}\n\n{error}"
        }
    
    # Roteamento para formatação específica de cada tool
    if tool_used == "CargaMensalTool":
        from .specific_formatters import format_carga_mensal_response
        return format_carga_mensal_response(tool_result, tool_used)
    elif tool_used == "ClastValoresTool":
        from .specific_formatters import format_clast_valores_response
        # Passar query para detectar se é CVU e gerar gráfico
        query = tool_result.get("query", "")
        return format_clast_valores_response(tool_result, tool_used, query)
    elif tool_used == "ExptOperacaoTool":
        from .specific_formatters import format_expt_operacao_response
        return format_expt_operacao_response(tool_result, tool_used)
    elif tool_used == "ModifOperacaoTool":
        from .specific_formatters import format_modif_operacao_response
        return format_modif_operacao_response(tool_result, tool_used)
    
    # Formatação genérica para outras tools - NÃO retornar dados crus
    return {
        "final_response": _format_generic_tool_response(tool_result, tool_used)
    }


def format_tool_response_summary(tool_result: dict, tool_used: str) -> str:
    """
    Cria um resumo do resultado da tool para passar ao LLM.
    Mantém informações estruturadas mas de forma resumida.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        
    Returns:
        String com resumo formatado
    """
    summary_parts = []
    
    # Informações básicas
    if tool_result.get("success"):
        summary_parts.append(f"Status: ✅ Sucesso")
    else:
        summary_parts.append(f"Status: ❌ Erro - {tool_result.get('error', 'Erro desconhecido')}")
        return "\n".join(summary_parts)
    
    # Filtros aplicados
    filtros = tool_result.get("filtros")
    if filtros:
        summary_parts.append(f"\nFiltros aplicados:")
        if isinstance(filtros, dict):
            for key, value in filtros.items():
                summary_parts.append(f"  - {key}: {value}")
    
    # Estatísticas gerais
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        summary_parts.append(f"\nEstatísticas gerais:")
        summary_parts.append(f"  - Total de registros: {stats_geral.get('total_registros', 0)}")
        summary_parts.append(f"  - Total de tipos: {stats_geral.get('total_tipos', 0)}")
        tipos_encontrados = stats_geral.get('tipos_encontrados', [])
        if tipos_encontrados:
            summary_parts.append(f"  - Tipos encontrados: {', '.join(tipos_encontrados)}")
    
    # Dados por tipo (resumido)
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    if dados_por_tipo:
        summary_parts.append(f"\nDados por tipo de modificação:")
        for tipo, dados in dados_por_tipo.items():
            total = len(dados) if isinstance(dados, list) else 0
            summary_parts.append(f"  - {tipo}: {total} registro(s)")
            # Mostrar primeiros 3 registros como exemplo
            if isinstance(dados, list) and dados:
                summary_parts.append(f"    Exemplos:")
                for i, registro in enumerate(dados[:3]):
                    summary_parts.append(f"      {i+1}. {str(registro)[:200]}...")
    
    # Dados por submercado (se organizados separadamente)
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        summary_parts.append(f"\nDados organizados por submercado:")
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            total = info.get('total_registros', 0)
            summary_parts.append(f"  - {nome} (Código {codigo}): {total} registro(s)")
    
    # Summary da tool (para CargaMensalTool)
    summary = tool_result.get("summary")
    if summary:
        if summary.get("organizado_por_submercado"):
            summary_parts.append(f"\n⚠️ Dados organizados separadamente por submercado conforme solicitado")
        submercados = summary.get("submercados", [])
        if submercados:
            summary_parts.append(f"\nSubmercados disponíveis: {', '.join(map(str, submercados))}")
    
    # Outras seções importantes
    for key in ["desativacoes", "repotenciacoes", "expansoes", "indisponibilidades", 
                "dados_expansoes", "dados_estruturais", "dados_conjunturais", "data"]:
        if key in tool_result and tool_result[key]:
            value = tool_result[key]
            if isinstance(value, list):
                summary_parts.append(f"\n{key}: {len(value)} registro(s)")
            elif isinstance(value, dict):
                summary_parts.append(f"\n{key}: {len(value)} item(s)")
            else:
                summary_parts.append(f"\n{key}: {value}")
    
    return "\n".join(summary_parts)

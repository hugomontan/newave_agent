"""
Formatação de tools usando LLM.
Para Single Deck Agent.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from newave_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from newave_agent.app.utils.text_utils import clean_response_text
from .base import format_tool_response, format_tool_response_summary
from .helpers import format_restricao_eletrica_data
from ..prompts import TOOL_INTERPRETER_SYSTEM_PROMPT, TOOL_INTERPRETER_USER_PROMPT
import json


def format_tool_response_data_for_llm(tool_result: dict) -> str:
    """
    Formata os dados da tool em formato estruturado para o LLM.
    Usa JSON para manter estrutura, mas limita tamanho.
    
    Args:
        tool_result: Resultado da execução da tool
        
    Returns:
        String JSON resumida
    """
    # Criar estrutura resumida
    # IMPORTANTE: NÃO incluir stats_estrutural ou stats_conjuntural que contêm
    # custo_medio, custo_min, custo_max - essas estatísticas podem influenciar
    # o LLM a calcular médias, o que é proibido
    data_summary = {
        "success": tool_result.get("success", False),
        "filtros": tool_result.get("filtros"),
    }
    
    # Incluir stats_geral apenas se não contiver estatísticas calculadas
    stats_geral = tool_result.get("stats_geral")
    if stats_geral:
        # Criar cópia sem campos de estatísticas calculadas
        stats_geral_clean = {}
        for key, value in stats_geral.items():
            # Incluir apenas campos descritivos, não estatísticas calculadas
            if key not in ['custo_medio', 'custo_min', 'custo_max', 'valor_medio', 'valor_min', 'valor_max']:
                stats_geral_clean[key] = value
        if stats_geral_clean:
            data_summary["stats_geral"] = stats_geral_clean
    
    # Dados por submercado (prioridade quando disponível)
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        data_summary["dados_por_submercado"] = {}
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            dados = info.get('dados', [])
            # Limitar a 50 registros por submercado para não exceder tokens
            data_summary["dados_por_submercado"][codigo] = {
                "nome": nome,
                "dados": dados[:50],
                "total_registros": len(dados)
            }
            if len(dados) > 50:
                data_summary["dados_por_submercado"][codigo]["_limitado"] = True
    
    # Adicionar dados principais (limitado para não sobrecarregar)
    dados_por_tipo = tool_result.get("dados_por_tipo", {})
    if dados_por_tipo:
        data_summary["dados_por_tipo"] = {}
        for tipo, dados in dados_por_tipo.items():
            if isinstance(dados, list):
                # Limitar a 20 registros por tipo para não exceder tokens
                data_summary["dados_por_tipo"][tipo] = dados[:20]
                if len(dados) > 20:
                    data_summary["dados_por_tipo"][tipo + "_total"] = len(dados)
            else:
                data_summary["dados_por_tipo"][tipo] = dados
    
    # Dados de carga mensal (para CargaMensalTool)
    # IMPORTANTE: Incluir apenas dados mensais brutos, NÃO dados agregados anuais
    data = tool_result.get("data")
    if data:
        # Incluir TODOS os dados mensais (sem limite para carga mensal)
        # O LLM deve apresentar todos os meses, não valores anuais agregados
        data_summary["data"] = data
    
    # Dados por submercado (para CargaMensalTool quando organizado por submercado)
    # IMPORTANTE: Incluir dados mensais brutos, não agregados
    dados_por_submercado = tool_result.get("dados_por_submercado")
    if dados_por_submercado:
        data_summary["dados_por_submercado"] = {}
        for codigo, info in dados_por_submercado.items():
            nome = info.get('nome', f'Subsistema {codigo}')
            dados = info.get('dados', [])
            # Incluir TODOS os dados mensais (sem limite para carga mensal)
            data_summary["dados_por_submercado"][codigo] = {
                "nome": nome,
                "dados": dados,  # TODOS os dados mensais, sem limite
                "total_registros": len(dados)
            }
    
    # Dados estruturais e conjunturais (para ClastValoresTool)
    # IMPORTANTE: Incluir apenas os dados brutos, NÃO as estatísticas calculadas
    dados_estruturais = tool_result.get("dados_estruturais")
    if dados_estruturais:
        # Incluir TODOS os dados estruturais (sem limite para CVU)
        # O LLM deve apresentar todos os anos, não calcular médias
        data_summary["dados_estruturais"] = dados_estruturais
    
    dados_conjunturais = tool_result.get("dados_conjunturais")
    if dados_conjunturais:
        # Incluir dados conjunturais (limitado para não exceder tokens)
        data_summary["dados_conjunturais"] = dados_conjunturais[:50]
        if len(dados_conjunturais) > 50:
            data_summary["dados_conjunturais_total"] = len(dados_conjunturais)
    
    # Dados de restrições elétricas (para RestricaoEletricaTool)
    dados = tool_result.get("dados")
    if dados:
        # Formatar valores numéricos muito grandes em notação científica
        dados_formatados = format_restricao_eletrica_data(dados)
        data_summary["dados"] = dados_formatados[:50]  # Limitar a 50 registros
        if len(dados_formatados) > 50:
            data_summary["dados_total"] = len(dados_formatados)
    
    # Outras seções importantes
    for key in ["desativacoes", "repotenciacoes", "expansoes", "indisponibilidades"]:
        if key in tool_result:
            value = tool_result[key]
            if isinstance(value, list):
                data_summary[key] = value[:20]  # Limitar também
            else:
                data_summary[key] = value
    
    # IMPORTANTE: NUNCA incluir:
    # - aggregated: dados agregados anuais (para CargaMensalTool)
    # - stats_estrutural ou stats_conjuntural: estatísticas calculadas (para ClastValoresTool)
    # Esses dados podem influenciar o LLM a calcular médias ou usar valores agregados, o que é proibido
    
    try:
        return json.dumps(data_summary, indent=2, ensure_ascii=False, default=str)
    except:
        return str(data_summary)[:2000]  # Fallback


def format_tool_response_with_llm(tool_result: dict, tool_used: str, query: str) -> dict:
    """
    Formata o resultado de uma tool usando LLM para filtrar e focar na pergunta do usuário.
    
    Args:
        tool_result: Resultado da execução da tool
        tool_used: Nome da tool usada
        query: Query original do usuário
        
    Returns:
        Dict com final_response formatado e filtrado
    """
    if not tool_result.get("success"):
        # Caso especial: quando a tool requer escolha do usuário (ex: VAZMIN não encontrado, mas VAZMINT existe)
        if tool_result.get("requires_user_choice") and tool_result.get("choice_message"):
            # Usar format_tool_response que já trata esse caso especial
            # IMPORTANTE: Não processar com LLM quando requer escolha do usuário
            return format_tool_response(tool_result, tool_used)
        
        error = tool_result.get("error", "Erro desconhecido")
        return {
            "final_response": f"## ❌ Erro na Tool {tool_used}\n\n{error}"
        }
    
    # Verificar se há requires_user_choice mesmo com success=True (caso especial)
    if tool_result.get("requires_user_choice"):
        # Não processar com LLM, retornar resposta formatada diretamente
        return format_tool_response(tool_result, tool_used)
    
    try:
        safe_print(f"[TOOL INTERPRETER LLM] Gerando resposta focada para query: {query[:100]}")
        
        # Adicionar query ao tool_result para uso na formatação
        tool_result_with_query = tool_result.copy()
        tool_result_with_query["query"] = query
        
        # Primeiro, gerar resposta formatada básica usando métodos existentes
        formatted_response = format_tool_response(tool_result_with_query, tool_used)
        base_response = formatted_response.get("final_response", "")
        
        # Criar resumos para o LLM
        tool_result_summary = format_tool_response_summary(tool_result, tool_used)
        tool_result_data = format_tool_response_data_for_llm(tool_result)
        
        # Usar LLM para filtrar e focar
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.2  # Temperatura baixa para respostas mais consistentes
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", TOOL_INTERPRETER_SYSTEM_PROMPT),
            ("human", TOOL_INTERPRETER_USER_PROMPT)
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({
            "query": query,
            "tool_name": tool_used,
            "tool_result_summary": tool_result_summary,
            "tool_result_data": tool_result_data,
            "tool_result_formatted": base_response[:4000]  # Limitar tamanho da resposta formatada
        })
        
        final_response = getattr(response, 'content', None)
        
        if final_response:
            safe_print(f"[TOOL INTERPRETER LLM] ✅ Resposta focada gerada ({len(final_response)} caracteres)")
            # Limitar emojis na resposta
            final_response = clean_response_text(final_response, max_emojis=2)
            return {"final_response": final_response}
        else:
            # Fallback para resposta formatada original
            safe_print(f"[TOOL INTERPRETER LLM] ⚠️ LLM não retornou conteúdo, usando resposta formatada original")
            return formatted_response
            
    except Exception as e:
        safe_print(f"[TOOL INTERPRETER LLM] ❌ Erro ao processar com LLM: {e}")
        import traceback
        traceback.print_exc()
        # Fallback para formatação original em caso de erro
        return format_tool_response(tool_result, tool_used)

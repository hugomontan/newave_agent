"""
Node principal do interpreter que coordena a interpretação de resultados.
"""

from app.agents.state import AgentState
from app.config import safe_print
from app.utils.text_utils import clean_response_text
from .comparison import format_comparison_response
from .tool_formatting import format_tool_response_with_llm
from .code_execution.formatter import format_code_execution_response


def interpreter_node(state: AgentState) -> dict:
    """
    Node que interpreta os resultados e gera a resposta final formatada em Markdown.
    
    Prioridades:
    1. Se tool_result existe: processa resultado da tool
    2. Se rag_status == "fallback": retorna resposta de fallback
    3. Caso contrário: interpreta resultados de execução de código
    """
    try:
        # IMPORTANTE: Verificar resultado de tool PRIMEIRO
        # Se há tool_result, processar mesmo que haja disambiguation no state
        # (disambiguation pode estar no state de uma query anterior)
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[INTERPRETER] Processando resultado de tool: {tool_used}")
            safe_print(f"[INTERPRETER]   Success: {tool_result.get('success', False)}")
            
            # Verificar se é uma comparação multi-deck
            if tool_result.get("is_comparison"):
                safe_print(f"[INTERPRETER] ✅ Resultado é comparação multi-deck")
                query = state.get("query", "")
                # Formatar a resposta de comparação - isso já retorna comparison_data com chart_data
                result = format_comparison_response(tool_result, tool_used, query)
                safe_print(f"[INTERPRETER]   Resposta de comparação gerada")
                # Usar o comparison_data que vem do result (já tem chart_data formatado)
                return result
            
            safe_print(f"[INTERPRETER]   Data count: {len(tool_result.get('data', [])) if tool_result.get('data') else 0}")
            query = state.get("query", "")
            safe_print(f"[INTERPRETER]   Query original: {query[:100]}")
            result = format_tool_response_with_llm(tool_result, tool_used, query)
            safe_print(f"[INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            return result
        
        # Verificar se há disambiguation (apenas se não há tool_result)
        disambiguation = state.get("disambiguation")
        if disambiguation:
            # Para disambiguation, não retornar mensagem - o frontend já cria
            # Apenas retornar vazio para evitar duplicação
            safe_print(f"[INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}  # Vazio - frontend já cria a mensagem
        
        # Verificar se é um caso de fallback
        rag_status = state.get("rag_status", "success")
        
        if rag_status == "fallback":
            fallback_response = state.get("fallback_response", "")
            if fallback_response:
                fallback_response = clean_response_text(fallback_response, max_emojis=2)
                return {"final_response": fallback_response}
            
            # Fallback genérico se não houver resposta
            fallback_msg = """## Não foi possível processar sua solicitação

Não encontrei arquivos de dados adequados para responder sua pergunta.

### Sugestões de perguntas válidas:

- "Quais são as usinas hidrelétricas com maior potência instalada?"
- "Quais térmicas têm manutenção programada?"
- "Qual o custo das classes térmicas?"
- "Qual a demanda do submercado Sudeste?"
- "Quais são as vazões históricas do posto 1?"

### Dados disponíveis para consulta:

- **HIDR.DAT**: Cadastro de usinas hidrelétricas (potência, volumes, características)
- **MANUTT.DAT**: Manutenções de térmicas
- **CLAST.DAT**: Custos de classes térmicas
- **SISTEMA.DAT**: Demandas e intercâmbios entre submercados
- **VAZOES.DAT**: Séries históricas de vazões
"""
            fallback_msg = clean_response_text(fallback_msg, max_emojis=2)
            return {"final_response": fallback_msg}
        
        # Fluxo normal - interpretar resultados de execução
        execution_result = state.get("execution_result") or {}
        generated_code = state.get("generated_code", "")
        query = state.get("query", "")
        relevant_docs = state.get("relevant_docs", [])
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        return format_code_execution_response(
            execution_result=execution_result,
            generated_code=generated_code,
            query=query,
            relevant_docs=relevant_docs,
            retry_count=retry_count,
            max_retries=max_retries
        )
        
    except Exception as e:
        safe_print(f"[INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao interpretar resultados\n\nOcorreu um erro ao gerar a resposta: {str(e)}\n\nConsulte a saída da execução do código para ver os dados."
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}


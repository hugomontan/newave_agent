"""
Node que interpreta os resultados de comparação e gera a resposta final formatada (multi-deck).
"""

from typing import Dict, Any, Optional
from app.agents.multi_deck.state import MultiDeckState
from app.config import safe_print
from app.utils.text_utils import clean_response_text
from app.agents.multi_deck.nodes.helpers.tool_formatting.llm_formatter import format_tool_response_with_llm
from app.agents.multi_deck.nodes.helpers.code_execution.formatter import format_code_execution_response
from app.agents.multi_deck.nodes.helpers.comparison_formatter import format_comparison_response




def comparison_interpreter_node(state: MultiDeckState) -> dict:
    """
    Node que interpreta os resultados de comparação e gera a resposta final formatada.
    
    Prioridades:
    1. Se tool_result existe e é comparação: processa resultado da tool
    2. Se tool_result existe mas não é comparação: processa normalmente
    3. Caso contrário: interpreta resultados de execução de código
    """
    try:
        tool_result = state.get("tool_result")
        tool_used = state.get("tool_used")
        
        if tool_result:
            safe_print(f"[COMPARISON INTERPRETER] Processando resultado de tool: {tool_used}")
            safe_print(f"[COMPARISON INTERPRETER]   Success: {tool_result.get('success', False)}")
            
            # Verificar se é uma comparação multi-deck
            if tool_result.get("is_comparison"):
                safe_print(f"[COMPARISON INTERPRETER] ✅ Resultado é comparação multi-deck")
                query = state.get("query", "")
                tool_used_for_formatting = tool_result.get("tool_used", tool_used)
                
                # Usar format_comparison_response que já faz toda a lógica correta:
                # - Usa app.agents.multi_deck.formatters.registry.get_formatter_for_tool()
                # - Extrai full_result corretamente
                # - Reconstroi estruturas quando necessário
                # - Chama formatters originais com can_format() + get_priority()
                result = format_comparison_response(
                    tool_result,
                    tool_used_for_formatting,
                    query
                )
                
                safe_print(f"[COMPARISON INTERPRETER]   Resposta de comparação gerada usando formatters originais")
                return result
            
            # Tool não é comparação, processar normalmente
            safe_print(f"[COMPARISON INTERPRETER]   Data count: {len(tool_result.get('data', [])) if tool_result.get('data') else 0}")
            query = state.get("query", "")
            result = format_tool_response_with_llm(tool_result, tool_used, query)
            safe_print(f"[COMPARISON INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            return result
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[COMPARISON INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}
        
        # Verificar se é um caso de fallback
        rag_status = state.get("rag_status", "success")
        
        if rag_status == "fallback":
            fallback_response = state.get("fallback_response", "")
            if fallback_response:
                fallback_response = clean_response_text(fallback_response, max_emojis=2)
                return {"final_response": fallback_response}
            
            fallback_msg = """## Não foi possível processar sua solicitação

Não encontrei arquivos de dados adequados para responder sua pergunta de comparação.

### Sugestões de perguntas válidas:

- "Compare a carga mensal entre dezembro e janeiro"
- "Quais são as diferenças nos limites de intercâmbio?"
- "Compare os custos de classes térmicas"
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
        safe_print(f"[COMPARISON INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao interpretar resultados de comparação\n\nOcorreu um erro ao gerar a resposta: {str(e)}\n\nConsulte a saída da execução do código para ver os dados."
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg}


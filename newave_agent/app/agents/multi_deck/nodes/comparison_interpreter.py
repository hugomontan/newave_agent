"""
Node que interpreta os resultados de comparação e gera a resposta final formatada (multi-deck).
"""

from typing import Dict, Any, Optional
from newave_agent.app.agents.multi_deck.state import MultiDeckState
from newave_agent.app.config import safe_print
from newave_agent.app.utils.text_utils import clean_response_text
from newave_agent.app.agents.multi_deck.nodes.helpers.tool_formatting.llm_formatter import format_tool_response_with_llm
from newave_agent.app.agents.multi_deck.nodes.helpers.code_execution.formatter import format_code_execution_response
from newave_agent.app.agents.multi_deck.formatting.registry import format_comparison_response




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
                
                # Limpar query se vier de disambiguation (remover tag __DISAMBIG__)
                if query.startswith("__DISAMBIG__:"):
                    try:
                        parts = query.split(":", 2)
                        if len(parts) == 3:
                            query = parts[2].strip()  # Usar apenas a query original
                            safe_print(f"[COMPARISON INTERPRETER] Query limpa de disambiguation: {query}")
                    except Exception as e:
                        safe_print(f"[COMPARISON INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
                
                # Priorizar tool_used do resultado da tool (mais confiável)
                # Se não tiver, usar tool do state, e se não tiver, usar tool do primeiro deck
                tool_used_for_formatting = tool_result.get("tool_used")
                if not tool_used_for_formatting:
                    # Tentar extrair do primeiro deck
                    decks_list = tool_result.get("decks", [])
                    if decks_list and len(decks_list) > 0:
                        first_deck = decks_list[0]
                        deck_result = first_deck.get("full_result") or first_deck.get("result") or first_deck
                        tool_used_for_formatting = deck_result.get("tool") or tool_used
                    else:
                        tool_used_for_formatting = tool_used
                
                safe_print(f"[COMPARISON INTERPRETER] Tool usada para formatação: {tool_used_for_formatting}")
                
                # Obter display names dos decks do state (suporte N decks)
                deck_display_names = state.get("deck_display_names", {})
                
                # Usar format_comparison_response que já faz toda a lógica correta:
                # - Usa app.agents.multi_deck.formatters.registry.get_formatter_for_tool()
                # - Extrai full_result corretamente
                # - Reconstroi estruturas quando necessário
                # - Chama formatters originais com can_format() + get_priority()
                # - Suporta N decks para comparação dinâmica
                result = format_comparison_response(
                    tool_result,
                    tool_used_for_formatting,
                    query,
                    deck_display_names
                )
                
                safe_print(f"[COMPARISON INTERPRETER]   Resposta de comparação gerada usando formatters originais")
                return result
            
            # Tool não é comparação, processar normalmente
            safe_print(f"[COMPARISON INTERPRETER]   Data count: {len(tool_result.get('data', [])) if tool_result.get('data') else 0}")
            query = state.get("query", "")
            
            # Limpar query se vier de disambiguation (remover tag __DISAMBIG__)
            if query.startswith("__DISAMBIG__:"):
                try:
                    parts = query.split(":", 2)
                    if len(parts) == 3:
                        query = parts[2].strip()  # Usar apenas a query original
                        safe_print(f"[COMPARISON INTERPRETER] Query limpa de disambiguation: {query}")
                except Exception as e:
                    safe_print(f"[COMPARISON INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
            
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
        
        # Limpar query se vier de disambiguation (remover tag __DISAMBIG__)
        if query.startswith("__DISAMBIG__:"):
            try:
                parts = query.split(":", 2)
                if len(parts) == 3:
                    query = parts[2].strip()  # Usar apenas a query original
                    safe_print(f"[COMPARISON INTERPRETER] Query limpa de disambiguation: {query}")
            except Exception as e:
                safe_print(f"[COMPARISON INTERPRETER] ⚠️ Erro ao limpar query de disambiguation: {e}")
        
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


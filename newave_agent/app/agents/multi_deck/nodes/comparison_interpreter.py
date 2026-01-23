"""
Node que interpreta os resultados de comparação e gera a resposta final formatada (multi-deck).
"""

from typing import Dict, Any, Optional
from newave_agent.app.agents.multi_deck.state import MultiDeckState
from newave_agent.app.config import safe_print
from newave_agent.app.utils.text_utils import clean_response_text
from newave_agent.app.agents.multi_deck.nodes.helpers.tool_formatting.base import format_tool_response
from newave_agent.app.agents.multi_deck.formatting.registry import format_comparison_response




def comparison_interpreter_node(state: MultiDeckState) -> dict:
    """
    Node que formata os resultados de comparação e gera a resposta final.
    
    Prioridades:
    1. Se tool_result existe e é comparação: formata resultado da tool usando formatters
    2. Se tool_result existe mas não é comparação: formata normalmente
    3. Se disambiguation existe: retorna resposta vazia (frontend cria mensagem)
    4. Caso contrário: retorna mensagem informando que não há tool disponível
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
            
            result = format_tool_response(tool_result, tool_used)
            safe_print(f"[COMPARISON INTERPRETER]   Resposta gerada: {len(result.get('final_response', ''))} caracteres")
            return result
        
        # Verificar se há disambiguation
        disambiguation = state.get("disambiguation")
        if disambiguation:
            safe_print(f"[COMPARISON INTERPRETER] Processando disambiguation com {len(disambiguation.get('options', []))} opções")
            return {"final_response": ""}
        
        # Se não há tool_result e não há disambiguation, retornar mensagem
        safe_print(f"[COMPARISON INTERPRETER] Nenhuma tool disponível para processar a consulta de comparação")
        no_tool_msg = """## Nenhuma tool disponível para sua consulta de comparação

Não encontrei uma tool pré-programada que possa processar sua solicitação de comparação.

### Sugestões de perguntas válidas:

- "Compare a carga mensal entre dezembro e janeiro"
- "Quais são as diferenças nos limites de intercâmbio?"
- "Compare os custos de classes térmicas entre os decks"
- "Compare as vazões históricas entre os períodos"

### Tools disponíveis:

Consulte a documentação para ver todas as tools disponíveis para comparação de decks NEWAVE."""
        no_tool_msg = clean_response_text(no_tool_msg, max_emojis=2)
        return {"final_response": no_tool_msg, "comparison_data": None}
        
    except Exception as e:
        safe_print(f"[COMPARISON INTERPRETER ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = f"## Erro ao processar resultado de comparação\n\nOcorreu um erro ao formatar a resposta: {str(e)}"
        error_msg = clean_response_text(error_msg, max_emojis=2)
        return {"final_response": error_msg, "comparison_data": None}


"""
Node que verifica se a query pode ser atendida por uma tool pré-programada DECOMP.
Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
Se houver ambiguidade (múltiplas tools com scores similares), gera disambiguation.

Para Single Deck Agent DECOMP - sem lógica de comparação.
Usa funções compartilhadas de shared/agents/nodes/tool_router_base.py.
"""
from typing import Optional, Dict, Any, List
from backend.decomp.agents.single_deck.state import SingleDeckState
from backend.decomp.tools import get_available_tools
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import (
    SEMANTIC_MATCHING_ENABLED, 
    SEMANTIC_MATCH_THRESHOLD, 
    SEMANTIC_MATCH_MIN_SCORE, 
    USE_HYBRID_MATCHING,
    DISAMBIGUATION_SCORE_DIFF_THRESHOLD,
    DISAMBIGUATION_MAX_OPTIONS,
    DISAMBIGUATION_MIN_SCORE,
    safe_print
)
from backend.decomp.tools.semantic_matcher import find_best_tool_semantic, find_top_tools_semantic
from backend.core.utils.debug import write_debug_log
from backend.core.nodes.tool_router_base import (
    execute_tool as shared_execute_tool,
    generate_disambiguation_response,
    parse_disambiguation_query,
    find_tool_by_name,
    generate_plant_correction_followup,
    parse_plant_correction_query,
)


# Mapeamento de descrições curtas fixas para cada tool DECOMP
# Será preenchido quando as tools forem criadas
TOOL_SHORT_DESCRIPTIONS = {
    # Exemplo: "UsinasHidreletricasTool": "Dados de usinas hidrelétricas DECOMP",
    # Adicionar conforme tools forem criadas
}


def tool_router_node(state: SingleDeckState) -> dict:
    """
    Node que verifica se a query pode ser atendida por uma tool pré-programada DECOMP.
    Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
    
    Returns:
        Dict com:
        - tool_route: bool - True se tool foi executada, False caso contrário
        - tool_result: Dict - Resultado da tool (se tool_route=True)
        - tool_used: str - Nome da tool usada (se tool_route=True)
    """
    query = state.get("query", "")
    deck_path = state.get("deck_path", "")
    
    safe_print("[TOOL ROUTER DECOMP] ===== INÍCIO: tool_router_node (SINGLE DECK) =====")
    safe_print(f"[TOOL ROUTER DECOMP] Query: {query[:100]}")
    safe_print(f"[TOOL ROUTER DECOMP] Deck path: {deck_path}")
    
    if not deck_path:
        safe_print("[TOOL ROUTER DECOMP] ❌ Deck path não especificado")
        return {"tool_route": False}
    
    # Obter todas as tools disponíveis
    safe_print("[TOOL ROUTER DECOMP] Obtendo tools disponiveis...")
    try:
        tools = get_available_tools(deck_path)
        safe_print(f"[TOOL ROUTER DECOMP] [OK] {len(tools)} tools disponiveis")
    except Exception as e:
        safe_print(f"[TOOL ROUTER DECOMP] ❌ Erro ao obter tools: {e}")
        import traceback
        traceback.print_exc()
        return {"tool_route": False}
    
    # Função auxiliar para executar uma tool (usa função compartilhada)
    def _execute_tool(tool, tool_name: str, query_to_use: str = None, **kwargs):
        """Executa uma tool e retorna o resultado formatado."""
        if query_to_use is None:
            query_to_use = query
        result = shared_execute_tool(
            tool,
            tool_name,
            query_to_use,
            "[TOOL ROUTER DECOMP]",
            **kwargs,
        )
        
        # Adicionar follow-up de correção de usina se aplicável
        if result.get("tool_route"):
            tool_result = result.get("tool_result", {})
            if tool_result.get("selected_plant"):
                followup = generate_plant_correction_followup(tool_result, query_to_use)
                if followup:
                    result["plant_correction_followup"] = followup
                    safe_print(
                        f"[TOOL ROUTER DECOMP] ✅ Follow-up de correção de usina gerado "
                        f"(success={tool_result.get('success')})"
                    )
        
        return result
    
    # Detectar se a query veio de uma correção de usina
    # Formato: "__PLANT_CORR__:ToolName:codigo:original_query"
    is_plant_correction, correction_tool_name, plant_code, original_query_correction = parse_plant_correction_query(
        query
    )
    
    if is_plant_correction:
        safe_print("[TOOL ROUTER DECOMP] ✅ Query de correção de usina detectada")
        safe_print(f"[TOOL ROUTER DECOMP]   Tool: {correction_tool_name}")
        safe_print(f"[TOOL ROUTER DECOMP]   Código da usina: {plant_code}")
        safe_print(f"[TOOL ROUTER DECOMP]   Query original: {original_query_correction}")
        
        # Encontrar a tool correspondente
        selected_tool = find_tool_by_name(correction_tool_name, tools) if correction_tool_name else None
        if selected_tool and plant_code is not None:
            try:
                result = _execute_tool(
                    selected_tool,
                    correction_tool_name,
                    original_query_correction or query,
                    forced_plant_code=plant_code,
                )
                result["from_plant_correction"] = True
                result["plant_code_forced"] = plant_code
                safe_print("[TOOL ROUTER DECOMP] ✅ Tool executada com correção de usina")
                return result
            except Exception as e:
                safe_print(f"[TOOL ROUTER DECOMP] ❌ Erro ao executar tool com correção: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "tool_route": False,
                    "error": f"Erro ao executar tool com correção: {str(e)}",
                }
        else:
            safe_print(
                f"[TOOL ROUTER DECOMP] ❌ Tool {correction_tool_name} não encontrada ou código inválido "
                "para correção de usina"
            )
    
    # Estratégia de matching: Semantic matching (se habilitado) + Keyword matching (fallback)
    if SEMANTIC_MATCHING_ENABLED or USE_HYBRID_MATCHING:
        # Tentar semantic matching primeiro (top 5 para aplicar regra vazão conjunta vs unitária)
        safe_print("[TOOL ROUTER DECOMP] Tentando semantic matching...")
        try:
            top_tools = find_top_tools_semantic(
                query, tools, top_n=5, threshold=SEMANTIC_MATCH_THRESHOLD
            )
            if top_tools:
                best_tool, score = top_tools[0]
                tool_name = best_tool.get_name()
                query_lower = query.lower()
                conjunta_keywords = [
                    "conjunta", "conjunto", "somatorio", "somatório",
                    "conjuntas", "conjuntos", "somatórios",
                ]
                has_conjunta_keyword = any(k in query_lower for k in conjunta_keywords)
                # Prioridade: query com "conjunta" → forçar RestricoesVazaoHQConjuntaTool se estiver no top
                if has_conjunta_keyword:
                    for t, s in top_tools:
                        if t.get_name() == "RestricoesVazaoHQConjuntaTool":
                            best_tool, score = t, s
                            tool_name = "RestricoesVazaoHQConjuntaTool"
                            safe_print(
                                "[TOOL ROUTER DECOMP] Palavra-chave 'conjunta' detectada → "
                                "RestricoesVazaoHQConjuntaTool (restrição conjunta)"
                            )
                            break
                # Regra: query sem "conjunta/conjunto/somatorio" não deve preferir a tool conjunta
                # quando a unitária tem score próximo (ex.: "restricao vazao de baixo iguacu" -> unitária)
                elif (
                    tool_name == "RestricoesVazaoHQConjuntaTool"
                    and not has_conjunta_keyword
                ):
                    for t, s in top_tools[1:]:
                        if t.get_name() == "RestricoesVazaoHQTool":
                            best_tool, score = t, s
                            tool_name = "RestricoesVazaoHQTool"
                            safe_print(
                                "[TOOL ROUTER DECOMP] Regra vazão: query sem 'conjunta/conjunto' → "
                                "preferindo RestricoesVazaoHQTool (unitária)"
                            )
                            break
                safe_print(f"[TOOL ROUTER DECOMP] ✅ Semantic matching encontrou tool: {tool_name} (score: {score:.4f})")
                return _execute_tool(best_tool, tool_name)
            else:
                safe_print("[TOOL ROUTER DECOMP] ⚠️ Semantic matching não encontrou tool acima do threshold")
        except Exception as e:
            safe_print(f"[TOOL ROUTER DECOMP] ⚠️ Erro no semantic matching: {e}")
            import traceback
            traceback.print_exc()
    
    # Nenhuma tool encontrada pelo semantic matching
    safe_print("[TOOL ROUTER DECOMP] ⚠️ Nenhuma tool encontrada pelo semantic matching")
    safe_print("[TOOL ROUTER DECOMP] ===== FIM: tool_router_node (retornando tool_route=False) =====")
    return {
        "tool_route": False
    }

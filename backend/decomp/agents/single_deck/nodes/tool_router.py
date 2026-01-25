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
from backend.decomp.tools.semantic_matcher import find_best_tool_semantic
from backend.core.utils.debug import write_debug_log
from backend.core.nodes.tool_router_base import (
    execute_tool as shared_execute_tool,
    generate_disambiguation_response,
    parse_disambiguation_query,
    find_tool_by_name,
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
    def _execute_tool(tool, tool_name: str, query_to_use: str = None):
        """Executa uma tool e retorna o resultado formatado."""
        if query_to_use is None:
            query_to_use = query
        return shared_execute_tool(tool, tool_name, query_to_use, "[TOOL ROUTER DECOMP]")
    
    # Estratégia de matching: Semantic matching (se habilitado) + Keyword matching (fallback)
    if SEMANTIC_MATCHING_ENABLED or USE_HYBRID_MATCHING:
        # Tentar semantic matching primeiro
        safe_print("[TOOL ROUTER DECOMP] Tentando semantic matching...")
        try:
            semantic_result = find_best_tool_semantic(query, tools, threshold=SEMANTIC_MATCH_THRESHOLD)
            if semantic_result:
                best_tool, score = semantic_result
                tool_name = best_tool.get_name()
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

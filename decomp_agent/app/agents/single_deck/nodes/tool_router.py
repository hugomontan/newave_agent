"""
Node que verifica se a query pode ser atendida por uma tool pré-programada DECOMP.
Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
Se houver ambiguidade (múltiplas tools com scores similares), gera disambiguation.

Para Single Deck Agent DECOMP - sem lógica de comparação.
"""
from typing import Optional, Dict, Any, List
import os
import json as json_module
from decomp_agent.app.agents.single_deck.state import SingleDeckState
from decomp_agent.app.tools import get_available_tools
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import (
    SEMANTIC_MATCHING_ENABLED, 
    SEMANTIC_MATCH_THRESHOLD, 
    SEMANTIC_MATCH_MIN_SCORE, 
    USE_HYBRID_MATCHING,
    DISAMBIGUATION_SCORE_DIFF_THRESHOLD,
    DISAMBIGUATION_MAX_OPTIONS,
    DISAMBIGUATION_MIN_SCORE,
    safe_print
)
from decomp_agent.app.tools.semantic_matcher import find_best_tool_semantic
from shared.utils.debug import write_debug_log


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
    
    # Função auxiliar para executar uma tool e retornar resultado
    def _execute_tool(tool, tool_name: str, query_to_use: str = None):
        """Executa uma tool e retorna o resultado formatado."""
        if query_to_use is None:
            query_to_use = query
        safe_print(f"[TOOL ROUTER DECOMP] Executando tool {tool_name}...")
        
        try:
            result = tool.execute(query_to_use)
            
            if result.get("success"):
                safe_print(f"[TOOL ROUTER DECOMP] [OK] Tool {tool_name} executada com sucesso")
                data_count = len(result.get('data', [])) if result.get('data') else 0
                
                return {
                    "tool_result": result,
                    "tool_used": tool_name,
                    "tool_route": True,
                    "execution_result": {
                        "success": True,
                        "stdout": f"Tool {tool_name} executada com sucesso. {result.get('summary', {}).get('total_registros', data_count)} registros processados.",
                        "stderr": "",
                        "return_code": 0
                    }
                }
            else:
                safe_print(f"[TOOL ROUTER DECOMP] [AVISO] Tool {tool_name} executada mas retornou erro: {result.get('error')}")
                return {
                    "tool_result": result,
                    "tool_used": tool_name,
                    "tool_route": True,
                    "execution_result": {
                        "success": False,
                        "stdout": "",
                        "stderr": result.get("error", "Erro desconhecido na tool"),
                        "return_code": -1
                    }
                }
        except Exception as e:
            safe_print(f"[TOOL ROUTER DECOMP] [ERRO] Erro ao executar tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "tool_result": {"success": False, "error": str(e)},
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Erro ao executar tool: {str(e)}",
                    "return_code": -1
                }
            }
    
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

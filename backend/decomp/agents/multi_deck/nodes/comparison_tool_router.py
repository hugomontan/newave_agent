"""Comparison Tool Router para Multi-Deck Agent DECOMP."""
import os
import json as json_module
from typing import Optional, Dict, Any
from backend.decomp.agents.multi_deck.state import MultiDeckState
from backend.decomp.agents.multi_deck.tools import get_available_tools
from backend.decomp.config import (
    SEMANTIC_MATCHING_ENABLED,
    SEMANTIC_MATCH_THRESHOLD,
    SEMANTIC_MATCH_MIN_SCORE,
    USE_HYBRID_MATCHING,
    safe_print
)
from backend.decomp.tools.semantic_matcher import find_best_tool_semantic
from backend.core.nodes.tool_router_base import (
    generate_plant_correction_followup,
)


TOOL_SHORT_DESCRIPTIONS = {}

def comparison_tool_router_node(state: MultiDeckState) -> dict:
    query = state.get("query", "")
    selected_decks = state.get("selected_decks", [])
    deck_paths = state.get("deck_paths", {})
    
    safe_print("[TOOL ROUTER DECOMP MULTI] Query:", query[:100])
    
    if not selected_decks:
        return {"tool_route": False}
    
    try:
        tools = get_available_tools(selected_decks, deck_paths)
        
        # Função auxiliar para executar uma tool
        def _execute_tool(tool, tool_name: str):
            safe_print(f"[TOOL ROUTER DECOMP MULTI] Executando tool {tool_name}...")
            result = tool.execute(query)
            
            tool_result_dict = {
                "tool_result": result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": result.get("success", False),
                    "stdout": "",
                    "stderr": result.get("error", "") if not result.get("success", False) else "",
                },
            }
            
            # Adicionar follow-up de correção de usina se aplicável
            if result.get("selected_plant"):
                followup = generate_plant_correction_followup(result, query)
                if followup:
                    tool_result_dict["plant_correction_followup"] = followup
                    safe_print("[TOOL ROUTER DECOMP MULTI] ✅ Follow-up de correção de usina gerado")
            
            return tool_result_dict
        
        # Estratégia de matching: Apenas semantic matching
        if SEMANTIC_MATCHING_ENABLED:
            # Tentar semantic matching
            safe_print("[TOOL ROUTER DECOMP MULTI] Tentando semantic matching...")
            try:
                semantic_result = find_best_tool_semantic(query, tools, threshold=SEMANTIC_MATCH_THRESHOLD)
                if semantic_result:
                    best_tool, score = semantic_result
                    tool_name = best_tool.get_name()
                    safe_print(f"[TOOL ROUTER DECOMP MULTI] ✅ Semantic matching encontrou tool: {tool_name} (score: {score:.4f})")
                    return _execute_tool(best_tool, tool_name)
                else:
                    safe_print("[TOOL ROUTER DECOMP MULTI] ⚠️ Semantic matching não encontrou tool acima do threshold")
            except Exception as e:
                safe_print(f"[TOOL ROUTER DECOMP MULTI] ⚠️ Erro no semantic matching: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        safe_print(f"[TOOL ROUTER DECOMP MULTI] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    # Nenhuma tool encontrada pelo semantic matching
    safe_print("[TOOL ROUTER DECOMP MULTI] ⚠️ Nenhuma tool encontrada pelo semantic matching")
    return {"tool_route": False}

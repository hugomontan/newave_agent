"""Comparison Tool Router para Multi-Deck Agent DECOMP."""
import os
import json as json_module
from typing import Optional, Dict, Any
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from decomp_agent.app.agents.multi_deck.tools import get_available_tools
from decomp_agent.app.config import (
    SEMANTIC_MATCHING_ENABLED,
    SEMANTIC_MATCH_THRESHOLD,
    SEMANTIC_MATCH_MIN_SCORE,
    USE_HYBRID_MATCHING,
    safe_print
)
from decomp_agent.app.tools.semantic_matcher import find_best_tool_semantic

def _write_debug_log(data: dict):
    try:
        log_path = r'c:\Users\Inteli\OneDrive\Desktop\nw_multi\.cursor\debug.log'
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(data) + '\n')
    except Exception:
        pass

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
            return {
                "tool_result": result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {"success": result.get("success", False), "stdout": "", "stderr": ""}
            }
        
        # Estratégia de matching: Semantic matching (se habilitado) + Keyword matching (fallback)
        if SEMANTIC_MATCHING_ENABLED or USE_HYBRID_MATCHING:
            # Tentar semantic matching primeiro
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
                    # Se USE_HYBRID_MATCHING, tentar keyword matching como fallback
                    if USE_HYBRID_MATCHING:
                        safe_print("[TOOL ROUTER DECOMP MULTI] Tentando keyword matching como fallback...")
                        for tool in tools:
                            if tool.can_handle(query):
                                tool_name = tool.get_name()
                                safe_print(f"[TOOL ROUTER DECOMP MULTI] [OK] Tool {tool_name} pode processar a query!")
                                return _execute_tool(tool, tool_name)
            except Exception as e:
                safe_print(f"[TOOL ROUTER DECOMP MULTI] ⚠️ Erro no semantic matching: {e}")
                import traceback
                traceback.print_exc()
                # Em caso de erro, tentar keyword matching como fallback
                safe_print("[TOOL ROUTER DECOMP MULTI] Tentando keyword matching como fallback...")
                for tool in tools:
                    if tool.can_handle(query):
                        tool_name = tool.get_name()
                        safe_print(f"[TOOL ROUTER DECOMP MULTI] [OK] Tool {tool_name} pode processar a query!")
                        return _execute_tool(tool, tool_name)
        else:
            # Apenas keyword matching (comportamento original)
            safe_print("[TOOL ROUTER DECOMP MULTI] Verificando qual tool pode processar a query (keyword matching)...")
            for tool in tools:
                if tool.can_handle(query):
                    tool_name = tool.get_name()
                    safe_print(f"[TOOL ROUTER DECOMP MULTI] [OK] Tool {tool_name} pode processar a query!")
                    return _execute_tool(tool, tool_name)
        
    except Exception as e:
        safe_print(f"[TOOL ROUTER DECOMP MULTI] Erro: {e}")
        import traceback
        traceback.print_exc()
    
    safe_print("[TOOL ROUTER DECOMP MULTI] ⚠️ Nenhuma tool pode processar")
    return {"tool_route": False}

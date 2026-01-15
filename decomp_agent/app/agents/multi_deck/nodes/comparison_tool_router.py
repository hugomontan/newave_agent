"""Comparison Tool Router para Multi-Deck Agent DECOMP."""
import os
import json as json_module
from typing import Optional, Dict, Any
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from decomp_agent.app.agents.multi_deck.tools import get_available_tools
from decomp_agent.app.config import safe_print

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
        for tool in tools:
            if tool.can_handle(query):
                result = tool.execute(query)
                return {
                    "tool_result": result,
                    "tool_used": tool.get_name(),
                    "tool_route": True,
                    "execution_result": {"success": result.get("success", False), "stdout": "", "stderr": ""}
                }
    except Exception as e:
        safe_print(f"[TOOL ROUTER DECOMP MULTI] Erro: {e}")
    
    return {"tool_route": False}

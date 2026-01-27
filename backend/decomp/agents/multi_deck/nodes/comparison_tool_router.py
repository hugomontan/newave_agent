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
    parse_plant_correction_query,
    find_tool_by_name,
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

        # Primeiro, tratar queries de correção de usina (__PLANT_CORR__)
        is_plant_correction, correction_tool_name, plant_code, original_query_correction = parse_plant_correction_query(
            query
        )
        if is_plant_correction and correction_tool_name and plant_code is not None:
            safe_print("[TOOL ROUTER DECOMP MULTI] ✅ Query de correção de usina detectada")
            safe_print(f"[TOOL ROUTER DECOMP MULTI]   Tool (single-deck): {correction_tool_name}")
            safe_print(f"[TOOL ROUTER DECOMP MULTI]   Código da usina: {plant_code}")
            safe_print(f"[TOOL ROUTER DECOMP MULTI]   Query original: {original_query_correction}")

            # Mapear tool single-deck -> tool multi-deck correspondente
            single_to_multi_tool_map = {
                "CTUsinasTermelétricasTool": "CVUMultiDeckTool",
                "DisponibilidadeUsinaTool": "DisponibilidadeMultiDeckTool",
                "InflexibilidadeUsinaTool": "InflexibilidadeMultiDeckTool",
                "UHUsinasHidrelétricasTool": "VolumeInicialMultiDeckTool",
            }
            target_tool_name = single_to_multi_tool_map.get(correction_tool_name, correction_tool_name)

            selected_tool = find_tool_by_name(target_tool_name, tools)
            if selected_tool:
                query_to_use = original_query_correction or query
                safe_print(
                    f"[TOOL ROUTER DECOMP MULTI] Executando tool {target_tool_name} com código forçado {plant_code}"
                )
                # Executar tool multi-deck passando forced_plant_code
                result = selected_tool.execute(query_to_use, forced_plant_code=plant_code)

                tool_result_dict = {
                    "tool_result": result,
                    "tool_used": target_tool_name,
                    "tool_route": True,
                    "execution_result": {
                        "success": result.get("success", False),
                        "stdout": "",
                        "stderr": result.get("error", "") if not result.get("success", False) else "",
                    },
                }

                # Re-gerar follow-up de correção de usina com a nova usina selecionada, se aplicável
                if result.get("selected_plant"):
                    followup = generate_plant_correction_followup(result, query_to_use)
                    if followup:
                        tool_result_dict["plant_correction_followup"] = followup
                        safe_print("[TOOL ROUTER DECOMP MULTI] ✅ Follow-up de correção de usina gerado (correção)")

                tool_result_dict["from_plant_correction"] = True
                tool_result_dict["plant_code_forced"] = plant_code
                return tool_result_dict
            else:
                safe_print(
                    f"[TOOL ROUTER DECOMP MULTI] ❌ Tool {target_tool_name} não encontrada para correção de usina"
                )
        
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

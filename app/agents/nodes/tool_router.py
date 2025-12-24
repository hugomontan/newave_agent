"""
Node que verifica se a query pode ser atendida por uma tool pré-programada.
Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
"""
from app.agents.state import AgentState
from app.tools import get_available_tools
from app.tools.semantic_matcher import find_best_tool_semantic
from app.config import SEMANTIC_MATCHING_ENABLED, SEMANTIC_MATCH_THRESHOLD, SEMANTIC_MATCH_MIN_SCORE, USE_HYBRID_MATCHING


def tool_router_node(state: AgentState) -> dict:
    """
    Node que verifica se a query pode ser atendida por uma tool pré-programada.
    Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
    
    Returns:
        Dict com:
        - tool_route: bool - True se tool foi executada, False caso contrário
        - tool_result: Dict - Resultado da tool (se tool_route=True)
        - tool_used: str - Nome da tool usada (se tool_route=True)
    """
    query = state.get("query", "")
    deck_path = state.get("deck_path", "")
    
    print("[TOOL ROUTER] ===== INÍCIO: tool_router_node =====")
    print(f"[TOOL ROUTER] Query: {query[:100]}")
    print(f"[TOOL ROUTER] Deck path: {deck_path}")
    
    if not deck_path:
        print("[TOOL ROUTER] ❌ Deck path não especificado")
        return {"tool_route": False}
    
    # Obter todas as tools disponíveis
    print("[TOOL ROUTER] Obtendo tools disponíveis...")
    try:
        tools = get_available_tools(deck_path)
        print(f"[TOOL ROUTER] ✅ {len(tools)} tools disponíveis")
    except Exception as e:
        print(f"[TOOL ROUTER] ❌ Erro ao obter tools: {e}")
        import traceback
        traceback.print_exc()
        return {"tool_route": False}
    
    # Função auxiliar para executar uma tool e retornar resultado
    def _execute_tool(tool, tool_name: str):
        """Executa uma tool e retorna o resultado formatado."""
        print(f"[TOOL ROUTER] Executando tool {tool_name}...")
        result = tool.execute(query)
        
        if result.get("success"):
            print(f"[TOOL ROUTER] ✅ Tool {tool_name} executada com sucesso")
            print(f"[TOOL ROUTER] Registros retornados: {len(result.get('data', []))}")
            
            return {
                "tool_result": result,
                "tool_used": tool_name,
                "tool_route": True,  # Flag para pular coder/executor
                "execution_result": {
                    "success": True,
                    "stdout": f"Tool {tool_name} executada com sucesso. {result.get('summary', {}).get('total_registros', 0)} registros processados.",
                    "stderr": "",
                    "return_code": 0
                }
            }
        else:
            print(f"[TOOL ROUTER] ⚠️ Tool {tool_name} executada mas retornou erro: {result.get('error')}")
            # Mesmo com erro, a tool foi tentada, então não usar coder
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
    
    # 1. Tentar match semântico primeiro (se habilitado)
    if SEMANTIC_MATCHING_ENABLED:
        print("[TOOL ROUTER] 🔍 SEMANTIC MATCHING HABILITADO")
        print(f"[TOOL ROUTER]   Threshold (ranking): {SEMANTIC_MATCH_THRESHOLD:.3f}")
        print(f"[TOOL ROUTER]   Score mínimo para executar: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
        print(f"[TOOL ROUTER]   Regra: Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} → Tool executada | Score < {SEMANTIC_MATCH_MIN_SCORE:.3f} → Fluxo normal")
        print(f"[TOOL ROUTER]   Hybrid matching: {USE_HYBRID_MATCHING}")
        print("[TOOL ROUTER] Tentando match semântico...")
        try:
            semantic_result = find_best_tool_semantic(query, tools, threshold=SEMANTIC_MATCH_THRESHOLD)
            if semantic_result:
                tool, score = semantic_result
                tool_name = tool.get_name()
                print(f"[TOOL ROUTER] ✅ Match semântico bem-sucedido!")
                print(f"[TOOL ROUTER]   Tool selecionada: {tool_name}")
                print(f"[TOOL ROUTER]   Score de similaridade: {score:.4f}")
                print(f"[TOOL ROUTER]   Score mínimo: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
                print(f"[TOOL ROUTER]   Status: ✅ Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} (tool será executada)")
                return _execute_tool(tool, tool_name)
            else:
                print(f"[TOOL ROUTER] ⚠️ Match semântico: melhor score < {SEMANTIC_MATCH_MIN_SCORE:.3f}")
                print(f"[TOOL ROUTER]   → Nenhuma tool será executada, fluxo normal (coder/executor) assumirá")
                if USE_HYBRID_MATCHING:
                    print("[TOOL ROUTER]   → Continuando para keyword matching (fallback)...")
                else:
                    print("[TOOL ROUTER]   → Hybrid matching desabilitado, não tentando keyword matching")
        except Exception as e:
            print(f"[TOOL ROUTER] ⚠️ Erro no match semântico: {e}")
            import traceback
            traceback.print_exc()
            if USE_HYBRID_MATCHING:
                print("[TOOL ROUTER]   → Continuando para keyword matching (fallback após erro)...")
            # Continuar para fallback keyword matching
    
    # 2. Fallback para keyword matching (se híbrido habilitado ou se semântico desabilitado)
    if USE_HYBRID_MATCHING or not SEMANTIC_MATCHING_ENABLED:
        print("[TOOL ROUTER] Verificando qual tool pode processar a query (keyword matching)...")
        for tool in tools:
            tool_name = tool.get_name()
            print(f"[TOOL ROUTER] Testando tool: {tool_name}")
            
            try:
                if tool.can_handle(query):
                    print(f"[TOOL ROUTER] ✅ Tool {tool_name} pode processar a query!")
                    return _execute_tool(tool, tool_name)
                else:
                    print(f"[TOOL ROUTER] ❌ Tool {tool_name} não pode processar")
            except Exception as e:
                print(f"[TOOL ROUTER] ❌ Erro ao testar/executar tool {tool_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Nenhuma tool pode processar, continuar fluxo normal
    print("[TOOL ROUTER] ⚠️ Nenhuma tool pode processar, continuando fluxo normal")
    print("[TOOL ROUTER] ===== FIM: tool_router_node (retornando tool_route=False) =====")
    return {
        "tool_route": False
    }


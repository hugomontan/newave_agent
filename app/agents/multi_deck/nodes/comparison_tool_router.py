"""
Node que verifica se a query pode ser atendida por uma tool pré-programada.
Se sim, executa a tool diretamente. Se não, retorna para o fluxo normal.
Se houver ambiguidade (múltiplas tools com scores similares), gera disambiguation.

Para Multi-Deck Agent - com lógica de comparação (executa em ambos os decks).
"""
import os
import json as json_module
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from app.agents.multi_deck.state import MultiDeckState
from app.agents.multi_deck.tools import get_available_tools
from app.tools.semantic_matcher import find_best_tool_semantic, find_top_tools_semantic
from app.tools.base import NEWAVETool
from app.config import (
    SEMANTIC_MATCHING_ENABLED, 
    SEMANTIC_MATCH_THRESHOLD, 
    SEMANTIC_MATCH_MIN_SCORE, 
    USE_HYBRID_MATCHING,
    DISAMBIGUATION_SCORE_DIFF_THRESHOLD,
    DISAMBIGUATION_MAX_OPTIONS,
    DISAMBIGUATION_MIN_SCORE,
    safe_print
)

# Função auxiliar para escrever no log de debug de forma segura
def _write_debug_log(data: dict):
    """Escreve no arquivo de debug, criando o diretório se necessário."""
    try:
        log_path = r'c:\Users\Inteli\OneDrive\Desktop\nw_multi\.cursor\debug.log'
        log_dir = os.path.dirname(log_path)
        # Criar diretório se não existir
        os.makedirs(log_dir, exist_ok=True)
        # Escrever no arquivo
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(data) + '\n')
    except Exception:
        # Silenciosamente ignorar erros de log para não interromper o fluxo
        pass

# Mapeamento de descrições curtas fixas para cada tool
# Usado nas opções de disambiguation
# Cada descrição deve ser curta, clara e indicar o tipo de informação que a tool fornece
TOOL_SHORT_DESCRIPTIONS = {
    "ConfhdTool": "Dados de configuração da usina hidrelétrica",
    "ClastValoresTool": "Custos de classe atribuídos",
    "TermCadastroTool": "Dados cadastrais da usina térmica",
    "HidrCadastroTool": "Dados cadastrais da usina hidrelétrica",
    "VazoesTool": "Vazões históricas",
    "DsvaguaTool": "Desvios de água",
    "ModifOperacaoTool": "Modificações operacionais hídricas",
    "ExptOperacaoTool": "Modificações operacionais térmicas",
    "RestricaoEletricaTool": "Restrições elétricas",
    "LimitesIntercambioTool": "Limites de intercâmbio",
    "AgrintTool": "Agrupamentos de intercâmbio",
    "CargaMensalTool": "Carga mensal do sistema",
    "UsinasNaoSimuladasTool": "Geração de usinas não simuladas",
    "CadicTool": "Cargas e ofertas adicionais",
    "MultiDeckComparisonTool": "Comparação entre dois decks NEWAVE",
    "MudancasGeracoesTermicasTool": "Mudanças de geração térmica mínima",
    "VariacaoVolumesIniciaisTool": "Variação de volumes iniciais",
}


def comparison_tool_router_node(state: MultiDeckState) -> dict:
    """
    Node que verifica se a query pode ser atendida por uma tool pré-programada.
    Se sim, executa a tool diretamente em ambos os decks. Se não, retorna para o fluxo normal.
    
    Returns:
        Dict com:
        - tool_route: bool - True se tool foi executada, False caso contrário
        - tool_result: Dict - Resultado da tool (se tool_route=True)
        - tool_used: str - Nome da tool usada (se tool_route=True)
    """
    query = state.get("query", "")
    deck_path = state.get("deck_path", "")
    deck_december_path = state.get("deck_december_path", "")
    deck_january_path = state.get("deck_january_path", "")
    
    safe_print("[TOOL ROUTER] ===== INÍCIO: comparison_tool_router_node (MULTI-DECK) =====")
    safe_print(f"[TOOL ROUTER] Query: {query[:100]}")
    safe_print(f"[TOOL ROUTER] Deck path: {deck_path}")
    safe_print(f"[TOOL ROUTER] Deck Dezembro: {deck_december_path}")
    safe_print(f"[TOOL ROUTER] Deck Janeiro: {deck_january_path}")
    
    if not deck_path:
        safe_print("[TOOL ROUTER] ❌ Deck path não especificado")
        return {"tool_route": False}
    
    # Obter todas as tools disponíveis
    safe_print("[TOOL ROUTER] Obtendo tools disponiveis...")
    try:
        tools = get_available_tools(deck_path)
        safe_print(f"[TOOL ROUTER] [OK] {len(tools)} tools disponiveis")
    except Exception as e:
        safe_print(f"[TOOL ROUTER] ❌ Erro ao obter tools: {e}")
        import traceback
        traceback.print_exc()
        return {"tool_route": False}
    
    # Função auxiliar para executar uma tool e retornar resultado
    def _execute_tool(tool, tool_name: str, query_to_use: str = None):
        """Executa uma tool e retorna o resultado formatado."""
        if query_to_use is None:
            query_to_use = query
        safe_print(f"[TOOL ROUTER] Executando tool {tool_name}...")
        safe_print(f"[TOOL ROUTER]   Query usada: {query_to_use[:100]}")
        
        try:
            result = tool.execute(query_to_use)
            
            if result.get("success"):
                safe_print(f"[TOOL ROUTER] [OK] Tool {tool_name} executada com sucesso")
                data_count = len(result.get('data', [])) if result.get('data') else 0
                safe_print(f"[TOOL ROUTER] Registros retornados: {data_count}")
                
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
                safe_print(f"[TOOL ROUTER] [AVISO] Tool {tool_name} executada mas retornou erro: {result.get('error')}")
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
            safe_print(f"[TOOL ROUTER] [ERRO] Erro ao executar tool {tool_name}: {e}")
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
    
    # Função para executar tool em ambos os decks (modo comparison)
    def _execute_tool_comparison(tool_class, tool_name: str, query_to_use: str = None):
        """
        Executa uma tool em ambos os decks e retorna resultado de comparação.
        
        NÃO tenta calcular diferenças automaticamente - passa os dados brutos
        para o LLM interpretar livremente (pode ser por período, usina, tipo, etc).
        """
        if query_to_use is None:
            query_to_use = query
        
        safe_print(f"[TOOL ROUTER] [COMPARISON] Executando {tool_name} em ambos os decks...")
        safe_print(f"[TOOL ROUTER]   Query usada: {query_to_use[:100]}")
        
        try:
            safe_print(f"[TOOL ROUTER]   Deck Dezembro: {deck_december_path}")
            safe_print(f"[TOOL ROUTER]   Deck Janeiro: {deck_january_path}")
            
            # Executar em paralelo
            def execute_in_deck(deck_path: str) -> Dict[str, Any]:
                try:
                    tool_instance = tool_class(str(deck_path))
                    return tool_instance.execute(query_to_use)
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_dec = executor.submit(execute_in_deck, deck_december_path)
                future_jan = executor.submit(execute_in_deck, deck_january_path)
                result_dec = future_dec.result()
                result_jan = future_jan.result()
            
            safe_print(f"[TOOL ROUTER]   Dezembro: success={result_dec.get('success', False)}")
            safe_print(f"[TOOL ROUTER]   Janeiro: success={result_jan.get('success', False)}")
            
            # Construir resultado de comparação com dados BRUTOS
            # O LLM vai interpretar livremente - não forçamos cálculo de diferenças
            comparison_result = {
                "success": result_dec.get("success", False) or result_jan.get("success", False),
                "is_comparison": True,
                "tool_used": tool_name,
                "query": query_to_use,
                "deck_1": {
                    "name": "Dezembro 2025",
                    "success": result_dec.get("success", False),
                    "full_result": result_dec  # Resultado COMPLETO para o LLM interpretar
                },
                "deck_2": {
                    "name": "Janeiro 2026",
                    "success": result_jan.get("success", False),
                    "full_result": result_jan  # Resultado COMPLETO para o LLM interpretar
                },
                # Campos opcionais - serão None, LLM interpreta os dados brutos
                "differences": None,
                "chart_data": None
            }
            
            safe_print(f"[TOOL ROUTER] [OK] Comparação concluída - dados brutos passados ao LLM")
            
            return {
                "tool_result": comparison_result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": comparison_result["success"],
                    "stdout": f"Comparação executada com {tool_name}",
                    "stderr": "",
                    "return_code": 0 if comparison_result["success"] else -1
                }
            }
            
        except Exception as e:
            safe_print(f"[TOOL ROUTER] [ERRO] Erro na comparação: {e}")
            import traceback
            traceback.print_exc()
            return {
                "tool_result": {"success": False, "error": str(e), "is_comparison": True},
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Erro na comparação: {str(e)}",
                    "return_code": -1
                }
            }
    
    # Detectar se a query veio de uma escolha de disambiguation
    # Formato novo: "__DISAMBIG__:ToolName:original_query"
    # Formato antigo (compatibilidade): contém " - " ou nome direto da tool
    is_from_disambiguation = False
    disambiguation_tool_name = None
    original_query_from_disambiguation = None
    
    # Verificar formato novo: __DISAMBIG__:ToolName:original_query
    if query.startswith("__DISAMBIG__:"):
        try:
            parts = query.split(":", 2)  # ["__DISAMBIG__", "ToolName", "original_query"]
            if len(parts) == 3:
                disambiguation_tool_name = parts[1].strip()
                original_query_from_disambiguation = parts[2].strip()
                is_from_disambiguation = True
                safe_print(f"[TOOL ROUTER] Query detectada como escolha de disambiguation (formato novo)")
                safe_print(f"[TOOL ROUTER]   Tool: {disambiguation_tool_name}")
                safe_print(f"[TOOL ROUTER]   Query original: {original_query_from_disambiguation}")
        except Exception as e:
            safe_print(f"[TOOL ROUTER] ⚠️ Erro ao parsear formato de disambiguation: {e}")
    
    # Verificar formato antigo (compatibilidade): " - " na query
    if not is_from_disambiguation and " - " in query:
        is_from_disambiguation = True
        parts = query.split(" - ", 1)
        original_query_from_disambiguation = parts[0].strip()
        # Tentar identificar tool pelo contexto (fallback para compatibilidade)
        context = parts[1].strip() if len(parts) > 1 else ""
        safe_print(f"[TOOL ROUTER] Query detectada como escolha de disambiguation (formato antigo com ' - ')")
        safe_print(f"[TOOL ROUTER]   Query original: {original_query_from_disambiguation}")
        safe_print(f"[TOOL ROUTER]   Contexto: {context}")
    
    # Verificar se a query contém diretamente o nome de uma tool (compatibilidade)
    direct_tool_match = None
    if not is_from_disambiguation:
        tool_names = [t.get_name() for t in tools]
        for tool_name in tool_names:
            if tool_name.lower() in query.lower():
                query_words = query.lower().split()
                if tool_name.lower() in query_words or tool_name.lower() == query.lower().strip():
                    direct_tool_match = tool_name
                    original_query_from_disambiguation = query.replace(tool_name, "").strip() or query
                    is_from_disambiguation = True
                    disambiguation_tool_name = tool_name
                    break
    
    if is_from_disambiguation:
        # Executar tool diretamente usando tool_name identificado
        if disambiguation_tool_name:
            # Buscar tool pelo nome
            selected_tool = None
            for tool in tools:
                if tool.get_name() == disambiguation_tool_name:
                    selected_tool = tool
                    break
            
            if selected_tool:
                query_to_use = original_query_from_disambiguation if original_query_from_disambiguation else query
                safe_print(f"[TOOL ROUTER] ✅ Tool identificada diretamente: {disambiguation_tool_name}")
                safe_print(f"[TOOL ROUTER]   -> Executando tool diretamente sem semantic matching")
                safe_print(f"[TOOL ROUTER]   Query que será usada na tool: {query_to_use}")
                safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                
                # #region agent log
                _write_debug_log({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "G",
                    "location": "comparison_tool_router.py:disambiguation",
                    "message": "Tool identified from disambiguation, executing directly",
                    "data": {"tool_name": disambiguation_tool_name, "original_query": query_to_use[:50]},
                    "timestamp": int(__import__('time').time() * 1000)
                })
                # #endregion
                
                result = _execute_tool_comparison(selected_tool.__class__, disambiguation_tool_name, query_to_use)
                result["from_disambiguation"] = True
                safe_print(f"[TOOL ROUTER] [OK] Resultado da tool retornado: success={result.get('tool_result', {}).get('success', False)}")
                return result
            else:
                safe_print(f"[TOOL ROUTER] ❌ Tool {disambiguation_tool_name} não encontrada na lista de tools disponíveis")
                safe_print(f"[TOOL ROUTER]   Tools disponíveis: {[t.get_name() for t in tools]}")
        else:
            # Formato antigo - tentar identificar por contexto (compatibilidade)
            if " - " in query:
                parts = query.split(" - ", 1)
                original_query = parts[0].strip()
                context = parts[1].strip() if len(parts) > 1 else ""
                
                if context:
                    selected_tool = _identify_tool_from_context(context, tools)
                    if selected_tool:
                        tool_name = selected_tool.get_name()
                        safe_print(f"[TOOL ROUTER] ✅ Tool identificada pelo contexto (compatibilidade): {tool_name}")
                        safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                        result = _execute_tool_comparison(selected_tool.__class__, tool_name, original_query)
                        result["from_disambiguation"] = True
                        return result
                
                safe_print(f"[TOOL ROUTER] ⚠️ Não foi possível identificar tool, continuando com fluxo normal")
    
    # Verificar palavras-chave prioritárias
    safe_print("[TOOL ROUTER] 🔍 Verificando palavras-chave prioritárias...")
    query_lower = query.lower()
    
    priority_keywords = {
        "DsvaguaTool": [
            "desvios de água", "desvios de agua", "desvio de água", "desvio de agua",
            "desvios-agua", "desvios-água", "desvios_agua", "desvios_água",
            "desvio-agua", "desvio-água", "desvio_agua", "desvio_água"
        ],
        "ModifOperacaoTool": [
            "vazão mínima", "vazao minima", "vazão minima", "vazao mínima",
            "vazao-minima", "vazão-mínima", "vazao_minima", "vazão_mínima"
        ]
    }
    
    for tool_name, keywords in priority_keywords.items():
        if any(kw in query_lower for kw in keywords):
            safe_print(f"[TOOL ROUTER] ✅ PALAVRA-CHAVE PRIORITÁRIA DETECTADA para {tool_name}")
            safe_print(f"[TOOL ROUTER]   → Executando tool diretamente (sem semantic matching)")
            
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   Tool encontrada: {tool_name}")
                    safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                    result = _execute_tool_comparison(tool.__class__, tool_name)
                    safe_print(f"[TOOL ROUTER] ✅ Tool executada diretamente por palavra-chave prioritária")
                    return result
            
            safe_print(f"[TOOL ROUTER] ⚠️ Tool {tool_name} não encontrada na lista de tools disponíveis")
    
    # Tentar match semântico primeiro (se habilitado)
    if SEMANTIC_MATCHING_ENABLED:
        safe_print("[TOOL ROUTER] 🔍 SEMANTIC MATCHING HABILITADO")
        safe_print(f"[TOOL ROUTER]   Threshold para busca (disambiguation): {DISAMBIGUATION_MIN_SCORE:.3f}")
        safe_print(f"[TOOL ROUTER]   Threshold ranking (legado): {SEMANTIC_MATCH_THRESHOLD:.3f}")
        safe_print(f"[TOOL ROUTER]   Score mínimo para executar: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
        safe_print(f"[TOOL ROUTER]   Disambiguation diff threshold: {DISAMBIGUATION_SCORE_DIFF_THRESHOLD:.3f}")
        safe_print(f"[TOOL ROUTER]   Regra: Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} → Tool executada | Score < {SEMANTIC_MATCH_MIN_SCORE:.3f} → Fluxo normal")
        safe_print(f"[TOOL ROUTER]   Hybrid matching: {USE_HYBRID_MATCHING}")
        safe_print("[TOOL ROUTER] Tentando match semântico...")
        try:
            # Se veio de disambiguation, usar query original (sem " - contexto") para semantic matching
            query_for_semantic = query
            if is_from_disambiguation and " - " in query:
                parts = query.split(" - ", 1)
                query_for_semantic = parts[0].strip()
                safe_print(f"[TOOL ROUTER]   Query veio de disambiguation, usando query original para semantic matching: '{query_for_semantic}'")
            
            safe_print(f"[TOOL ROUTER]   Buscando top {DISAMBIGUATION_MAX_OPTIONS} tools com threshold >= {DISAMBIGUATION_MIN_SCORE:.3f}...")
            semantic_results = find_top_tools_semantic(
                query_for_semantic, 
                tools, 
                top_n=DISAMBIGUATION_MAX_OPTIONS,
                threshold=DISAMBIGUATION_MIN_SCORE
            )
            
            # #region agent log
            _write_debug_log({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "comparison_tool_router.py:375",
                "message": "Semantic matching called",
                "data": {"query_for_semantic": query_for_semantic[:50], "is_from_disambiguation": is_from_disambiguation, "results_count": len(semantic_results) if semantic_results else 0},
                "timestamp": int(__import__('time').time() * 1000)
            })
            # #endregion
            
            if semantic_results:
                top_tool, top_score = semantic_results[0]
                tool_name = top_tool.get_name()
                
                safe_print(f"[TOOL ROUTER] ✅ Top tool encontrada: {tool_name} (score: {top_score:.4f})")
                safe_print(f"[TOOL ROUTER]   Total de tools retornadas: {len(semantic_results)}")
                
                # #region agent log
                _write_debug_log({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "D",
                    "location": "comparison_tool_router.py:395",
                    "message": "Semantic matching results",
                    "data": {"top_tool": tool_name, "top_score": top_score, "is_from_disambiguation": is_from_disambiguation},
                    "timestamp": int(__import__('time').time() * 1000)
                })
                # #endregion
                
                # REGRA CRÍTICA: Se veio de disambiguation, SEMPRE executar a tool diretamente, sem verificar score ou ambiguidade
                if is_from_disambiguation:
                    original_query_for_tool = query_for_semantic if " - " in query else query
                    safe_print(f"[TOOL ROUTER] ✅ Query veio de disambiguation, executando tool diretamente (sem nova disambiguation)")
                    safe_print(f"[TOOL ROUTER]   Tool selecionada: {tool_name} (score: {top_score:.4f})")
                    safe_print(f"[TOOL ROUTER]   Query que sera usada na tool: {original_query_for_tool}")
                    safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                    # #region agent log
                    _write_debug_log({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "D",
                        "location": "comparison_tool_router.py:410",
                        "message": "Executing tool from disambiguation (always execute)",
                        "data": {"tool_name": tool_name, "score": top_score, "original_query": original_query_for_tool[:50]},
                        "timestamp": int(__import__('time').time() * 1000)
                    })
                    # #endregion
                    result = _execute_tool_comparison(top_tool.__class__, tool_name, original_query_for_tool)
                    result["from_disambiguation"] = True
                    return result
                
                # Para queries normais (não vêm de disambiguation), verificar score mínimo
                if top_score >= SEMANTIC_MATCH_MIN_SCORE:
                    # Verificar ambiguidade se houver 2+ tools
                    if len(semantic_results) >= 2:
                        second_tool, second_score = semantic_results[1]
                        score_diff = top_score - second_score
                        
                        safe_print(f"[TOOL ROUTER]  ANÁLISE DE AMBIGUIDADE:")
                        safe_print(f"[TOOL ROUTER]   1º lugar: {tool_name} (score: {top_score:.4f})")
                        safe_print(f"[TOOL ROUTER]   2º lugar: {second_tool.get_name()} (score: {second_score:.4f})")
                        safe_print(f"[TOOL ROUTER]   Diferença 1º-2º: {score_diff:.4f}")
                        safe_print(f"[TOOL ROUTER]   Threshold ambiguidade: {DISAMBIGUATION_SCORE_DIFF_THRESHOLD:.3f}")
                        
                        if score_diff < DISAMBIGUATION_SCORE_DIFF_THRESHOLD:
                            safe_print(f"[TOOL ROUTER] ⚠️ AMBIGUIDADE DETECTADA!")
                            safe_print(f"[TOOL ROUTER]   Diferença {score_diff:.4f} < {DISAMBIGUATION_SCORE_DIFF_THRESHOLD} → Gerando disambiguation")
                            safe_print(f"[TOOL ROUTER]   Gerando disambiguation com {len(semantic_results)} opções...")
                            return _generate_disambiguation_response(query_for_semantic, semantic_results)
                        else:
                            safe_print(f"[TOOL ROUTER] ✅ Sem ambiguidade (diferença {score_diff:.4f} >= {DISAMBIGUATION_SCORE_DIFF_THRESHOLD})")
                            safe_print(f"[TOOL ROUTER]   → Executando tool diretamente: {tool_name}")
                    else:
                        safe_print(f"[TOOL ROUTER] ✅ Apenas 1 tool encontrada, executando diretamente")
                    
                    # Sem ambiguidade, executar tool diretamente
                    safe_print(f"[TOOL ROUTER]   Status: [OK] Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} (tool sera executada)")
                    safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                    # #region agent log
                    _write_debug_log({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "D",
                        "location": "comparison_tool_router.py:445",
                        "message": "Executing tool from semantic matching (normal query)",
                        "data": {"tool_name": tool_name, "score": top_score},
                        "timestamp": int(__import__('time').time() * 1000)
                    })
                    # #endregion
                    return _execute_tool_comparison(top_tool.__class__, tool_name)
                else:
                    safe_print(f"[TOOL ROUTER] ⚠️ Match semântico: melhor score {top_score:.4f} < {SEMANTIC_MATCH_MIN_SCORE:.3f}")
                    safe_print(f"[TOOL ROUTER]   → Nenhuma tool será executada, fluxo normal (coder/executor) assumirá")
                    if USE_HYBRID_MATCHING:
                        safe_print("[TOOL ROUTER]   → Continuando para keyword matching (fallback)...")
            else:
                # Se veio de disambiguation mas não encontrou nenhuma tool, tentar com threshold 0.0
                if is_from_disambiguation:
                    safe_print(f"[TOOL ROUTER] ⚠️ Match semântico: nenhuma tool encontrada acima do threshold")
                    safe_print(f"[TOOL ROUTER]   -> Tentando com threshold 0.0 (fallback para disambiguation)...")
                    try:
                        semantic_results = find_top_tools_semantic(
                            query_for_semantic,
                            tools,
                            top_n=1,
                            threshold=0.0  # Sem threshold mínimo
                        )
                        if semantic_results:
                            top_tool, top_score = semantic_results[0]
                            tool_name = top_tool.get_name()
                            original_query_for_tool = query_for_semantic if " - " in query else query
                            safe_print(f"[TOOL ROUTER] ✅ Tool encontrada com threshold 0.0: {tool_name} (score: {top_score:.4f})")
                            safe_print(f"[TOOL ROUTER]   Query que sera usada na tool: {original_query_for_tool}")
                            safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                            # #region agent log
                            _write_debug_log({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "D",
                                "location": "comparison_tool_router.py:470",
                                "message": "Executing tool from disambiguation with threshold 0.0",
                                "data": {"tool_name": tool_name, "score": top_score, "original_query": original_query_for_tool[:50]},
                                "timestamp": int(__import__('time').time() * 1000)
                            })
                            # #endregion
                            result = _execute_tool_comparison(top_tool.__class__, tool_name, original_query_for_tool)
                            result["from_disambiguation"] = True
                            return result
                    except Exception as e:
                        safe_print(f"[TOOL ROUTER] ⚠️ Erro no fallback com threshold 0.0: {e}")
                
                safe_print(f"[TOOL ROUTER] ⚠️ Match semântico: nenhuma tool encontrada acima do threshold")
                safe_print(f"[TOOL ROUTER]   → Nenhuma tool será executada, fluxo normal (coder/executor) assumirá")
                if USE_HYBRID_MATCHING:
                    safe_print("[TOOL ROUTER]   → Continuando para keyword matching (fallback)...")
        except Exception as e:
            safe_print(f"[TOOL ROUTER] ⚠️ Erro no match semântico: {e}")
            import traceback
            traceback.print_exc()
            if USE_HYBRID_MATCHING:
                safe_print("[TOOL ROUTER]   → Continuando para keyword matching (fallback após erro)...")
    
    # Fallback para keyword matching
    if USE_HYBRID_MATCHING or not SEMANTIC_MATCHING_ENABLED:
        safe_print("[TOOL ROUTER] Verificando qual tool pode processar a query (keyword matching)...")
        for tool in tools:
            tool_name = tool.get_name()
            safe_print(f"[TOOL ROUTER] Testando tool: {tool_name}")
            
            try:
                if tool.can_handle(query):
                    safe_print(f"[TOOL ROUTER] [OK] Tool {tool_name} pode processar a query!")
                    safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                    return _execute_tool_comparison(tool.__class__, tool_name)
                else:
                    safe_print(f"[TOOL ROUTER] [X] Tool {tool_name} nao pode processar")
            except Exception as e:
                safe_print(f"[TOOL ROUTER] ❌ Erro ao testar/executar tool {tool_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Nenhuma tool pode processar, continuar fluxo normal
    safe_print("[TOOL ROUTER] ⚠️ Nenhuma tool pode processar, continuando fluxo normal")
    safe_print("[TOOL ROUTER] ===== FIM: comparison_tool_router_node (retornando tool_route=False) =====")
    return {
        "tool_route": False
    }


def _generate_disambiguation_response(
    query: str,
    top_tools: list[tuple]
) -> dict:
    """
    Gera resposta de disambiguation com descrições curtas fixas.
    Cada opção direciona diretamente para uma tool específica.
    
    Args:
        query: Query original do usuário
        top_tools: Lista de tuplas (tool, score) ordenadas por score
        
    Returns:
        Dict com final_response e disambiguation
    """
    from app.config import DISAMBIGUATION_MAX_OPTIONS
    
    safe_print("[TOOL ROUTER] Gerando resposta de disambiguation com descrições fixas...")
    
    # Usar apenas a função simplificada (sem LLM)
    return _create_fallback_disambiguation(query, top_tools)


def _create_fallback_disambiguation(
    query: str,
    top_tools: list[tuple]
) -> dict:
    """
    Cria disambiguation usando mapeamento de descrições curtas fixas.
    Cada opção usa formato especial que permite execução direta da tool.
    
    Args:
        query: Query original do usuário
        top_tools: Lista de tuplas (tool, score) ordenadas por score
        
    Returns:
        Dict com final_response e disambiguation
    """
    from app.config import DISAMBIGUATION_MAX_OPTIONS
    
    safe_print("[TOOL ROUTER] Criando disambiguation com opções fixas...")
    
    # Limitar a máximo de opções
    tools_to_show = top_tools[:DISAMBIGUATION_MAX_OPTIONS]
    
    # Pergunta padrão
    question = "Preciso de mais informações, escolha a opção que se refere melhor a sua consulta:"
    
    safe_print(f"[TOOL ROUTER] Query original: {query}")
    safe_print(f"[TOOL ROUTER] Tools candidatas: {[t.get_name() for t, _ in tools_to_show]}")
    
    options = []
    for idx, (tool, score) in enumerate(tools_to_show, 1):
        tool_name = tool.get_name()
        # Usar descrição curta fixa do mapeamento
        friendly_desc = TOOL_SHORT_DESCRIPTIONS.get(tool_name, tool_name)
        
        # Criar query no formato especial: __DISAMBIG__:ToolName:original_query
        # Isso permite que o backend identifique diretamente a tool sem novo semantic matching
        special_query = f"__DISAMBIG__:{tool_name}:{query}"
        
        safe_print(f"[TOOL ROUTER]   Opção {idx}: {tool_name} -> '{friendly_desc}'")
        safe_print(f"[TOOL ROUTER]     Query especial: {special_query[:80]}")
        
        options.append({
            "label": friendly_desc,
            "query": special_query,  # Formato especial para identificação direta
            "tool_name": tool_name,
            "original_query": query  # Preservar query original
        })
    
    safe_print(f"[TOOL ROUTER] ✅ Disambiguation criada com {len(options)} opções")
    
    return {
        "tool_route": False,
        "final_response": "",  # Vazio - frontend cria a mensagem
        "disambiguation": {
            "type": "tool_selection",
            "question": question,
            "options": options,
            "original_query": query
        }
    }


def _identify_tool_from_context(context: str, tools: list[NEWAVETool]) -> Optional[NEWAVETool]:
    """
    Identifica qual tool corresponde ao contexto escolhido pelo usuário.
    Usado quando a query veio de uma escolha de disambiguation.
    
    Args:
        context: Contexto após o " - " na query expandida (em lowercase)
        tools: Lista de tools disponíveis
        
    Returns:
        Tool correspondente ou None se não encontrada
    """
    context_to_tool = {
        "dados cadastrais físicos da usina": "HidrCadastroTool",
        "configuração ree e status": "ConfhdTool",
        "vazões históricas": "VazoesTool",
        "desvios de água": "DsvaguaTool",
        "modificações operacionais hídricas": "ModifOperacaoTool",
        "modificações operacionais térmicas": "ExptOperacaoTool",
        "restrições elétricas": "RestricaoEletricaTool",
        "limites de intercâmbio": "LimitesIntercambioTool",
        "agrupamentos de intercâmbio": "AgrintTool",
        "carga mensal do sistema": "CargaMensalTool",
        "geração de usinas não simuladas": "UsinasNaoSimuladasTool",
        "custos de classes térmicas": "ClastValoresTool",
        "cargas e ofertas adicionais": "CadicTool",
        "cadastro de usinas termoelétricas": "TermCadastroTool",
        "comparação entre dois decks": "MultiDeckComparisonTool",
        "mudanças de geração térmica mínima": "MudancasGeracoesTermicasTool",
        "variação de volumes iniciais": "VariacaoVolumesIniciaisTool",
    }
    
    context_normalized = context.strip().lower()
    
    safe_print(f"[TOOL ROUTER]   Buscando tool para contexto: '{context_normalized}'")
    safe_print(f"[TOOL ROUTER]   Contextos disponíveis: {list(context_to_tool.keys())}")
    
    tool_names = [t.get_name() for t in tools]
    for tool_name in tool_names:
        if tool_name.lower() == context_normalized or tool_name.lower() in context_normalized.split():
            safe_print(f"[TOOL ROUTER]   ✅ Contexto contém nome da tool diretamente: {tool_name}")
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                    return tool
    
    tool_name = context_to_tool.get(context_normalized)
    if tool_name:
        safe_print(f"[TOOL ROUTER]   ✅ Match exato encontrado: {tool_name}")
        for tool in tools:
            if tool.get_name() == tool_name:
                safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                return tool
    
    for key, tool_name in context_to_tool.items():
        key_normalized = key.lower()
        if key_normalized in context_normalized or context_normalized in key_normalized:
            safe_print(f"[TOOL ROUTER]   ✅ Match parcial encontrado: {tool_name} (chave: '{key}')")
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                    return tool
    
    context_words = set(context_normalized.split())
    
    best_match = None
    best_score = 0
    
    for key, tool_name in context_to_tool.items():
        key_normalized = key.lower()
        key_words = set(key_normalized.split())
        
        common_words = context_words.intersection(key_words)
        if len(common_words) > 0:
            score = len(common_words) / max(len(key_words), 1)
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = (tool_name, key)
    
    if best_match:
        tool_name, matched_key = best_match
        safe_print(f"[TOOL ROUTER]   ✅ Match por palavras-chave encontrado: {tool_name} (chave: '{matched_key}', score: {best_score:.2f})")
        for tool in tools:
            if tool.get_name() == tool_name:
                safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                return tool
    
    safe_print(f"[TOOL ROUTER]   ❌ Nenhuma tool encontrada para contexto: '{context_normalized}'")
    safe_print(f"[TOOL ROUTER]   Palavras do contexto: {context_words}")
    return None

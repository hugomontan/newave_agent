"""
Node que verifica se a query pode ser atendida por uma tool pre-programada.
Se sim, executa a tool diretamente. Se nao, retorna para o fluxo normal.
Se houver ambiguidade (multiplas tools com scores similares), gera disambiguation.

No modo "comparison", a tool selecionada e executada em ambos os decks (dezembro e janeiro)
e os resultados sao retornados para o interpreter formatar a comparacao.
"""
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from app.agents.state import AgentState
from app.tools import get_available_tools
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
    analysis_mode = state.get("analysis_mode", "single")
    
    safe_print("[TOOL ROUTER] ===== INÍCIO: tool_router_node =====")
    safe_print(f"[TOOL ROUTER] Query: {query[:100]}")
    safe_print(f"[TOOL ROUTER] Deck path: {deck_path}")
    safe_print(f"[TOOL ROUTER] Analysis mode: {analysis_mode}")
    
    if not deck_path:
        safe_print("[TOOL ROUTER] ❌ Deck path não especificado")
        return {"tool_route": False}
    
    # Obter todas as tools disponíveis
    safe_print("[TOOL ROUTER] Obtendo tools disponiveis...")
    try:
        tools = get_available_tools(deck_path, analysis_mode)
        safe_print(f"[TOOL ROUTER] [OK] {len(tools)} tools disponiveis (modo: {analysis_mode})")
    except Exception as e:
        safe_print(f"[TOOL ROUTER] ❌ Erro ao obter tools: {e}")
        import traceback
        traceback.print_exc()
        return {"tool_route": False}
    
    # Funcao auxiliar para executar uma tool e retornar resultado
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
                    "tool_route": True,  # Flag para pular coder/executor
                    "execution_result": {
                        "success": True,
                        "stdout": f"Tool {tool_name} executada com sucesso. {result.get('summary', {}).get('total_registros', data_count)} registros processados.",
                        "stderr": "",
                        "return_code": 0
                    }
                }
            else:
                safe_print(f"[TOOL ROUTER] [AVISO] Tool {tool_name} executada mas retornou erro: {result.get('error')}")
                # Mesmo com erro, a tool foi tentada, entao nao usar coder
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
    
    # Funcao para executar tool em ambos os decks (modo comparison)
    def _execute_tool_comparison(tool_class, tool_name: str, query_to_use: str = None):
        """
        Executa uma tool em ambos os decks e retorna resultado de comparacao.
        
        NAO tenta calcular diferencas automaticamente - passa os dados brutos
        para o LLM interpretar livremente (pode ser por periodo, usina, tipo, etc).
        """
        from app.utils.deck_loader import get_december_deck_path, get_january_deck_path
        
        if query_to_use is None:
            query_to_use = query
        
        safe_print(f"[TOOL ROUTER] [COMPARISON] Executando {tool_name} em ambos os decks...")
        safe_print(f"[TOOL ROUTER]   Query usada: {query_to_use[:100]}")
        
        try:
            # Obter caminhos dos decks
            deck_december = get_december_deck_path()
            deck_january = get_january_deck_path()
            
            safe_print(f"[TOOL ROUTER]   Deck Dezembro: {deck_december}")
            safe_print(f"[TOOL ROUTER]   Deck Janeiro: {deck_january}")
            
            # Executar em paralelo
            def execute_in_deck(deck_path: str) -> Dict[str, Any]:
                try:
                    tool_instance = tool_class(str(deck_path))
                    return tool_instance.execute(query_to_use)
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_dec = executor.submit(execute_in_deck, deck_december)
                future_jan = executor.submit(execute_in_deck, deck_january)
                result_dec = future_dec.result()
                result_jan = future_jan.result()
            
            safe_print(f"[TOOL ROUTER]   Dezembro: success={result_dec.get('success', False)}")
            safe_print(f"[TOOL ROUTER]   Janeiro: success={result_jan.get('success', False)}")
            
            # Construir resultado de comparacao com dados BRUTOS
            # O LLM vai interpretar livremente - nao forcamos calculo de diferencas
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
                # Campos opcionais - serao None, LLM interpreta os dados brutos
                "differences": None,
                "chart_data": None
            }
            
            safe_print(f"[TOOL ROUTER] [OK] Comparacao concluida - dados brutos passados ao LLM")
            
            return {
                "tool_result": comparison_result,
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": comparison_result["success"],
                    "stdout": f"Comparacao executada com {tool_name}",
                    "stderr": "",
                    "return_code": 0 if comparison_result["success"] else -1
                }
            }
            
        except Exception as e:
            safe_print(f"[TOOL ROUTER] [ERRO] Erro na comparacao: {e}")
            import traceback
            traceback.print_exc()
            return {
                "tool_result": {"success": False, "error": str(e), "is_comparison": True},
                "tool_used": tool_name,
                "tool_route": True,
                "execution_result": {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Erro na comparacao: {str(e)}",
                    "return_code": -1
                }
            }
    
    # Detectar se a query veio de uma escolha de disambiguation
    # Queries expandidas contêm " - " (espaço, hífen, espaço) separando query original do contexto
    # OU podem conter diretamente o nome da tool (ex: "TermCadastroTool")
    is_from_disambiguation = " - " in query
    
    # Verificar se a query contém diretamente o nome de uma tool
    # Isso pode acontecer se o LLM retornar apenas o nome da tool na disambiguation
    tool_names = [t.get_name() for t in tools]
    direct_tool_match = None
    for tool_name in tool_names:
        if tool_name.lower() in query.lower():
            # Verificar se é uma correspondência exata ou contém o nome da tool
            query_words = query.lower().split()
            if tool_name.lower() in query_words or tool_name.lower() == query.lower().strip():
                direct_tool_match = tool_name
                break
    
    # Flag para indicar se estamos no modo comparison
    # Definida ANTES de processar disambiguation para ser usada em todos os fluxos
    is_comparison_mode = analysis_mode == "comparison"
    if is_comparison_mode:
        safe_print("[TOOL ROUTER] [COMPARISON] Modo comparacao ativo - tool sera executada em ambos os decks")
    
    if is_from_disambiguation or direct_tool_match:
        if is_from_disambiguation:
            safe_print("[TOOL ROUTER] Query detectada como escolha de disambiguation (contem ' - ')")
            safe_print("[TOOL ROUTER]   -> Identificando tool diretamente sem semantic matching")
            
            # Extrair contexto apos o " - "
            parts = query.split(" - ", 1)
            original_query = parts[0].strip()
            context = parts[1].strip() if len(parts) > 1 else ""
            
            safe_print(f"[TOOL ROUTER]   Query completa: {query}")
            safe_print(f"[TOOL ROUTER]   Query original: {original_query}")
            safe_print(f"[TOOL ROUTER]   Contexto escolhido: '{context}'")
            
            if not context:
                safe_print(f"[TOOL ROUTER] [AVISO] Contexto vazio apos ' - ', continuando com fluxo normal")
            else:
                # Identificar tool diretamente pelo contexto
                safe_print(f"[TOOL ROUTER]   Buscando tool para contexto: '{context}'")
                safe_print(f"[TOOL ROUTER]   Tools disponiveis: {[t.get_name() for t in tools]}")
                selected_tool = _identify_tool_from_context(context, tools)
                
                if selected_tool:
                    tool_name = selected_tool.get_name()
                    safe_print(f"[TOOL ROUTER] [OK] Tool identificada diretamente: {tool_name}")
                    safe_print(f"[TOOL ROUTER]   -> Executando tool sem semantic matching")
                    safe_print(f"[TOOL ROUTER]   Query que sera usada na tool: {original_query}")
                    
                    # IMPORTANTE: Verificar modo comparison
                    if is_comparison_mode:
                        safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                        result = _execute_tool_comparison(selected_tool.__class__, tool_name, original_query)
                    else:
                        result = _execute_tool(selected_tool, tool_name, original_query)
                    
                    result["from_disambiguation"] = True
                    safe_print(f"[TOOL ROUTER] [OK] Resultado da tool retornado: success={result.get('tool_result', {}).get('success', False)}")
                    return result
                else:
                    safe_print(f"[TOOL ROUTER] [AVISO] Nao foi possivel identificar tool pelo contexto")
                    safe_print(f"[TOOL ROUTER]   -> Continuando com fluxo normal (semantic matching)")
        
        elif direct_tool_match:
            safe_print(f"[TOOL ROUTER] Query detectada como escolha de disambiguation (contem nome da tool: {direct_tool_match})")
            safe_print(f"[TOOL ROUTER]   -> Executando tool diretamente sem semantic matching")
            
            # Encontrar a tool correspondente
            selected_tool = None
            for tool in tools:
                if tool.get_name() == direct_tool_match:
                    selected_tool = tool
                    break
            
            if selected_tool:
                # Tentar extrair a query original (remover o nome da tool)
                original_query = query.replace(direct_tool_match, "").strip()
                if not original_query:
                    original_query = query
                
                safe_print(f"[TOOL ROUTER] [OK] Tool identificada diretamente: {direct_tool_match}")
                safe_print(f"[TOOL ROUTER]   Query que sera usada na tool: {original_query}")
                
                # IMPORTANTE: Verificar modo comparison
                if is_comparison_mode:
                    safe_print(f"[TOOL ROUTER]   [COMPARISON] Executando em ambos os decks...")
                    result = _execute_tool_comparison(selected_tool.__class__, direct_tool_match, original_query)
                else:
                    result = _execute_tool(selected_tool, direct_tool_match, original_query)
                
                result["from_disambiguation"] = True
                safe_print(f"[TOOL ROUTER] [OK] Resultado da tool retornado: success={result.get('tool_result', {}).get('success', False)}")
                return result
            else:
                safe_print(f"[TOOL ROUTER] [AVISO] Tool {direct_tool_match} nao encontrada na lista de tools")
    
    # 1. Verificar palavras-chave prioritarias ANTES do semantic matching
    # Isso garante que tools com palavras-chave prioritárias sejam executadas diretamente
    safe_print("[TOOL ROUTER] 🔍 Verificando palavras-chave prioritárias...")
    query_lower = query.lower()
    
    # Mapeamento de palavras-chave prioritárias para nomes de tools
    priority_keywords = {
        # DsvaguaTool: "desvios de água" em todas as variações
        "DsvaguaTool": [
            "desvios de água", "desvios de agua", "desvio de água", "desvio de agua",
            "desvios-agua", "desvios-água", "desvios_agua", "desvios_água",
            "desvio-agua", "desvio-água", "desvio_agua", "desvio_água"
        ],
        # ModifOperacaoTool: "vazão mínima" em todas as variações
        "ModifOperacaoTool": [
            "vazão mínima", "vazao minima", "vazão minima", "vazao mínima",
            "vazao-minima", "vazão-mínima", "vazao_minima", "vazão_mínima"
        ]
    }
    
    # Verificar se alguma palavra-chave prioritária está presente
    for tool_name, keywords in priority_keywords.items():
        if any(kw in query_lower for kw in keywords):
            safe_print(f"[TOOL ROUTER] ✅ PALAVRA-CHAVE PRIORITÁRIA DETECTADA para {tool_name}")
            safe_print(f"[TOOL ROUTER]   → Executando tool diretamente (sem semantic matching)")
            
            # Encontrar a tool correspondente
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   Tool encontrada: {tool_name}")
                    result = _execute_tool(tool, tool_name)
                    safe_print(f"[TOOL ROUTER] ✅ Tool executada diretamente por palavra-chave prioritária")
                    return result
            
            safe_print(f"[TOOL ROUTER] ⚠️ Tool {tool_name} não encontrada na lista de tools disponíveis")
    
    # 1. Tentar match semântico primeiro (se habilitado)
    if SEMANTIC_MATCHING_ENABLED:
        safe_print("[TOOL ROUTER] 🔍 SEMANTIC MATCHING HABILITADO")
        safe_print(f"[TOOL ROUTER]   Threshold para busca (disambiguation): {DISAMBIGUATION_MIN_SCORE:.3f} (captura todas tools >= 0.4)")
        safe_print(f"[TOOL ROUTER]   Threshold ranking (legado): {SEMANTIC_MATCH_THRESHOLD:.3f}")
        safe_print(f"[TOOL ROUTER]   Score mínimo para executar: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
        safe_print(f"[TOOL ROUTER]   Disambiguation diff threshold: {DISAMBIGUATION_SCORE_DIFF_THRESHOLD:.3f} (diferença < 0.1 = ambiguidade)")
        safe_print(f"[TOOL ROUTER]   Regra: Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} → Tool executada | Score < {SEMANTIC_MATCH_MIN_SCORE:.3f} → Fluxo normal")
        safe_print(f"[TOOL ROUTER]   Hybrid matching: {USE_HYBRID_MATCHING}")
        safe_print("[TOOL ROUTER] Tentando match semântico...")
        try:
            # Obter top N tools para verificar ambiguidade
            # IMPORTANTE: Usar DISAMBIGUATION_MIN_SCORE (0.4) como threshold, não SEMANTIC_MATCH_THRESHOLD (0.55)
            # Isso garante que capturamos TODAS as tools com score >= 0.4 para detectar ambiguidade
            # Exemplo: se temos scores 0.55 e 0.53, ambos devem ser capturados para comparação
            safe_print(f"[TOOL ROUTER]   Buscando top {DISAMBIGUATION_MAX_OPTIONS} tools com threshold >= {DISAMBIGUATION_MIN_SCORE:.3f}...")
            semantic_results = find_top_tools_semantic(
                query, 
                tools, 
                top_n=DISAMBIGUATION_MAX_OPTIONS,
                threshold=DISAMBIGUATION_MIN_SCORE  # 0.4 - queremos ver todas as tools acima do mínimo
            )
            
            if semantic_results:
                top_tool, top_score = semantic_results[0]
                tool_name = top_tool.get_name()
                
                safe_print(f"[TOOL ROUTER] ✅ Top tool encontrada: {tool_name} (score: {top_score:.4f})")
                safe_print(f"[TOOL ROUTER]   Total de tools retornadas: {len(semantic_results)}")
                
                # Verificar se score está acima do mínimo
                if top_score >= SEMANTIC_MATCH_MIN_SCORE:
                    # Verificar ambiguidade se houver 2+ tools E query não veio de disambiguation
                    if len(semantic_results) >= 2 and not is_from_disambiguation:
                        second_tool, second_score = semantic_results[1]
                        score_diff = top_score - second_score
                        
                        safe_print(f"[TOOL ROUTER]  ANÁLISE DE AMBIGUIDADE:")
                        safe_print(f"[TOOL ROUTER]   1º lugar: {tool_name} (score: {top_score:.4f})")
                        safe_print(f"[TOOL ROUTER]   2º lugar: {second_tool.get_name()} (score: {second_score:.4f})")
                        safe_print(f"[TOOL ROUTER]   Diferença 1º-2º: {score_diff:.4f}")
                        safe_print(f"[TOOL ROUTER]   Threshold ambiguidade: {DISAMBIGUATION_SCORE_DIFF_THRESHOLD:.3f}")
                        
                        # Detectar ambiguidade baseado em análise empírica
                        if score_diff < DISAMBIGUATION_SCORE_DIFF_THRESHOLD:
                            safe_print(f"[TOOL ROUTER] ⚠️ AMBIGUIDADE DETECTADA!")
                            safe_print(f"[TOOL ROUTER]   Diferença {score_diff:.4f} < {DISAMBIGUATION_SCORE_DIFF_THRESHOLD} → Gerando disambiguation")
                            safe_print(f"[TOOL ROUTER]   Gerando disambiguation com {len(semantic_results)} opções...")
                            return _generate_disambiguation_response(query, semantic_results)
                        else:
                            safe_print(f"[TOOL ROUTER] ✅ Sem ambiguidade (diferença {score_diff:.4f} >= {DISAMBIGUATION_SCORE_DIFF_THRESHOLD})")
                            safe_print(f"[TOOL ROUTER]   → Executando tool diretamente: {tool_name}")
                    elif is_from_disambiguation:
                        safe_print(f"[TOOL ROUTER] ✅ Query veio de disambiguation, executando tool diretamente (sem nova disambiguation)")
                        safe_print(f"[TOOL ROUTER]   Tool selecionada: {tool_name} (score: {top_score:.4f})")
                    else:
                        safe_print(f"[TOOL ROUTER] ✅ Apenas 1 tool encontrada, executando diretamente")
                    
                    # Sem ambiguidade ou veio de disambiguation, executar tool diretamente
                    safe_print(f"[TOOL ROUTER]   Status: [OK] Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f} (tool sera executada)")
                    
                    # Se modo comparison, executar em ambos os decks
                    if is_comparison_mode:
                        return _execute_tool_comparison(top_tool.__class__, tool_name)
                    else:
                        return _execute_tool(top_tool, tool_name)
                else:
                    safe_print(f"[TOOL ROUTER] ⚠️ Match semântico: melhor score {top_score:.4f} < {SEMANTIC_MATCH_MIN_SCORE:.3f}")
                    safe_print(f"[TOOL ROUTER]   → Nenhuma tool será executada, fluxo normal (coder/executor) assumirá")
                    if USE_HYBRID_MATCHING:
                        safe_print("[TOOL ROUTER]   → Continuando para keyword matching (fallback)...")
            else:
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
            # Continuar para fallback keyword matching
    
    # 2. Fallback para keyword matching (se híbrido habilitado ou se semântico desabilitado)
    if USE_HYBRID_MATCHING or not SEMANTIC_MATCHING_ENABLED:
        safe_print("[TOOL ROUTER] Verificando qual tool pode processar a query (keyword matching)...")
        for tool in tools:
            tool_name = tool.get_name()
            safe_print(f"[TOOL ROUTER] Testando tool: {tool_name}")
            
            try:
                if tool.can_handle(query):
                    safe_print(f"[TOOL ROUTER] [OK] Tool {tool_name} pode processar a query!")
                    # Se modo comparison, executar em ambos os decks
                    if is_comparison_mode:
                        return _execute_tool_comparison(tool.__class__, tool_name)
                    else:
                        return _execute_tool(tool, tool_name)
                else:
                    safe_print(f"[TOOL ROUTER] [X] Tool {tool_name} nao pode processar")
            except Exception as e:
                safe_print(f"[TOOL ROUTER] ❌ Erro ao testar/executar tool {tool_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Nenhuma tool pode processar, continuar fluxo normal
    safe_print("[TOOL ROUTER] ⚠️ Nenhuma tool pode processar, continuando fluxo normal")
    safe_print("[TOOL ROUTER] ===== FIM: tool_router_node (retornando tool_route=False) =====")
    return {
        "tool_route": False
    }


def _generate_disambiguation_response(
    query: str,
    top_tools: list[tuple]
) -> dict:
    """
    Gera resposta de disambiguation com perguntas contextuais.
    Baseado em análise empírica, limita a 3 opções.
    
    Args:
        query: Query original do usuário
        top_tools: Lista de tuplas (tool, score) ordenadas por score
        
    Returns:
        Dict com final_response e disambiguation
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from app.config import OPENAI_API_KEY, OPENAI_MODEL, DISAMBIGUATION_MAX_OPTIONS
    
    safe_print("[TOOL ROUTER] Gerando resposta de disambiguation...")
    
    # Limitar a máximo de opções
    tools_to_show = top_tools[:DISAMBIGUATION_MAX_OPTIONS]
    
    # Preparar informações das tools
    tools_info = []
    for tool, score in tools_to_show:
        tool_name = tool.get_name()
        tool_description = tool.get_description()
        # Extrair primeira linha da descrição para resumo
        first_line = tool_description.split('\n')[0].strip()
        # Remover prefixos comuns
        if first_line.startswith("Geração de"):
            first_line = first_line.replace("Geração de", "").strip()
        elif first_line.startswith("Dados de"):
            first_line = first_line.replace("Dados de", "").strip()
        elif first_line.startswith("Informações"):
            first_line = first_line.replace("Informações", "").strip()
        
        # Criar query expandida que direciona para esta tool
        # Formato: "query original - contexto da tool"
        expanded_query = f"{query} - {first_line.lower()}"
        
        tools_info.append({
            'name': tool_name,
            'description': first_line,
            'score': score,
            'expanded_query': expanded_query
        })
    
    # Tentar usar LLM para gerar pergunta natural
    try:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.7
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente especializado em análise de dados do setor elétrico brasileiro.

Sua tarefa é gerar uma pergunta natural e contextualizada para ajudar o usuário a escolher
entre múltiplas opções de ferramentas disponíveis.

IMPORTANTE:
- NÃO mencione explicitamente "qual tool", "qual ferramenta" ou "qual opção"
- Faça perguntas que busquem mais contexto sobre o que o usuário quer
- Seja natural e conversacional
- Use termos técnicos do setor elétrico quando apropriado
- Cada opção deve ser uma query expandida que direciona para a tool correta

FORMATO DA RESPOSTA:
Você deve retornar um JSON com a seguinte estrutura:
{
  "question": "Pergunta natural para o usuário",
  "options": [
    {
      "label": "Texto do botão clicável",
      "query": "Query expandida que direciona para esta tool",
      "tool_name": "NomeDaTool"
    },
    ...
  ]
}"""),
            ("human", """Query original do usuário: "{query}"

Tools candidatas:
{tools_info}

Gere uma pergunta natural com opções clicáveis que ajudem o usuário a escolher a opção correta.
Cada opção deve ser uma query expandida que deixe claro qual tool deve ser usada."""),
        ])
        
        chain = prompt | llm
        
        tools_info_str = "\n".join([
            f"- {info['name']}: {info['description']} (score: {info['score']:.3f})"
            for info in tools_info
        ])
        
        response = chain.invoke({
            "query": query,
            "tools_info": tools_info_str
        })
        
        # Parsear resposta JSON
        import json
        import re
        
        content = getattr(response, 'content', '')
        
        # Extrair JSON da resposta (pode estar dentro de markdown code blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Tentar extrair JSON direto
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback: criar opções manualmente
                safe_print("[TOOL ROUTER] ⚠️ LLM não retornou JSON válido, usando fallback")
                return _create_fallback_disambiguation(query, tools_to_show)
        
        try:
            disambiguation_data = json.loads(json_str)
            options = disambiguation_data.get('options', [])
            
            # Validar que temos opções
            if not options or len(options) != len(tools_to_show):
                safe_print("[TOOL ROUTER] ⚠️ LLM retornou opções inválidas, usando fallback")
                return _create_fallback_disambiguation(query, tools_to_show)
            
            # Pergunta padrão única
            question = "Preciso de mais informações, escolha a opção que se refere melhor a sua consulta:"
            
            safe_print(f"[TOOL ROUTER] ✅ Disambiguation gerada com {len(options)} opções")
            
            return {
                "tool_route": False,  # Não executar tool ainda
                "final_response": "",  # Vazio - frontend cria a mensagem
                "disambiguation": {
                    "type": "tool_selection",
                    "question": question,
                    "options": options,
                    "original_query": query
                }
            }
            
        except json.JSONDecodeError as e:
            safe_print(f"[TOOL ROUTER] ⚠️ Erro ao parsear JSON de disambiguation: {e}")
            return _create_fallback_disambiguation(query, tools_to_show)
            
    except Exception as e:
        safe_print(f"[TOOL ROUTER] ⚠️ Erro ao gerar disambiguation com LLM: {e}")
        import traceback
        traceback.print_exc()
        return _create_fallback_disambiguation(query, tools_to_show)


def _create_fallback_disambiguation(
    query: str,
    top_tools: list[tuple]
) -> dict:
    """
    Cria disambiguation de fallback usando mapeamento de descrições amigáveis.
    Usado quando LLM falha ou retorna formato inválido.
    """
    safe_print("[TOOL ROUTER] Usando fallback para disambiguation...")
    
    # Mapear nomes de tools para descrições amigáveis
    tool_descriptions = {
        "HidrCadastroTool": "Informações cadastrais da usina (dados físicos, volumes, potência)",
        "ConfhdTool": "Configuração da usina (REE, status, volume inicial)",
        "VazoesTool": "Vazões históricas da usina",
        "DsvaguaTool": "Desvios de água da usina",
        "ModifOperacaoTool": "Modificações operacionais hídricas da usina",
        "ExptOperacaoTool": "Modificações operacionais térmicas",
        "RestricaoEletricaTool": "Restrições elétricas (fórmulas e limites)",
        "LimitesIntercambioTool": "Limites de intercâmbio entre subsistemas",
        "AgrintTool": "Agrupamentos de intercâmbio",
        "CargaMensalTool": "Carga mensal do sistema por submercado",
        "UsinasNaoSimuladasTool": "Geração de usinas não simuladas (PCH, PCT, EOL, UFV)",
        "ClastValoresTool": "Custos de classes térmicas",
        "CadicTool": "Cargas e ofertas adicionais",
        "TermCadastroTool": "Cadastro de usinas termoelétricas (potência, fator de capacidade, indisponibilidades)",
    }
    
    # Pergunta padrão única
    question = "Preciso de mais informações, escolha a opção que se refere melhor a sua consulta:"
    
    options = []
    for idx, (tool, score) in enumerate(top_tools, 1):
        tool_name = tool.get_name()
        friendly_desc = tool_descriptions.get(tool_name, tool_name)
        
        # Criar query expandida baseada no nome da tool
        expanded_query = _expand_query_for_tool(query, tool_name)
        
        options.append({
            "label": friendly_desc,
            "query": expanded_query,
            "tool_name": tool_name
        })
    
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


def _expand_query_for_tool(query: str, tool_name: str) -> str:
    """
    Expande a query original para direcionar para uma tool específica.
    """
    expansions = {
        "HidrCadastroTool": f"{query} - dados cadastrais físicos da usina",
        "ConfhdTool": f"{query} - configuração REE e status",
        "VazoesTool": f"{query} - vazões históricas",
        "DsvaguaTool": f"{query} - desvios de água",
        "ModifOperacaoTool": f"{query} - modificações operacionais hídricas",
        "ExptOperacaoTool": f"{query} - modificações operacionais térmicas",
        "RestricaoEletricaTool": f"{query} - restrições elétricas",
        "LimitesIntercambioTool": f"{query} - limites de intercâmbio",
        "AgrintTool": f"{query} - agrupamentos de intercâmbio",
        "CargaMensalTool": f"{query} - carga mensal do sistema",
        "UsinasNaoSimuladasTool": f"{query} - geração de usinas não simuladas",
        "ClastValoresTool": f"{query} - custos de classes térmicas",
        "CadicTool": f"{query} - cargas e ofertas adicionais",
        "TermCadastroTool": f"{query} - cadastro de usinas termoelétricas",
    }
    return expansions.get(tool_name, query)


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
    # Mapeamento de contextos para nomes de tools
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
    }
    
    # Normalizar contexto (remover espaços extras, lowercase)
    context_normalized = context.strip().lower()
    
    safe_print(f"[TOOL ROUTER]   Buscando tool para contexto: '{context_normalized}'")
    safe_print(f"[TOOL ROUTER]   Contextos disponíveis: {list(context_to_tool.keys())}")
    
    # PRIMEIRO: Verificar se o contexto contém diretamente o nome de uma tool
    # Isso pode acontecer se o LLM retornar "TermCadastroTool" diretamente
    tool_names = [t.get_name() for t in tools]
    for tool_name in tool_names:
        if tool_name.lower() == context_normalized or tool_name.lower() in context_normalized.split():
            safe_print(f"[TOOL ROUTER]   ✅ Contexto contém nome da tool diretamente: {tool_name}")
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                    return tool
    
    # Buscar match exato primeiro
    tool_name = context_to_tool.get(context_normalized)
    if tool_name:
        safe_print(f"[TOOL ROUTER]   ✅ Match exato encontrado: {tool_name}")
        for tool in tools:
            if tool.get_name() == tool_name:
                safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                return tool
    
    # Se não encontrou match exato, buscar por palavras-chave
    # Primeiro, tentar match parcial (contexto contém chave ou vice-versa)
    for key, tool_name in context_to_tool.items():
        key_normalized = key.lower()
        # Verificar se o contexto contém a chave ou vice-versa
        if key_normalized in context_normalized or context_normalized in key_normalized:
            safe_print(f"[TOOL ROUTER]   ✅ Match parcial encontrado: {tool_name} (chave: '{key}')")
            for tool in tools:
                if tool.get_name() == tool_name:
                    safe_print(f"[TOOL ROUTER]   ✅ Tool encontrada: {tool.get_name()}")
                    return tool
    
    # Se ainda não encontrou, buscar por palavras-chave importantes
    # Extrair palavras-chave importantes do contexto
    context_words = set(context_normalized.split())
    
    best_match = None
    best_score = 0
    
    for key, tool_name in context_to_tool.items():
        key_normalized = key.lower()
        key_words = set(key_normalized.split())
        
        # Calcular score de similaridade (quantas palavras em comum)
        common_words = context_words.intersection(key_words)
        if len(common_words) > 0:
            # Score baseado em palavras comuns e tamanho da chave
            score = len(common_words) / max(len(key_words), 1)
            if score > best_score and score >= 0.5:  # Pelo menos 50% de match
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


"""
Módulo para matching semântico de tools usando embeddings.
"""
from typing import Optional, Tuple, Dict
import numpy as np
import re
import hashlib
from app.tools.base import NEWAVETool
from app.rag.vectorstore import get_embeddings
from app.config import QUERY_EXPANSION_ENABLED, SEMANTIC_MATCH_MIN_SCORE, safe_print

# Cache global de embeddings das tools
# Estrutura: {tool_name: {'description_hash': str, 'embedding': list[float]}}
_tool_embeddings_cache: Dict[str, Dict] = {}


def clear_tool_embeddings_cache():
    """
    Limpa o cache de embeddings das tools.
    Útil se as descrições das tools forem modificadas.
    """
    global _tool_embeddings_cache
    _tool_embeddings_cache.clear()
    safe_print("[SEMANTIC MATCHER] 🗑️ Cache de embeddings das tools limpo")


def get_cache_stats() -> Dict[str, int]:
    """
    Retorna estatísticas do cache de embeddings.
    
    Returns:
        Dict com estatísticas do cache
    """
    return {
        'cached_tools': len(_tool_embeddings_cache),
        'total_embeddings': len(_tool_embeddings_cache)
    }


def preload_tool_embeddings(tools: list[NEWAVETool]) -> None:
    """
    Pré-carrega os embeddings de todas as tools no cache.
    Útil para melhorar performance na primeira query.
    
    Args:
        tools: Lista de tools para pré-carregar embeddings
    """
    if not tools:
        return
    
    safe_print(f"[SEMANTIC MATCHER] 🔄 Pré-carregando embeddings de {len(tools)} tools...")
    embeddings_model = get_embeddings()
    
    for tool in tools:
        try:
            _get_tool_embedding(tool, embeddings_model)
        except Exception as e:
            safe_print(f"[SEMANTIC MATCHER] ⚠️ Erro ao pré-carregar embedding de {tool.get_name()}: {e}")
    
    cache_stats = get_cache_stats()
    safe_print(f"[SEMANTIC MATCHER] ✅ Pré-carregamento concluído: {cache_stats['cached_tools']} embeddings cacheados")


def expand_query(query: str) -> str:
    """
    Expande a query com sinônimos e variações para melhorar o matching semântico.
    
    Args:
        query: Query original do usuário
        
    Returns:
        Query expandida com sinônimos e variações
    """
    if not QUERY_EXPANSION_ENABLED:
        return query
    
    query_lower = query.lower()
    expanded_parts = [query]  # Sempre incluir query original
    
    # Dicionário de expansões: termo -> lista de sinônimos/variações
    expansions = {
        # Variações de comandos
        r'\bme dê\b': ['me de', 'mostre', 'quero ver', 'preciso de', 'quero', 'desejo'],
        r'\bme de\b': ['me dê', 'mostre', 'quero ver', 'preciso de', 'quero'],
        r'\bmostre\b': ['me dê', 'me de', 'quero ver', 'preciso de'],
        r'\bquais são\b': ['quais', 'mostre', 'me dê', 'me de'],
        r'\bqual\b': ['quais', 'mostre', 'me dê'],
        
        # Carga/Demanda
        r'\bcargas mensais\b': ['demandas mensais', 'consumo mensal', 'carga mensal', 'demanda mensal'],
        r'\bcarga mensal\b': ['demanda mensal', 'consumo mensal', 'cargas mensais', 'demandas mensais'],
        r'\bdemanda mensal\b': ['carga mensal', 'consumo mensal', 'demandas mensais', 'cargas mensais'],
        r'\bdemandas mensais\b': ['cargas mensais', 'consumo mensal', 'demanda mensal', 'carga mensal'],
        r'\bconsumo mensal\b': ['carga mensal', 'demanda mensal', 'cargas mensais', 'demandas mensais'],
        r'\bcarga\b': ['demanda', 'consumo', 'necessidade'],
        r'\bdemanda\b': ['carga', 'consumo', 'necessidade'],
        
        # Submercado/Subsistema
        r'\bpor submercado\b': ['por subsistema', 'por região', 'do submercado', 'do subsistema'],
        r'\bdo submercado\b': ['do subsistema', 'por submercado', 'por subsistema'],
        r'\bsubmercado\b': ['subsistema', 'região'],
        r'\bsubsistema\b': ['submercado', 'região'],
        
        # Modificações hídricas
        r'\bmodificações hídricas\b': ['modificação hídrica', 'operação hídrica', 'modificações hidrelétricas', 'alterações hidrelétricas'],
        r'\bmodificação hídrica\b': ['modificações hídricas', 'operação hídrica', 'modificações hidrelétricas'],
        r'\boperação hídrica\b': ['modificações hídricas', 'modificação hídrica', 'operacional hídrica'],
        r'\bvolume mínimo\b': ['volumes mínimos', 'volume min', 'vol min'],
        r'\bvolume máximo\b': ['volumes máximos', 'volume max', 'vol max'],
        r'\bvazão mínima\b': ['vazões mínimas', 'vazao minima', 'vaz min'],
        r'\bvazão máxima\b': ['vazões máximas', 'vazao maxima', 'vaz max'],
        
        # Operação térmica
        r'\bmodificações térmicas\b': ['modificação térmica', 'operação térmica', 'expansões térmicas', 'expansão térmica'],
        r'\bexpansão térmica\b': ['expansões térmicas', 'modificações térmicas', 'operação térmica'],
        r'\bexpansões térmicas\b': ['expansão térmica', 'modificações térmicas', 'operação térmica'],
        r'\bpotência efetiva\b': ['potencia efetiva', 'pot efetiva', 'potef'],
        r'\bgeração mínima\b': ['geracao minima', 'ger min', 'gtmin'],
        r'\bindisponibilidade programada\b': ['indisponibilidades programadas', 'indisponibilidade', 'ipter'],
        
        # Custos
        r'\bcustos das classes térmicas\b': ['custo da classe térmica', 'custos térmicos', 'valores estruturais', 'valores conjunturais'],
        r'\bclasse térmica\b': ['classes térmicas', 'classe termica', 'classe termelétrica'],
        r'\bvalores estruturais\b': ['valor estrutural', 'custos base', 'custos estruturais'],
        r'\bvalores conjunturais\b': ['valor conjuntural', 'modificações sazonais', 'ajustes sazonais'],
        r'\bcvu\b': ['custo variável unitário', 'custo variavel unitario', 'custo unitário variável'],
    }
    
    # Aplicar expansões mantendo contexto
    expanded_queries = [query]  # Sempre incluir query original
    
    for pattern, synonyms in expansions.items():
        if re.search(pattern, query_lower):
            # Para cada sinônimo, criar uma variação da query
            for synonym in synonyms:
                # Substituir o padrão pelo sinônimo na query
                expanded = re.sub(pattern, synonym, query_lower, flags=re.IGNORECASE)
                if expanded != query_lower:
                    expanded_queries.append(expanded)
    
    # Adicionar variações comuns
    # Remover pontuação
    query_no_punct = re.sub(r'[?!.,;:]', '', query)
    if query_no_punct != query:
        expanded_queries.append(query_no_punct)
    
    # Versão sem acentos (simplificada - apenas casos comuns)
    query_no_accents = query_lower.replace('ã', 'a').replace('á', 'a').replace('â', 'a').replace('à', 'a')
    query_no_accents = query_no_accents.replace('é', 'e').replace('ê', 'e')
    query_no_accents = query_no_accents.replace('í', 'i').replace('î', 'i')
    query_no_accents = query_no_accents.replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
    query_no_accents = query_no_accents.replace('ú', 'u').replace('û', 'u')
    query_no_accents = query_no_accents.replace('ç', 'c')
    if query_no_accents != query_lower:
        expanded_queries.append(query_no_accents)
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique_queries = []
    for exp_query in expanded_queries:
        exp_lower = exp_query.lower().strip()
        if exp_lower and exp_lower not in seen:
            seen.add(exp_lower)
            unique_queries.append(exp_query)
    
    # Combinar todas as expansões em uma única string
    # Isso ajuda o embedding a capturar todos os sinônimos
    expanded_query = ' '.join(unique_queries)
    
    return expanded_query


def _get_tool_embedding(tool: NEWAVETool, embeddings_model) -> list[float]:
    """
    Obtém o embedding de uma tool, usando cache se disponível.
    
    Args:
        tool: Tool para obter embedding
        embeddings_model: Modelo de embeddings
        
    Returns:
        Embedding da descrição da tool
    """
    tool_name = tool.get_name()
    tool_description = tool.get_description()
    
    # Calcular hash da descrição para detectar mudanças
    description_hash = hashlib.md5(tool_description.encode('utf-8')).hexdigest()
    
    # Verificar se já temos o embedding em cache e se a descrição não mudou
    if tool_name in _tool_embeddings_cache:
        cached = _tool_embeddings_cache[tool_name]
        if cached['description_hash'] == description_hash:
            safe_print(f"[SEMANTIC MATCHER]   └─ ✅ Embedding em cache (tool: {tool_name})")
            return cached['embedding']
        else:
            safe_print(f"[SEMANTIC MATCHER]   └─ ⚠️ Descrição mudou, regenerando embedding (tool: {tool_name})")
    
    # Gerar novo embedding
    safe_print(f"[SEMANTIC MATCHER]   └─ 🔄 Gerando novo embedding (tool: {tool_name})")
    embedding = embeddings_model.embed_query(tool_description)
    
    # Armazenar no cache
    _tool_embeddings_cache[tool_name] = {
        'description_hash': description_hash,
        'embedding': embedding
    }
    
    return embedding


def _calculate_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calcula a similaridade de cosseno entre dois vetores.
    
    Args:
        vec1: Primeiro vetor (embedding)
        vec2: Segundo vetor (embedding)
        
    Returns:
        Similaridade de cosseno (0.0 a 1.0)
    """
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    # Calcular produto escalar
    dot_product = np.dot(vec1_array, vec2_array)
    
    # Calcular normas
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    # Evitar divisão por zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Similaridade de cosseno
    similarity = dot_product / (norm1 * norm2)
    
    # Garantir que está no range [0, 1]
    return max(0.0, min(1.0, similarity))


def find_best_tool_semantic(
    query: str, 
    tools: list[NEWAVETool], 
    threshold: float = 0.7
) -> Optional[Tuple[NEWAVETool, float]]:
    """
    Encontra a tool mais relevante usando matching semântico.
    
    Gera embeddings da query e das descrições de cada tool,
    calcula similaridade de cosseno e retorna a tool com maior
    similaridade se acima do threshold.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        threshold: Threshold mínimo de similaridade (0.0 a 1.0)
        
    Returns:
        Tupla (tool, score) se encontrada tool acima do threshold, ou None
    """
    if not tools:
        safe_print("[SEMANTIC MATCHER] ⚠️ Nenhuma tool disponível")
        return None
    
    safe_print("[SEMANTIC MATCHER] ===== INÍCIO: Semantic Matching =====")
    safe_print(f"[SEMANTIC MATCHER] Query original: \"{query}\"")
    
    # Aplicar query expansion se habilitado
    expanded_query = expand_query(query)
    if expanded_query != query:
        safe_print(f"[SEMANTIC MATCHER] 🔍 Query Expansion aplicada:")
        safe_print(f"[SEMANTIC MATCHER]   Original: \"{query}\"")
        safe_print(f"[SEMANTIC MATCHER]   Expandida: \"{expanded_query}\"")
    else:
        safe_print(f"[SEMANTIC MATCHER] ⚠️ Query Expansion desabilitada ou sem expansões aplicadas")
    
    safe_print(f"[SEMANTIC MATCHER] Threshold (ranking): {threshold:.3f}")
    safe_print(f"[SEMANTIC MATCHER] Score mínimo para executar: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
    safe_print(f"[SEMANTIC MATCHER] Tools disponíveis: {len(tools)}")
    
    # Mostrar estatísticas do cache
    cache_stats = get_cache_stats()
    safe_print(f"[SEMANTIC MATCHER] 📦 Cache: {cache_stats['cached_tools']} tools com embeddings cacheados")
    
    try:
        # Obter modelo de embeddings
        safe_print("[SEMANTIC MATCHER] Gerando embedding da query...")
        embeddings_model = get_embeddings()
        
        # Gerar embedding da query expandida (ou original se expansion desabilitada)
        query_embedding = embeddings_model.embed_query(expanded_query)
        safe_print(f"[SEMANTIC MATCHER] ✅ Embedding da query gerado (dimensão: {len(query_embedding)})")
        
        # Calcular similaridade com cada tool
        best_tool = None
        best_score = 0.0
        all_scores = []  # Para ranking completo
        
        safe_print("[SEMANTIC MATCHER] Calculando similaridades com cada tool...")
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        
        for idx, tool in enumerate(tools, 1):
            try:
                tool_name = tool.get_name()
                safe_print(f"[SEMANTIC MATCHER] [{idx}/{len(tools)}] Processando: {tool_name}")
                
                # Obter descrição da tool
                tool_description = tool.get_description()
                desc_length = len(tool_description)
                safe_print(f"[SEMANTIC MATCHER]   └─ Descrição: {desc_length} caracteres")
                
                # Obter embedding da descrição (usando cache se disponível)
                tool_embedding = _get_tool_embedding(tool, embeddings_model)
                
                # Calcular similaridade de cosseno
                similarity = _calculate_cosine_similarity(query_embedding, tool_embedding)
                
                # Armazenar score para ranking
                all_scores.append({
                    'tool': tool_name,
                    'score': similarity,
                    'above_threshold': similarity >= threshold
                })
                
                # Atualizar melhor match se necessário
                status = "✅ MELHOR" if similarity > best_score else "  "
                threshold_status = "✅ ACIMA" if similarity >= threshold else "❌ ABAIXO"
                safe_print(f"[SEMANTIC MATCHER]   └─ Similaridade: {similarity:.4f} {status} | Threshold: {threshold_status}")
                
                if similarity > best_score:
                    best_score = similarity
                    best_tool = tool
                    
            except Exception as e:
                # Se houver erro ao processar uma tool, continuar com as outras
                safe_print(f"[SEMANTIC MATCHER]   └─ ❌ Erro ao processar: {e}")
                all_scores.append({
                    'tool': tool.get_name(),
                    'score': 0.0,
                    'above_threshold': False,
                    'error': str(e)
                })
                continue
        
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        
        # Mostrar ranking completo
        safe_print("[SEMANTIC MATCHER] 📊 RANKING DE SIMILARIDADE:")
        all_scores_sorted = sorted(all_scores, key=lambda x: x['score'], reverse=True)
        for rank, item in enumerate(all_scores_sorted, 1):
            tool_name = item['tool']
            score = item['score']
            above = "✅" if item['above_threshold'] else "❌"
            marker = "🏆" if rank == 1 else "  "
            safe_print(f"[SEMANTIC MATCHER]   {marker} {rank}. {tool_name}: {score:.4f} {above} (threshold: {threshold:.3f})")
        
        # Nova regra: Se score >= 0.4, sempre executar a tool com maior score
        # Se score < 0.4, nenhuma tool é executada (fluxo normal assume)
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        safe_print(f"[SEMANTIC MATCHER] 📋 REGRA DE DECISÃO:")
        safe_print(f"[SEMANTIC MATCHER]   - Score >= {SEMANTIC_MATCH_MIN_SCORE:.3f}: Tool será executada")
        safe_print(f"[SEMANTIC MATCHER]   - Score < {SEMANTIC_MATCH_MIN_SCORE:.3f}: Nenhuma tool (fluxo normal)")
        
        if best_tool and best_score >= SEMANTIC_MATCH_MIN_SCORE:
            safe_print(f"[SEMANTIC MATCHER] ✅ TOOL SELECIONADA PARA EXECUÇÃO!")
            safe_print(f"[SEMANTIC MATCHER]   Tool: {best_tool.get_name()}")
            safe_print(f"[SEMANTIC MATCHER]   Score: {best_score:.4f}")
            safe_print(f"[SEMANTIC MATCHER]   Score mínimo: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
            safe_print(f"[SEMANTIC MATCHER]   Status: ✅ ACIMA DO MÍNIMO (tool será executada)")
            safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (TOOL SELECIONADA) =====")
            return (best_tool, best_score)
        else:
            if best_tool:
                safe_print(f"[SEMANTIC MATCHER] ❌ NENHUMA TOOL SERÁ EXECUTADA")
                safe_print(f"[SEMANTIC MATCHER]   Melhor tool: {best_tool.get_name()}")
                safe_print(f"[SEMANTIC MATCHER]   Melhor score: {best_score:.4f}")
                safe_print(f"[SEMANTIC MATCHER]   Score mínimo necessário: {SEMANTIC_MATCH_MIN_SCORE:.3f}")
                safe_print(f"[SEMANTIC MATCHER]   Diferença: {best_score - SEMANTIC_MATCH_MIN_SCORE:.4f} (faltam {SEMANTIC_MATCH_MIN_SCORE - best_score:.4f})")
                safe_print(f"[SEMANTIC MATCHER]   → Fluxo normal (coder/executor) assumirá")
            else:
                safe_print(f"[SEMANTIC MATCHER] ❌ NENHUMA TOOL PROCESSADA COM SUCESSO")
                safe_print(f"[SEMANTIC MATCHER]   → Fluxo normal (coder/executor) assumirá")
            safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (FLUXO NORMAL) =====")
            return None
            
    except Exception as e:
        safe_print(f"[SEMANTIC MATCHER] ❌ Erro no matching semântico: {e}")
        import traceback
        traceback.print_exc()
        safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (ERRO) =====")
        return None


def find_top_tools_semantic(
    query: str,
    tools: list[NEWAVETool],
    top_n: int = 3,
    threshold: float = 0.55
) -> list[Tuple[NEWAVETool, float]]:
    """
    Encontra as top N tools mais relevantes usando matching semântico.
    Baseado na análise empírica, retorna até 3 tools candidatas.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        top_n: Número máximo de tools a retornar (padrão: 3)
        threshold: Threshold mínimo de similaridade para ranking
        
    Returns:
        Lista de tuplas (tool, score) ordenadas por score decrescente
    """
    if not tools:
        safe_print("[SEMANTIC MATCHER] ⚠️ Nenhuma tool disponível")
        return []
    
    safe_print(f"[SEMANTIC MATCHER] ===== INÍCIO: find_top_tools_semantic (top_n={top_n}) =====")
    safe_print(f"[SEMANTIC MATCHER] Query: \"{query}\"")
    
    # Aplicar query expansion se habilitado
    expanded_query = expand_query(query)
    
    try:
        # Obter modelo de embeddings
        embeddings_model = get_embeddings()
        
        # Gerar embedding da query expandida
        query_embedding = embeddings_model.embed_query(expanded_query)
        
        # Calcular similaridade com cada tool
        all_scores = []
        
        for tool in tools:
            try:
                tool_name = tool.get_name()
                
                # Obter embedding da descrição (usando cache se disponível)
                tool_embedding = _get_tool_embedding(tool, embeddings_model)
                
                # Calcular similaridade de cosseno
                similarity = _calculate_cosine_similarity(query_embedding, tool_embedding)
                
                # Armazenar score
                all_scores.append((tool, similarity))
                    
            except Exception as e:
                safe_print(f"[SEMANTIC MATCHER]   └─ ❌ Erro ao processar {tool.get_name()}: {e}")
                continue
        
        # Ordenar por score decrescente
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Mostrar ranking completo de scores
        safe_print(f"[SEMANTIC MATCHER] 📊 RANKING COMPLETO DE SCORES ({len(all_scores)} tools):")
        for idx, (tool, score) in enumerate(all_scores[:10], 1):  # Mostrar top 10
            status = "✅" if score >= threshold else "❌"
            safe_print(f"[SEMANTIC MATCHER]   {idx}. {tool.get_name()}: {score:.4f} {status} (threshold: {threshold:.3f})")
        if len(all_scores) > 10:
            safe_print(f"[SEMANTIC MATCHER]   ... ({len(all_scores) - 10} tools restantes)")
        
        # Filtrar por threshold e retornar top N
        filtered_scores = [(tool, score) for tool, score in all_scores if score >= threshold]
        top_tools = filtered_scores[:top_n]
        
        safe_print(f"[SEMANTIC MATCHER] ✅ Top {len(top_tools)} tools encontradas (após filtro threshold={threshold:.3f}):")
        for idx, (tool, score) in enumerate(top_tools, 1):
            safe_print(f"[SEMANTIC MATCHER]   {idx}. {tool.get_name()}: {score:.4f}")
        
        if len(top_tools) >= 2:
            score_diff = top_tools[0][1] - top_tools[1][1]
            safe_print(f"[SEMANTIC MATCHER]   📏 Diferença 1º-2º: {score_diff:.4f}")
        
        safe_print("[SEMANTIC MATCHER] ===== FIM: find_top_tools_semantic =====")
        return top_tools
            
    except Exception as e:
        safe_print(f"[SEMANTIC MATCHER] ❌ Erro no find_top_tools_semantic: {e}")
        import traceback
        traceback.print_exc()
        return []


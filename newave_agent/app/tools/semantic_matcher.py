"""
Módulo para matching semântico de tools usando embeddings.
"""
from typing import Optional, Tuple, Dict, List
import numpy as np
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from newave_agent.app.tools.base import NEWAVETool
from newave_agent.app.rag.vectorstore import get_embeddings
from newave_agent.app.config import QUERY_EXPANSION_ENABLED, SEMANTIC_MATCH_MIN_SCORE, safe_print

# Cache global de embeddings das tools
# Estrutura: {tool_name: {'description_hash': str, 'embedding': list[float], 'embedding_normalized': np.ndarray}}
_tool_embeddings_cache: Dict[str, Dict] = {}

# Cache global de embeddings de queries
# Estrutura: {query_hash: {'expanded_query': str, 'embedding': list[float], 'embedding_normalized': np.ndarray}}
_query_embeddings_cache: Dict[str, Dict] = {}


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
        'cached_queries': len(_query_embeddings_cache),
        'total_embeddings': len(_tool_embeddings_cache)
    }


def clear_query_embeddings_cache():
    """
    Limpa o cache de embeddings de queries.
    Útil se necessário limpar o cache de queries.
    """
    global _query_embeddings_cache
    _query_embeddings_cache.clear()
    safe_print("[SEMANTIC MATCHER] 🗑️ Cache de embeddings de queries limpo")


def _normalize_embedding(embedding: list[float]) -> np.ndarray:
    """
    Normaliza um embedding para uso em cálculos de similaridade.
    
    Args:
        embedding: Embedding como lista de floats
        
    Returns:
        Embedding normalizado como array NumPy
    """
    embedding_array = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(embedding_array)
    if norm == 0:
        return embedding_array
    return embedding_array / norm


def _get_query_embedding(expanded_query: str, embeddings_model) -> Tuple[list[float], np.ndarray]:
    """
    Obtém o embedding de uma query expandida, usando cache se disponível.
    
    Args:
        expanded_query: Query expandida
        embeddings_model: Modelo de embeddings
        
    Returns:
        Tupla (embedding, embedding_normalized)
    """
    global _query_embeddings_cache
    
    # Calcular hash da query expandida
    query_hash = hashlib.md5(expanded_query.encode('utf-8')).hexdigest()
    
    # Verificar se já temos o embedding em cache
    if query_hash in _query_embeddings_cache:
        cached = _query_embeddings_cache[query_hash]
        safe_print(f"[SEMANTIC MATCHER] ✅ Embedding de query em cache")
        return cached['embedding'], cached['embedding_normalized']
    
    # Gerar novo embedding
    safe_print(f"[SEMANTIC MATCHER] 🔄 Gerando novo embedding de query...")
    embedding = embeddings_model.embed_query(expanded_query)
    
    # Normalizar embedding
    embedding_normalized = _normalize_embedding(embedding)
    
    # Armazenar no cache
    _query_embeddings_cache[query_hash] = {
        'expanded_query': expanded_query,
        'embedding': embedding,
        'embedding_normalized': embedding_normalized
    }
    
    return embedding, embedding_normalized


def preload_tool_embeddings(tools: list[NEWAVETool]) -> None:
    """
    Pré-carrega os embeddings de todas as tools no cache usando processamento paralelo.
    Útil para melhorar performance na primeira query.
    
    Args:
        tools: Lista de tools para pré-carregar embeddings
    """
    if not tools:
        return
    
    safe_print(f"[SEMANTIC MATCHER] 🔄 Pré-carregando embeddings de {len(tools)} tools (paralelo)...")
    embeddings_model = get_embeddings()
    
    # Usar processamento paralelo para pré-carregar embeddings
    _get_tool_embeddings_parallel(tools, embeddings_model, max_workers=5)
    
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


def _get_tool_embedding(tool: NEWAVETool, embeddings_model) -> Tuple[list[float], np.ndarray]:
    """
    Obtém o embedding de uma tool, usando cache se disponível.
    
    Args:
        tool: Tool para obter embedding
        embeddings_model: Modelo de embeddings
        
    Returns:
        Tupla (embedding, embedding_normalized)
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
            # Se não tiver normalizado no cache (compatibilidade com cache antigo), calcular
            if 'embedding_normalized' not in cached:
                cached['embedding_normalized'] = _normalize_embedding(cached['embedding'])
            return cached['embedding'], cached['embedding_normalized']
        else:
            safe_print(f"[SEMANTIC MATCHER]   └─ ⚠️ Descrição mudou, regenerando embedding (tool: {tool_name})")
    
    # Gerar novo embedding
    safe_print(f"[SEMANTIC MATCHER]   └─ 🔄 Gerando novo embedding (tool: {tool_name})")
    embedding = embeddings_model.embed_query(tool_description)
    
    # Normalizar embedding
    embedding_normalized = _normalize_embedding(embedding)
    
    # Armazenar no cache
    _tool_embeddings_cache[tool_name] = {
        'description_hash': description_hash,
        'embedding': embedding,
        'embedding_normalized': embedding_normalized
    }
    
    return embedding, embedding_normalized


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


def _calculate_cosine_similarity_batch(query_embedding_normalized: np.ndarray, tool_embeddings_normalized: np.ndarray) -> np.ndarray:
    """
    Calcula similaridade de cosseno em batch entre um vetor query e múltiplos vetores de tools.
    Todos os vetores devem estar normalizados (já divididos por sua norma).
    
    Args:
        query_embedding_normalized: Embedding da query normalizado (1D array)
        tool_embeddings_normalized: Embeddings das tools normalizados (2D array, shape: [n_tools, embedding_dim])
        
    Returns:
        Array de similaridades de cosseno (1D array, shape: [n_tools])
    """
    # Se tool_embeddings_normalized for 1D (apenas uma tool), converter para 2D
    if tool_embeddings_normalized.ndim == 1:
        tool_embeddings_normalized = tool_embeddings_normalized.reshape(1, -1)
    
    # Calcular produto escalar entre query e cada tool (já normalizados, então é a similaridade de cosseno)
    # query_embedding_normalized: [embedding_dim]
    # tool_embeddings_normalized: [n_tools, embedding_dim]
    # Resultado: [n_tools]
    similarities = np.dot(tool_embeddings_normalized, query_embedding_normalized)
    
    # Garantir que está no range [0, 1] (clipping para evitar erros numéricos)
    similarities = np.clip(similarities, 0.0, 1.0)
    
    return similarities


def _get_tool_embeddings_parallel(tools: list[NEWAVETool], embeddings_model, max_workers: int = 5) -> Dict[str, Tuple[list[float], np.ndarray]]:
    """
    Obtém embeddings de múltiplas tools em paralelo, usando cache quando disponível.
    
    Args:
        tools: Lista de tools para obter embeddings
        embeddings_model: Modelo de embeddings
        max_workers: Número máximo de workers para processamento paralelo
        
    Returns:
        Dict {tool_name: (embedding, embedding_normalized)}
    """
    results = {}
    tools_to_process = []
    
    # Separar tools cacheadas das que precisam ser processadas
    for tool in tools:
        tool_name = tool.get_name()
        tool_description = tool.get_description()
        description_hash = hashlib.md5(tool_description.encode('utf-8')).hexdigest()
        
        if tool_name in _tool_embeddings_cache:
            cached = _tool_embeddings_cache[tool_name]
            if cached['description_hash'] == description_hash:
                # Tool já está em cache
                if 'embedding_normalized' not in cached:
                    cached['embedding_normalized'] = _normalize_embedding(cached['embedding'])
                results[tool_name] = (cached['embedding'], cached['embedding_normalized'])
                continue
        
        # Tool precisa ser processada
        tools_to_process.append(tool)
    
    # Processar tools não cacheadas em paralelo
    if tools_to_process:
        safe_print(f"[SEMANTIC MATCHER] Processando {len(tools_to_process)} embeddings em paralelo...")
        
        def process_tool(tool: NEWAVETool) -> Tuple[str, list[float], np.ndarray]:
            """Função auxiliar para processar uma tool."""
            try:
                embedding, embedding_normalized = _get_tool_embedding(tool, embeddings_model)
                return tool.get_name(), embedding, embedding_normalized
            except Exception as e:
                safe_print(f"[SEMANTIC MATCHER] ⚠️ Erro ao processar {tool.get_name()}: {e}")
                return None, None, None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tool = {executor.submit(process_tool, tool): tool for tool in tools_to_process}
            
            for future in as_completed(future_to_tool):
                tool_name, embedding, embedding_normalized = future.result()
                if tool_name is not None and embedding is not None:
                    results[tool_name] = (embedding, embedding_normalized)
    
    return results


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
        
        # Obter embedding da query expandida (usando cache se disponível)
        query_embedding, query_embedding_normalized = _get_query_embedding(expanded_query, embeddings_model)
        safe_print(f"[SEMANTIC MATCHER] ✅ Embedding da query gerado (dimensão: {len(query_embedding)})")
        
        # Obter embeddings de todas as tools em paralelo (com cache)
        safe_print("[SEMANTIC MATCHER] Obtendo embeddings das tools...")
        tool_embeddings_dict = _get_tool_embeddings_parallel(tools, embeddings_model)
        
        # Preparar arrays para cálculo vetorizado
        tool_names = []
        tool_embeddings_normalized = []
        tool_map = {}  # Mapear tool_name para tool
        
        for tool in tools:
            tool_name = tool.get_name()
            if tool_name in tool_embeddings_dict:
                tool_names.append(tool_name)
                _, embedding_normalized = tool_embeddings_dict[tool_name]
                tool_embeddings_normalized.append(embedding_normalized)
                tool_map[tool_name] = tool
        
        if not tool_embeddings_normalized:
            safe_print("[SEMANTIC MATCHER] ⚠️ Nenhum embedding de tool obtido")
            return None
        
        # Converter para array NumPy
        tool_embeddings_array = np.array(tool_embeddings_normalized)
        
        # Calcular todas as similaridades de uma vez (vetorizado)
        safe_print("[SEMANTIC MATCHER] Calculando similaridades com cada tool (vetorizado)...")
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        similarities = _calculate_cosine_similarity_batch(query_embedding_normalized, tool_embeddings_array)
        
        # Processar resultados
        best_tool = None
        best_score = 0.0
        all_scores = []
        
        for idx, (tool_name, similarity) in enumerate(zip(tool_names, similarities)):
            try:
                tool = tool_map[tool_name]
                safe_print(f"[SEMANTIC MATCHER] [{idx+1}/{len(tool_names)}] {tool_name}: {similarity:.4f}")
                
                # Armazenar score para ranking
                all_scores.append({
                    'tool': tool_name,
                    'score': float(similarity),
                    'above_threshold': similarity >= threshold
                })
                
                # Atualizar melhor match se necessário
                if similarity > best_score:
                    best_score = float(similarity)
                    best_tool = tool
                    
            except Exception as e:
                safe_print(f"[SEMANTIC MATCHER]   └─ ❌ Erro ao processar {tool_name}: {e}")
                all_scores.append({
                    'tool': tool_name,
                    'score': 0.0,
                    'above_threshold': False,
                    'error': str(e)
                })
                continue
        
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        
        # Mostrar ranking completo
        safe_print("[SEMANTIC MATCHER]  RANKING DE SIMILARIDADE:")
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
        
        # Obter embedding da query expandida (usando cache se disponível)
        query_embedding, query_embedding_normalized = _get_query_embedding(expanded_query, embeddings_model)
        
        # Obter embeddings de todas as tools em paralelo (com cache)
        tool_embeddings_dict = _get_tool_embeddings_parallel(tools, embeddings_model)
        
        # Preparar arrays para cálculo vetorizado
        tool_names = []
        tool_embeddings_normalized = []
        tool_map = {}  # Mapear tool_name para tool
        
        for tool in tools:
            tool_name = tool.get_name()
            if tool_name in tool_embeddings_dict:
                tool_names.append(tool_name)
                _, embedding_normalized = tool_embeddings_dict[tool_name]
                tool_embeddings_normalized.append(embedding_normalized)
                tool_map[tool_name] = tool
        
        if not tool_embeddings_normalized:
            safe_print("[SEMANTIC MATCHER] ⚠️ Nenhum embedding de tool obtido")
            return []
        
        # Converter para array NumPy
        tool_embeddings_array = np.array(tool_embeddings_normalized)
        
        # Calcular todas as similaridades de uma vez (vetorizado)
        similarities = _calculate_cosine_similarity_batch(query_embedding_normalized, tool_embeddings_array)
        
        # Criar lista de scores
        all_scores = []
        for tool_name, similarity in zip(tool_names, similarities):
            if tool_name in tool_map:
                all_scores.append((tool_map[tool_name], float(similarity)))
        
        # Ordenar por score decrescente
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Mostrar ranking completo de scores
        safe_print(f"[SEMANTIC MATCHER]  RANKING COMPLETO DE SCORES ({len(all_scores)} tools):")
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


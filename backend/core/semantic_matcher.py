"""
Módulo compartilhado para matching semântico de tools usando embeddings.
Parametrizado para funcionar com qualquer tipo de tool (NEWAVE, DECOMP, etc).
"""
from typing import Optional, Tuple, Dict, List, Callable, Any, Protocol
import numpy as np
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.core.config import safe_print


# Protocolo para qualquer tipo de Tool
class ToolProtocol(Protocol):
    """Protocolo que define a interface mínima de uma Tool."""
    def get_name(self) -> str: ...
    def get_description(self) -> str: ...


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
    safe_print("[SEMANTIC MATCHER] Cache de embeddings das tools limpo")


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
    safe_print("[SEMANTIC MATCHER] Cache de embeddings de queries limpo")


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
        safe_print(f"[SEMANTIC MATCHER] [OK] Embedding de query em cache")
        return cached['embedding'], cached['embedding_normalized']
    
    # Gerar novo embedding
    safe_print(f"[SEMANTIC MATCHER] Gerando novo embedding de query...")
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


def preload_tool_embeddings(
    tools: list,
    get_embeddings_func: Callable[[], Any]
) -> None:
    """
    Pré-carrega os embeddings de todas as tools no cache usando processamento paralelo.
    Útil para melhorar performance na primeira query.
    
    Args:
        tools: Lista de tools para pré-carregar embeddings
        get_embeddings_func: Função para obter o modelo de embeddings
    """
    if not tools:
        return
    
    safe_print(f"[SEMANTIC MATCHER] Pre-carregando embeddings de {len(tools)} tools (paralelo)...")
    embeddings_model = get_embeddings_func()
    
    # Usar processamento paralelo para pré-carregar embeddings
    _get_tool_embeddings_parallel(tools, embeddings_model, max_workers=5)
    
    cache_stats = get_cache_stats()
    safe_print(f"[SEMANTIC MATCHER] [OK] Pre-carregamento concluido: {cache_stats['cached_tools']} embeddings cacheados")


def expand_query(query: str, expansions: Dict[str, List[str]], enabled: bool = True) -> str:
    """
    Expande a query com sinônimos e variações para melhorar o matching semântico.
    
    Args:
        query: Query original do usuário
        expansions: Dicionário de expansões {pattern: [sinônimos]}
        enabled: Se query expansion está habilitada
        
    Returns:
        Query expandida com sinônimos e variações
    """
    if not enabled:
        return query
    
    query_lower = query.lower()
    
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


def _get_tool_embedding(tool, embeddings_model) -> Tuple[list[float], np.ndarray]:
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
            safe_print(f"[SEMANTIC MATCHER]   [OK] Embedding em cache (tool: {tool_name})")
            # Se não tiver normalizado no cache (compatibilidade com cache antigo), calcular
            if 'embedding_normalized' not in cached:
                cached['embedding_normalized'] = _normalize_embedding(cached['embedding'])
            return cached['embedding'], cached['embedding_normalized']
        else:
            safe_print(f"[SEMANTIC MATCHER]   [AVISO] Descricao mudou, regenerando embedding (tool: {tool_name})")
    
    # Gerar novo embedding
    safe_print(f"[SEMANTIC MATCHER]   Gerando novo embedding (tool: {tool_name})")
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
    similarities = np.dot(tool_embeddings_normalized, query_embedding_normalized)
    
    # Garantir que está no range [0, 1] (clipping para evitar erros numéricos)
    similarities = np.clip(similarities, 0.0, 1.0)
    
    return similarities


def _get_tool_embeddings_parallel(
    tools: list,
    embeddings_model,
    max_workers: int = 5
) -> Dict[str, Tuple[list[float], np.ndarray]]:
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
        
        def process_tool(tool) -> Tuple[str, list[float], np.ndarray]:
            """Função auxiliar para processar uma tool."""
            try:
                embedding, embedding_normalized = _get_tool_embedding(tool, embeddings_model)
                return tool.get_name(), embedding, embedding_normalized
            except Exception as e:
                safe_print(f"[SEMANTIC MATCHER] [AVISO] Erro ao processar {tool.get_name()}: {e}")
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
    tools: list,
    get_embeddings_func: Callable[[], Any],
    query_expansion_enabled: bool,
    expansions: Dict[str, List[str]],
    semantic_match_min_score: float,
    threshold: float = 0.7,
    can_handle_filter: bool = False
) -> Optional[Tuple[Any, float]]:
    """
    Encontra a tool mais relevante usando matching semântico.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        get_embeddings_func: Função para obter modelo de embeddings
        query_expansion_enabled: Se query expansion está habilitada
        expansions: Dicionário de expansões para query expansion
        semantic_match_min_score: Score mínimo para executar uma tool
        threshold: Threshold mínimo de similaridade para ranking
        can_handle_filter: Se deve filtrar tools por can_handle (DECOMP usa True)
        
    Returns:
        Tupla (tool, score) se encontrada tool acima do threshold, ou None
    """
    if not tools:
        safe_print("[SEMANTIC MATCHER] [AVISO] Nenhuma tool disponível")
        return None
    
    safe_print("[SEMANTIC MATCHER] ===== INÍCIO: Semantic Matching =====")
    safe_print(f"[SEMANTIC MATCHER] Query original: \"{query}\"")
    
    # Aplicar query expansion se habilitado
    expanded_query = expand_query(query, expansions, query_expansion_enabled)
    if expanded_query != query:
        safe_print(f"[SEMANTIC MATCHER] Query Expansion aplicada:")
        safe_print(f"[SEMANTIC MATCHER]   Original: \"{query}\"")
        safe_print(f"[SEMANTIC MATCHER]   Expandida: \"{expanded_query}\"")
    
    safe_print(f"[SEMANTIC MATCHER] Threshold (ranking): {threshold:.3f}")
    safe_print(f"[SEMANTIC MATCHER] Score mínimo para executar: {semantic_match_min_score:.3f}")
    safe_print(f"[SEMANTIC MATCHER] Tools disponíveis: {len(tools)}")
    
    # Mostrar estatísticas do cache
    cache_stats = get_cache_stats()
    safe_print(f"[SEMANTIC MATCHER] Cache: {cache_stats['cached_tools']} tools com embeddings cacheados")
    
    try:
        # Obter modelo de embeddings
        safe_print("[SEMANTIC MATCHER] Gerando embedding da query...")
        embeddings_model = get_embeddings_func()
        
        # Obter embedding da query expandida (usando cache se disponível)
        query_embedding, query_embedding_normalized = _get_query_embedding(expanded_query, embeddings_model)
        safe_print(f"[SEMANTIC MATCHER] [OK] Embedding da query gerado (dimensão: {len(query_embedding)})")
        
        # Filtrar tools por can_handle se necessário
        tools_filtered = tools
        if can_handle_filter:
            safe_print("[SEMANTIC MATCHER] Filtrando tools por can_handle...")
            tools_filtered = []
            for tool in tools:
                try:
                    if tool.can_handle(query):
                        tools_filtered.append(tool)
                except Exception as e:
                    safe_print(f"[SEMANTIC MATCHER]   [AVISO] Erro ao verificar can_handle para {tool.get_name()}: {e}")
                    tools_filtered.append(tool)  # Incluir mesmo assim em caso de erro
            safe_print(f"[SEMANTIC MATCHER] Tools após filtro can_handle: {len(tools_filtered)}/{len(tools)}")
            
            if not tools_filtered:
                safe_print("[SEMANTIC MATCHER] [AVISO] Nenhuma tool passou pelo filtro can_handle")
                return None
        
        # Obter embeddings das tools (com cache)
        safe_print("[SEMANTIC MATCHER] Obtendo embeddings das tools...")
        tool_embeddings_dict = _get_tool_embeddings_parallel(tools_filtered, embeddings_model)
        
        # Preparar arrays para cálculo vetorizado
        tool_names = []
        tool_embeddings_normalized = []
        tool_map = {}
        
        for tool in tools_filtered:
            tool_name = tool.get_name()
            if tool_name in tool_embeddings_dict:
                tool_names.append(tool_name)
                _, embedding_normalized = tool_embeddings_dict[tool_name]
                tool_embeddings_normalized.append(embedding_normalized)
                tool_map[tool_name] = tool
        
        if not tool_embeddings_normalized:
            safe_print("[SEMANTIC MATCHER] [AVISO] Nenhum embedding de tool obtido")
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
                
                all_scores.append({
                    'tool': tool_name,
                    'score': float(similarity),
                    'above_threshold': similarity >= threshold
                })
                
                if similarity > best_score:
                    best_score = float(similarity)
                    best_tool = tool
                    
            except Exception as e:
                safe_print(f"[SEMANTIC MATCHER]   [ERRO] Erro ao processar {tool_name}: {e}")
                continue
        
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        
        # Mostrar ranking completo
        safe_print("[SEMANTIC MATCHER]  RANKING DE SIMILARIDADE:")
        all_scores_sorted = sorted(all_scores, key=lambda x: x['score'], reverse=True)
        for rank, item in enumerate(all_scores_sorted, 1):
            tool_name = item['tool']
            score = item['score']
            above = "[OK]" if item['above_threshold'] else "[X]"
            marker = ">>> " if rank == 1 else "    "
            safe_print(f"[SEMANTIC MATCHER]   {marker}{rank}. {tool_name}: {score:.4f} {above}")
        
        # Decisão final
        safe_print("[SEMANTIC MATCHER] " + "=" * 70)
        safe_print(f"[SEMANTIC MATCHER] REGRA DE DECISAO:")
        safe_print(f"[SEMANTIC MATCHER]   - Score >= {semantic_match_min_score:.3f}: Tool sera executada")
        safe_print(f"[SEMANTIC MATCHER]   - Score < {semantic_match_min_score:.3f}: Nenhuma tool (fluxo normal)")
        
        if best_tool and best_score >= semantic_match_min_score:
            safe_print(f"[SEMANTIC MATCHER] [OK] TOOL SELECIONADA PARA EXECUCAO!")
            safe_print(f"[SEMANTIC MATCHER]   Tool: {best_tool.get_name()}")
            safe_print(f"[SEMANTIC MATCHER]   Score: {best_score:.4f}")
            safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (TOOL SELECIONADA) =====")
            return (best_tool, best_score)
        else:
            if best_tool:
                safe_print(f"[SEMANTIC MATCHER] [X] NENHUMA TOOL SERA EXECUTADA")
                safe_print(f"[SEMANTIC MATCHER]   Melhor tool: {best_tool.get_name()}")
                safe_print(f"[SEMANTIC MATCHER]   Melhor score: {best_score:.4f}")
                safe_print(f"[SEMANTIC MATCHER]   Score minimo necessario: {semantic_match_min_score:.3f}")
            safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (FLUXO NORMAL) =====")
            return None
            
    except Exception as e:
        safe_print(f"[SEMANTIC MATCHER] [ERRO] Erro no matching semantico: {e}")
        import traceback
        traceback.print_exc()
        safe_print("[SEMANTIC MATCHER] ===== FIM: Semantic Matching (ERRO) =====")
        return None


def find_top_tools_semantic(
    query: str,
    tools: list,
    get_embeddings_func: Callable[[], Any],
    query_expansion_enabled: bool,
    expansions: Dict[str, List[str]],
    top_n: int = 3,
    threshold: float = 0.55
) -> list[Tuple[Any, float]]:
    """
    Encontra as top N tools mais relevantes usando matching semântico.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        get_embeddings_func: Função para obter modelo de embeddings
        query_expansion_enabled: Se query expansion está habilitada
        expansions: Dicionário de expansões para query expansion
        top_n: Número máximo de tools a retornar (padrão: 3)
        threshold: Threshold mínimo de similaridade para ranking
        
    Returns:
        Lista de tuplas (tool, score) ordenadas por score decrescente
    """
    if not tools:
        safe_print("[SEMANTIC MATCHER] [AVISO] Nenhuma tool disponível")
        return []
    
    safe_print(f"[SEMANTIC MATCHER] ===== INÍCIO: find_top_tools_semantic (top_n={top_n}) =====")
    safe_print(f"[SEMANTIC MATCHER] Query: \"{query}\"")
    
    # Aplicar query expansion se habilitado
    expanded_query = expand_query(query, expansions, query_expansion_enabled)
    
    try:
        # Obter modelo de embeddings
        embeddings_model = get_embeddings_func()
        
        # Obter embedding da query expandida (usando cache se disponível)
        query_embedding, query_embedding_normalized = _get_query_embedding(expanded_query, embeddings_model)
        
        # Obter embeddings de todas as tools em paralelo (com cache)
        tool_embeddings_dict = _get_tool_embeddings_parallel(tools, embeddings_model)
        
        # Preparar arrays para cálculo vetorizado
        tool_names = []
        tool_embeddings_normalized = []
        tool_map = {}
        
        for tool in tools:
            tool_name = tool.get_name()
            if tool_name in tool_embeddings_dict:
                tool_names.append(tool_name)
                _, embedding_normalized = tool_embeddings_dict[tool_name]
                tool_embeddings_normalized.append(embedding_normalized)
                tool_map[tool_name] = tool
        
        if not tool_embeddings_normalized:
            safe_print("[SEMANTIC MATCHER] [AVISO] Nenhum embedding de tool obtido")
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
        for idx, (tool, score) in enumerate(all_scores[:10], 1):
            status = "[OK]" if score >= threshold else "[X]"
            safe_print(f"[SEMANTIC MATCHER]   {idx}. {tool.get_name()}: {score:.4f} {status}")
        if len(all_scores) > 10:
            safe_print(f"[SEMANTIC MATCHER]   ... ({len(all_scores) - 10} tools restantes)")
        
        # Filtrar por threshold e retornar top N
        filtered_scores = [(tool, score) for tool, score in all_scores if score >= threshold]
        top_tools = filtered_scores[:top_n]
        
        safe_print(f"[SEMANTIC MATCHER] [OK] Top {len(top_tools)} tools encontradas:")
        for idx, (tool, score) in enumerate(top_tools, 1):
            safe_print(f"[SEMANTIC MATCHER]   {idx}. {tool.get_name()}: {score:.4f}")
        
        if len(top_tools) >= 2:
            score_diff = top_tools[0][1] - top_tools[1][1]
            safe_print(f"[SEMANTIC MATCHER]   Diferenca 1-2: {score_diff:.4f}")
        
        safe_print("[SEMANTIC MATCHER] ===== FIM: find_top_tools_semantic =====")
        return top_tools
            
    except Exception as e:
        safe_print(f"[SEMANTIC MATCHER] [ERRO] Erro no find_top_tools_semantic: {e}")
        import traceback
        traceback.print_exc()
        return []

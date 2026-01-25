"""
Módulo para matching semântico de tools usando embeddings (DECOMP).
Usa o módulo compartilhado em shared/tools/semantic_matcher.py.
"""
from typing import Optional, Tuple, Dict, List
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.rag.vectorstore import get_embeddings
from backend.decomp.config import QUERY_EXPANSION_ENABLED, SEMANTIC_MATCH_MIN_SCORE

# Re-exportar funções do módulo compartilhado
from backend.core.semantic_matcher import (
    clear_tool_embeddings_cache,
    get_cache_stats,
    clear_query_embeddings_cache,
    preload_tool_embeddings as _shared_preload,
    expand_query as _shared_expand_query,
    find_best_tool_semantic as _shared_find_best,
    find_top_tools_semantic as _shared_find_top,
)


# Dicionário de expansões específicas para DECOMP
DECOMP_QUERY_EXPANSIONS = {
    # Variações de comandos
    r'\bme dê\b': ['me de', 'mostre', 'quero ver', 'preciso de', 'quero', 'desejo'],
    r'\bme de\b': ['me dê', 'mostre', 'quero ver', 'preciso de', 'quero'],
    r'\bmostre\b': ['me dê', 'me de', 'quero ver', 'preciso de'],
    r'\bquais são\b': ['quais', 'mostre', 'me dê', 'me de'],
    r'\bqual\b': ['quais', 'mostre', 'me dê'],
    
    # Disponibilidade
    r'\bdisponibilidade\b': ['capacidade disponível', 'potência disponível', 'potencia disponivel', 'potencia disponível'],
    r'\bcapacidade disponível\b': ['disponibilidade', 'potência disponível', 'potencia disponivel'],
    r'\bpotência disponível\b': ['disponibilidade', 'capacidade disponível', 'potencia disponivel'],
    
    # Inflexibilidade
    r'\binflexibilidade\b': ['potência mínima', 'potencia minima', 'capacidade mínima', 'capacidade minima', 'pot mínima'],
    r'\bpotência mínima\b': ['inflexibilidade', 'potencia minima', 'capacidade mínima', 'pot mínima'],
    r'\bpotencia minima\b': ['inflexibilidade', 'potência mínima', 'capacidade mínima'],
    
    # CVU (Custo Variável Unitário)
    r'\bcvu\b': ['custo variável unitário', 'custo variavel unitario', 'custo operacional', 'custo unitário variável'],
    r'\bcusto variável unitário\b': ['cvu', 'custo variavel unitario', 'custo operacional'],
    r'\bcusto operacional\b': ['cvu', 'custo variável unitário', 'custo variavel unitario'],
    
    # Carga/Demanda
    r'\bcargas mensais\b': ['demandas mensais', 'consumo mensal', 'carga mensal', 'demanda mensal'],
    r'\bcarga mensal\b': ['demanda mensal', 'consumo mensal', 'cargas mensais', 'demandas mensais'],
    r'\bdemanda mensal\b': ['carga mensal', 'consumo mensal', 'cargas mensais', 'demandas mensais'],
    r'\bdemandas mensais\b': ['cargas mensais', 'consumo mensal', 'demanda mensal', 'carga mensal'],
    r'\bconsumo mensal\b': ['carga mensal', 'demanda mensal', 'cargas mensais', 'demandas mensais'],
    r'\bcarga\b': ['demanda', 'consumo', 'necessidade'],
    r'\bdemanda\b': ['carga', 'consumo', 'necessidade'],
    
    # Submercado/Subsistema
    r'\bpor submercado\b': ['por subsistema', 'por região', 'do submercado', 'do subsistema'],
    r'\bdo submercado\b': ['do subsistema', 'por submercado', 'por subsistema'],
    r'\bsubmercado\b': ['subsistema', 'região'],
    r'\bsubsistema\b': ['submercado', 'região'],
    
    # Usinas Térmicas
    r'\busina termelétrica\b': ['ute', 'térmica', 'usina termica', 'usina térmica'],
    r'\businas termelétricas\b': ['utes', 'térmicas', 'usinas termicas'],
    r'\bute\b': ['usina termelétrica', 'térmica', 'usina termica'],
    r'\btérmica\b': ['usina termelétrica', 'ute', 'termica'],
    
    # Usinas Hidrelétricas
    r'\busina hidrelétrica\b': ['uh', 'hidrelétrica', 'usina hidreletrica', 'usina hidrelétrica'],
    r'\businas hidrelétricas\b': ['uhs', 'hidrelétricas', 'usinas hidreletricas'],
    r'\buh\b': ['usina hidrelétrica', 'hidrelétrica', 'usina hidreletrica'],
    r'\bhidrelétrica\b': ['usina hidrelétrica', 'uh', 'hidreletrica'],
    
    # Patamares
    r'\bpatamar pesada\b': ['patamar 1', 'patamar pesado', 'pesada'],
    r'\bpatamar média\b': ['patamar 2', 'patamar medio', 'média', 'media'],
    r'\bpatamar leve\b': ['patamar 3', 'leve'],
    r'\bpesada\b': ['patamar pesada', 'patamar 1'],
    r'\bmédia\b': ['patamar média', 'patamar 2', 'media'],
    r'\bleve\b': ['patamar leve', 'patamar 3'],
    
    # Estágios
    r'\bestágio 1\b': ['estagio 1', 'estágio um', 'estagio um', 'estágio i'],
    r'\bestágio\b': ['estagio', 'fase', 'período'],
}


def preload_tool_embeddings(tools: list[DECOMPTool]) -> None:
    """
    Pré-carrega os embeddings de todas as tools no cache.
    """
    _shared_preload(tools, get_embeddings)


def expand_query(query: str) -> str:
    """
    Expande a query com sinônimos e variações específicas do DECOMP.
    """
    return _shared_expand_query(query, DECOMP_QUERY_EXPANSIONS, QUERY_EXPANSION_ENABLED)


def find_best_tool_semantic(
    query: str, 
    tools: list[DECOMPTool], 
    threshold: float = 0.7
) -> Optional[Tuple[DECOMPTool, float]]:
    """
    Encontra a tool mais relevante usando matching semântico.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        threshold: Threshold mínimo de similaridade (0.0 a 1.0)
        
    Returns:
        Tupla (tool, score) se encontrada tool acima do threshold, ou None
    """
    return _shared_find_best(
        query=query,
        tools=tools,
        get_embeddings_func=get_embeddings,
        query_expansion_enabled=QUERY_EXPANSION_ENABLED,
        expansions=DECOMP_QUERY_EXPANSIONS,
        semantic_match_min_score=SEMANTIC_MATCH_MIN_SCORE,
        threshold=threshold,
        can_handle_filter=False  # Desabilitado para permitir matching semântico de todas as tools
    )


def find_top_tools_semantic(
    query: str,
    tools: list[DECOMPTool],
    top_n: int = 3,
    threshold: float = 0.55
) -> list[Tuple[DECOMPTool, float]]:
    """
    Encontra as top N tools mais relevantes usando matching semântico.
    
    Args:
        query: Query do usuário
        tools: Lista de tools disponíveis
        top_n: Número máximo de tools a retornar (padrão: 3)
        threshold: Threshold mínimo de similaridade para ranking
        
    Returns:
        Lista de tuplas (tool, score) ordenadas por score decrescente
    """
    return _shared_find_top(
        query=query,
        tools=tools,
        get_embeddings_func=get_embeddings,
        query_expansion_enabled=QUERY_EXPANSION_ENABLED,
        expansions=DECOMP_QUERY_EXPANSIONS,
        top_n=top_n,
        threshold=threshold
    )

"""
Módulo para matching semântico de tools usando embeddings (NEWAVE).
Usa o módulo compartilhado em shared/tools/semantic_matcher.py.
"""
from typing import Optional, Tuple, Dict, List
from backend.newave.tools.base import NEWAVETool
from backend.newave.rag.vectorstore import get_embeddings
from backend.newave.config import QUERY_EXPANSION_ENABLED, SEMANTIC_MATCH_MIN_SCORE

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


# Dicionário de expansões específicas para NEWAVE
NEWAVE_QUERY_EXPANSIONS = {
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


def preload_tool_embeddings(tools: list[NEWAVETool]) -> None:
    """
    Pré-carrega os embeddings de todas as tools no cache.
    """
    _shared_preload(tools, get_embeddings)


def expand_query(query: str) -> str:
    """
    Expande a query com sinônimos e variações específicas do NEWAVE.
    """
    return _shared_expand_query(query, NEWAVE_QUERY_EXPANSIONS, QUERY_EXPANSION_ENABLED)


def find_best_tool_semantic(
    query: str, 
    tools: list[NEWAVETool], 
    threshold: float = 0.7
) -> Optional[Tuple[NEWAVETool, float]]:
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
        expansions=NEWAVE_QUERY_EXPANSIONS,
        semantic_match_min_score=SEMANTIC_MATCH_MIN_SCORE,
        threshold=threshold,
        can_handle_filter=False  # NEWAVE não usa filtro can_handle
    )


def find_top_tools_semantic(
    query: str,
    tools: list[NEWAVETool],
    top_n: int = 3,
    threshold: float = 0.55
) -> list[Tuple[NEWAVETool, float]]:
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
        expansions=NEWAVE_QUERY_EXPANSIONS,
        top_n=top_n,
        threshold=threshold
    )

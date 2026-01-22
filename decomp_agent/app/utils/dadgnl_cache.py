"""
⚡ Cache global para objetos Dadgnl do DECOMP.

O RegisterFile.read() é uma operação muito lenta (faz parse do arquivo inteiro).
Este módulo implementa um cache LRU para evitar leituras repetidas.

Uso:
    from decomp_agent.app.utils.dadgnl_cache import get_cached_dadgnl
    
    dadgnl = get_cached_dadgnl(deck_path)
"""
from functools import lru_cache
from typing import Optional
from decomp_agent.app.utils.deck_loader import find_dadgnl_file
from decomp_agent.app.config import safe_print
from decomp_agent.app.utils.dadgnl import Dadgnl
import time

# Cache com até 55 decks em memória (~3-5GB RAM)
# Ajuste conforme a quantidade de decks que você usa
_CACHE_SIZE = 55


@lru_cache(maxsize=_CACHE_SIZE)
def _load_dadgnl(dadgnl_path: str) -> Dadgnl:
    """
    Carrega o Dadgnl com cache LRU.
    
    ⚠️ INTERNO: Use get_cached_dadgnl() em vez disso.
    
    Args:
        dadgnl_path: Caminho completo do arquivo dadgnl.rv*
        
    Returns:
        Objeto Dadgnl carregado com registros GL
    """
    start = time.time()
    # Criar Dadgnl (que herda de RegisterFile e especifica GL nos REGISTERS)
    dadgnl = Dadgnl.read(dadgnl_path)
    elapsed = time.time() - start
    safe_print(f"[DADGNL CACHE] ⚡ Carregado {dadgnl_path} em {elapsed:.2f}s (novo)")
    return dadgnl


def get_cached_dadgnl(deck_path: str) -> Optional[Dadgnl]:
    """
    Retorna objeto Dadgnl do cache ou carrega se não existir.
    
    Esta função deve ser usada por todas as tools em vez de Dadgnl.read() direto.
    
    Args:
        deck_path: Caminho do diretório do deck DECOMP
        
    Returns:
        Objeto Dadgnl com registros GL ou None se não encontrar o arquivo
    """
    dadgnl_path = find_dadgnl_file(deck_path)
    
    if not dadgnl_path:
        safe_print(f"[DADGNL CACHE] ❌ Arquivo dadgnl não encontrado em {deck_path}")
        return None
    
    # Verificar se já está em cache
    cache_info = _load_dadgnl.cache_info()
    
    # Carregar (do cache ou novo)
    dadgnl = _load_dadgnl(dadgnl_path)
    
    # Log se veio do cache
    new_cache_info = _load_dadgnl.cache_info()
    if new_cache_info.hits > cache_info.hits:
        safe_print(f"[DADGNL CACHE] ✅ Hit! {dadgnl_path} (cache)")
    
    return dadgnl


def clear_dadgnl_cache():
    """Limpa o cache do Dadgnl (útil para testes ou reload forçado)."""
    _load_dadgnl.cache_clear()
    safe_print("[DADGNL CACHE] 🗑️ Cache limpo")


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache."""
    info = _load_dadgnl.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0
    }

"""
⚡ Cache global para objetos Dadger do DECOMP.

O Dadger.read() é uma operação muito lenta (faz parse do arquivo inteiro).
Este módulo implementa um cache LRU para evitar leituras repetidas.

Uso:
    from decomp_agent.app.utils.dadger_cache import get_cached_dadger
    
    dadger = get_cached_dadger(deck_path)
"""
from functools import lru_cache
from typing import Optional
from idecomp.decomp import Dadger
from decomp_agent.app.utils.deck_loader import find_dadger_file
from decomp_agent.app.config import safe_print
import time

# Cache com até 55 decks em memória (~3-5GB RAM)
# Ajuste conforme a quantidade de decks que você usa
_CACHE_SIZE = 55


@lru_cache(maxsize=_CACHE_SIZE)
def _load_dadger(dadger_path: str) -> Dadger:
    """
    Carrega o Dadger com cache LRU.
    
    ⚠️ INTERNO: Use get_cached_dadger() em vez disso.
    
    Args:
        dadger_path: Caminho completo do arquivo dadger.rv*
        
    Returns:
        Objeto Dadger carregado
    """
    start = time.time()
    dadger = Dadger.read(dadger_path)
    elapsed = time.time() - start
    safe_print(f"[DADGER CACHE] ⚡ Carregado {dadger_path} em {elapsed:.2f}s (novo)")
    return dadger


def get_cached_dadger(deck_path: str) -> Optional[Dadger]:
    """
    Retorna objeto Dadger do cache ou carrega se não existir.
    
    Esta função deve ser usada por todas as tools em vez de Dadger.read() direto.
    
    Args:
        deck_path: Caminho do diretório do deck DECOMP
        
    Returns:
        Objeto Dadger ou None se não encontrar o arquivo
    """
    dadger_path = find_dadger_file(deck_path)
    
    if not dadger_path:
        safe_print(f"[DADGER CACHE] ❌ Arquivo dadger não encontrado em {deck_path}")
        return None
    
    # Verificar se já está em cache
    cache_info = _load_dadger.cache_info()
    
    # Carregar (do cache ou novo)
    dadger = _load_dadger(dadger_path)
    
    # Log se veio do cache
    new_cache_info = _load_dadger.cache_info()
    if new_cache_info.hits > cache_info.hits:
        safe_print(f"[DADGER CACHE] ✅ Hit! {dadger_path} (cache)")
    
    return dadger


def clear_dadger_cache():
    """Limpa o cache do Dadger (útil para testes ou reload forçado)."""
    _load_dadger.cache_clear()
    safe_print("[DADGER CACHE] 🗑️ Cache limpo")


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache."""
    info = _load_dadger.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0
    }

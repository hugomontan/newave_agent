"""
Utilitário para matching de nomes de usinas entre NEWAVE e DECOMP.
Normaliza nomes e faz matching fuzzy para encontrar correspondências.
"""
import re
from typing import Optional, Tuple
from difflib import SequenceMatcher

# Importar safe_print para logs
try:
    from backend.core.config import safe_print
except ImportError:
    # Fallback se não conseguir importar
    def safe_print(*args, **kwargs):
        pass


def normalize_usina_name(name: str) -> str:
    """
    Normaliza o nome de uma usina para comparação.
    
    Remove acentos, converte para minúsculas, remove espaços extras,
    e normaliza variações comuns.
    
    Args:
        name: Nome da usina
        
    Returns:
        Nome normalizado
    """
    if not name:
        return ""
    
    # Converter para minúsculas e remover espaços extras
    normalized = name.lower().strip()
    
    # Remover acentos (substituições básicas)
    replacements = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Remover caracteres especiais e normalizar espaços
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def find_usina_match(
    query: str,
    available_names: list,
    threshold: float = 0.5
) -> Optional[Tuple[str, float]]:
    """
    Encontra o melhor match de uma usina na query entre os nomes disponíveis.
    
    Usa matching fuzzy com SequenceMatcher para encontrar a melhor correspondência.
    
    Args:
        query: Query do usuário
        available_names: Lista de nomes de usinas disponíveis
        threshold: Score mínimo para considerar um match (0.0 a 1.0)
        
    Returns:
        Tupla (matched_name, score) se encontrado, None caso contrário
    """
    if not query or not available_names:
        return None
    
    query_normalized = normalize_usina_name(query)
    if not query_normalized:
        return None
    
    # Debug: mostrar query normalizada
    safe_print(f"[USINA_NAME_MATCHER] Query original: '{query}'")
    safe_print(f"[USINA_NAME_MATCHER] Query normalizada: '{query_normalized}'")
    safe_print(f"[USINA_NAME_MATCHER] Threshold: {threshold}")
    safe_print(f"[USINA_NAME_MATCHER] Nomes disponíveis: {len(available_names)}")
    
    best_match = None
    best_score = 0.0
    all_scores = []
    
    for name in available_names:
        if not name:
            continue
        
        name_normalized = normalize_usina_name(str(name))
        if not name_normalized:
            continue
        
        # Calcular similaridade usando SequenceMatcher
        # Comparar tanto o nome normalizado quanto o original
        score1 = SequenceMatcher(None, query_normalized, name_normalized).ratio()
        
        # Verificar se o nome normalizado está contido na query normalizada
        # ou vice-versa (com bônus) - MAS APENAS SE FOR PALAVRA COMPLETA
        # Isso evita matches parciais como "anta" em "santa"
        contains_bonus = False
        if name_normalized in query_normalized or query_normalized in name_normalized:
            # Verificar se é uma palavra completa usando word boundaries
            # Isso evita matches parciais como "anta" em "santa clara"
            pattern_name_in_query = r'\b' + re.escape(name_normalized) + r'\b'
            pattern_query_in_name = r'\b' + re.escape(query_normalized) + r'\b'
            
            is_word_boundary_match = (
                re.search(pattern_name_in_query, query_normalized) or 
                re.search(pattern_query_in_name, name_normalized)
            )
            
            if is_word_boundary_match:
                # Bônus apenas para palavras completas (word boundaries)
                score1 = max(score1, 0.7)
                contains_bonus = True
            # Se for substring parcial (sem word boundaries), não dar bônus
            # O SequenceMatcher já calcula a similaridade corretamente
        
        # Verificar match exato após normalização
        exact_match = False
        if query_normalized == name_normalized:
            score1 = 1.0
            exact_match = True
        
        all_scores.append((name, score1, exact_match, contains_bonus))
        
        if score1 > best_score:
            best_score = score1
            best_match = name
    
    # Debug: mostrar top 5 scores
    all_scores.sort(key=lambda x: x[1], reverse=True)
    safe_print(f"[USINA_NAME_MATCHER] Top 5 scores:")
    for idx, (name, score, exact, contains) in enumerate(all_scores[:5], 1):
        flags = []
        if exact:
            flags.append("EXATO")
        if contains:
            flags.append("CONTÉM")
        flags_str = f" [{', '.join(flags)}]" if flags else ""
        safe_print(f"[USINA_NAME_MATCHER]   {idx}. '{name}': {score:.4f}{flags_str}")
    
    if best_match and best_score >= threshold:
        safe_print(f"[USINA_NAME_MATCHER] ✅ Match encontrado: '{best_match}' (score: {best_score:.4f})")
        return (best_match, best_score)
    else:
        if best_match:
            safe_print(f"[USINA_NAME_MATCHER] ⚠️ Melhor match '{best_match}' (score: {best_score:.4f}) abaixo do threshold {threshold}")
        else:
            safe_print(f"[USINA_NAME_MATCHER] ⚠️ Nenhum match encontrado")
        return None

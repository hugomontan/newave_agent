"""
Utilitário para matching de nomes de usinas entre NEWAVE e DECOMP.
Normaliza nomes e faz matching fuzzy para encontrar correspondências.
"""
import re
from typing import Optional, Tuple
from difflib import SequenceMatcher


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
    
    best_match = None
    best_score = 0.0
    
    for name in available_names:
        if not name:
            continue
        
        name_normalized = normalize_usina_name(str(name))
        if not name_normalized:
            continue
        
        # Calcular similaridade usando SequenceMatcher
        # Comparar tanto o nome normalizado quanto o original
        score1 = SequenceMatcher(None, query_normalized, name_normalized).ratio()
        
        # Também verificar se o nome normalizado está contido na query normalizada
        # ou vice-versa (com bônus)
        if name_normalized in query_normalized or query_normalized in name_normalized:
            score1 = max(score1, 0.7)  # Bônus para matches parciais
        
        # Verificar match exato após normalização
        if query_normalized == name_normalized:
            score1 = 1.0
        
        if score1 > best_score:
            best_score = score1
            best_match = name
    
    if best_match and best_score >= threshold:
        return (best_match, best_score)
    
    return None

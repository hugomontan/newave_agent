"""
Utilitários para processamento de texto, incluindo limitação de emojis.
"""
import re


def remove_emojis(text: str) -> str:
    """
    Remove todos os emojis de um texto.
    
    Args:
        text: Texto a ser processado
        
    Returns:
        Texto sem emojis
    """
    # Padrão para remover emojis (Unicode ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


def limit_emojis(text: str, max_emojis: int = 2) -> str:
    """
    Limita o número de emojis em um texto, mantendo apenas os primeiros.
    
    Args:
        text: Texto a ser processado
        max_emojis: Número máximo de emojis a manter (padrão: 2)
        
    Returns:
        Texto com emojis limitados
    """
    # Padrão para encontrar emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]",
        flags=re.UNICODE
    )
    
    emojis = emoji_pattern.findall(text)
    
    if len(emojis) <= max_emojis:
        return text
    
    # Remover emojis extras
    emojis_to_keep = emojis[:max_emojis]
    emojis_to_remove = emojis[max_emojis:]
    
    result = text
    for emoji in emojis_to_remove:
        result = result.replace(emoji, '', 1)
    
    return result


def clean_response_text(text: str, max_emojis: int = 2) -> str:
    """
    Limpa texto de resposta, removendo emojis excessivos.
    
    Args:
        text: Texto a ser processado
        max_emojis: Número máximo de emojis a manter (padrão: 2)
        
    Returns:
        Texto limpo
    """
    return limit_emojis(text, max_emojis)


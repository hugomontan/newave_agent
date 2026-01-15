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


def normalize_markdown_tables(text: str) -> str:
    """
    Normaliza tabelas markdown para garantir que sejam renderizadas corretamente.
    Garante que cada linha da tabela esteja em uma linha separada.
    
    Args:
        text: Texto markdown a ser normalizado
        
    Returns:
        Texto markdown normalizado
    """
    lines = text.split('\n')
    normalized_lines = []
    in_table = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detectar início de tabela (linha com |)
        if '|' in stripped and not in_table:
            in_table = True
            normalized_lines.append(line)
            continue
        
        # Se estamos em uma tabela
        if in_table:
            # Se a linha contém |, é parte da tabela
            if '|' in stripped:
                normalized_lines.append(line)
            # Se a linha está vazia, pode ser separador ou fim da tabela
            elif not stripped:
                # Verificar se a próxima linha também não tem |
                if i + 1 < len(lines) and '|' not in lines[i + 1].strip():
                    in_table = False
                normalized_lines.append(line)
            # Se não tem | e não está vazia, saiu da tabela
            else:
                in_table = False
                normalized_lines.append(line)
        else:
            normalized_lines.append(line)
    
    return '\n'.join(normalized_lines)


def clean_response_text(text: str, max_emojis: int = 2) -> str:
    """
    Limpa texto de resposta, removendo emojis excessivos e normalizando markdown.
    
    Args:
        text: Texto a ser processado
        max_emojis: Número máximo de emojis a manter (padrão: 2)
        
    Returns:
        Texto limpo e normalizado
    """
    # Primeiro normalizar tabelas markdown
    text = normalize_markdown_tables(text)
    # Depois limitar emojis
    return limit_emojis(text, max_emojis)

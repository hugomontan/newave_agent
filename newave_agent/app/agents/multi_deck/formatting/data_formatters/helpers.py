"""
Funções auxiliares comuns para formatters temporais.
Extraídas de temporal_formatters.py para reduzir duplicação de código.
"""
from typing import Dict, Any, List, Set, Optional, Tuple
from newave_agent.app.agents.multi_deck.formatting.base import DeckData


def extract_data_from_all_decks(
    decks_data: List[DeckData],
    data_key: str = "data",
    fallback_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extrai dados de todos os decks usando uma chave específica.
    
    Args:
        decks_data: Lista de DeckData
        data_key: Chave para acessar os dados (padrão: "data")
        fallback_key: Chave alternativa se data_key não existir
        
    Returns:
        Lista de todos os registros de todos os decks
    """
    all_data = []
    for deck in decks_data:
        result = deck.result
        data = result.get(data_key, [])
        if not data and fallback_key:
            data = result.get(fallback_key, [])
        if isinstance(data, list):
            all_data.extend(data)
    return all_data


def get_unique_periods(
    data: List[Dict[str, Any]],
    period_key_func: callable
) -> Set[str]:
    """
    Obtém todos os períodos únicos de uma lista de dados.
    
    Args:
        data: Lista de registros
        period_key_func: Função que extrai a chave do período de um registro
        
    Returns:
        Set de chaves de período únicas
    """
    periods = set()
    for record in data:
        period_key = period_key_func(record)
        if period_key:
            periods.add(period_key)
    return periods


def index_data_by_period(
    data: List[Dict[str, Any]],
    period_key_func: callable,
    value_key: str = "valor",
    sanitize_func: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Indexa dados por período.
    
    Args:
        data: Lista de registros
        period_key_func: Função que extrai a chave do período
        value_key: Chave do valor a ser indexado
        sanitize_func: Função opcional para sanitizar valores
        
    Returns:
        Dicionário {periodo_key: valor}
    """
    indexed = {}
    for record in data:
        periodo_key = period_key_func(record)
        if periodo_key:
            valor = record.get(value_key)
            if sanitize_func:
                valor = sanitize_func(valor)
            if valor is not None:
                if periodo_key not in indexed:
                    indexed[periodo_key] = valor
    return indexed


def remove_duplicates(
    data: List[Dict[str, Any]],
    key_fields: List[str]
) -> List[Dict[str, Any]]:
    """
    Remove duplicatas de uma lista de dicionários baseado em campos-chave.
    
    Args:
        data: Lista de registros
        key_fields: Lista de campos que formam a chave única
        
    Returns:
        Lista sem duplicatas
    """
    seen = set()
    unique_data = []
    for record in data:
        key_tuple = tuple(record.get(field) for field in key_fields)
        if key_tuple not in seen:
            seen.add(key_tuple)
            unique_data.append(record)
    return unique_data


def build_decks_info(
    decks_data: List[DeckData],
    extract_func: callable
) -> List[Dict[str, Any]]:
    """
    Constrói lista de informações de decks usando uma função de extração.
    
    Args:
        decks_data: Lista de DeckData
        extract_func: Função que extrai informações de um deck (recebe deck, result)
        
    Returns:
        Lista de dicionários com informações dos decks
    """
    decks_info = []
    for deck in decks_data:
        result = deck.result
        info = extract_func(deck, result)
        if info:
            info["deck"] = deck
            info["display_name"] = deck.display_name
            decks_info.append(info)
    return decks_info


def get_period_key_from_record(
    record: Dict[str, Any],
    ano_key: str = "ano",
    mes_key: str = "mes",
    ano_mes_key: Optional[str] = None
) -> Optional[str]:
    """
    Extrai chave de período de um registro.
    
    Args:
        record: Registro de dados
        ano_key: Chave do ano
        mes_key: Chave do mês
        ano_mes_key: Chave alternativa que já contém "ano-mes"
        
    Returns:
        String no formato "YYYY-MM" ou None
    """
    if ano_mes_key and ano_mes_key in record:
        return record[ano_mes_key]
    
    ano = record.get(ano_key)
    mes = record.get(mes_key)
    
    if ano is not None and mes is not None:
        return f"{ano}-{mes:02d}" if isinstance(mes, int) else f"{ano}-{mes}"
    
    return None

"""
Utilitários para manipulação de JSON.
"""
import json
import math
from typing import Any


def clean_nan_for_json(obj: Any) -> Any:
    """
    Remove valores NaN, Infinity e -Infinity de estruturas de dados
    para permitir serialização JSON válida.
    
    Args:
        obj: Objeto a ser limpo (dict, list, ou valor primitivo)
        
    Returns:
        Objeto com NaN/Infinity substituídos por None ou strings
    """
    if isinstance(obj, dict):
        return {key: clean_nan_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
        elif math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        else:
            return obj
    else:
        return obj

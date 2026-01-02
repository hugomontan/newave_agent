"""
Funções auxiliares para formatação de tools.
"""

from typing import List, Dict, Any


def format_number_for_display(value: float, threshold: float = 1e10) -> str:
    """
    Formata um número para exibição, usando notação científica para valores muito grandes.
    
    Args:
        value: Valor numérico a formatar
        threshold: Limite acima do qual usar notação científica
        
    Returns:
        String formatada
    """
    if not isinstance(value, (int, float)):
        return str(value)
    
    # Valores muito grandes (absoluto >= 1e10) ou muito pequenos (absoluto < 1e-3 e != 0): usar notação científica
    # Valores como -1.0999999999999999e+36 devem ser formatados em notação científica
    if abs(value) >= threshold or (abs(value) < 1e-3 and value != 0):
        # Formatar em notação científica com 2 casas decimais
        return f"{value:.2e}"
    elif abs(value) >= 1e30:  # Valores extremamente grandes (como -1.0999999999999999e+36)
        # Formatar em notação científica com 2 casas decimais
        return f"{value:.2e}"
    else:
        # Formatar com separador de milhar e 2 casas decimais
        return f"{value:,.2f}"


def format_restricao_eletrica_data(dados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formata os dados de restrições elétricas, convertendo valores muito grandes
    para notação científica.
    
    Args:
        dados: Lista de dicionários com dados de restrições elétricas
        
    Returns:
        Lista de dicionários formatados
    """
    dados_formatados = []
    for registro in dados:
        registro_formatado = registro.copy()
        
        # Formatar lim_inf e lim_sup se existirem
        if 'lim_inf' in registro_formatado:
            valor = registro_formatado['lim_inf']
            if isinstance(valor, (int, float)):
                registro_formatado['lim_inf'] = format_number_for_display(valor)
        
        if 'lim_sup' in registro_formatado:
            valor = registro_formatado['lim_sup']
            if isinstance(valor, (int, float)):
                registro_formatado['lim_sup'] = format_number_for_display(valor)
        
        dados_formatados.append(registro_formatado)
    
    return dados_formatados


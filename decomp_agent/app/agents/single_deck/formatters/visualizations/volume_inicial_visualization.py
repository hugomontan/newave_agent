"""
Módulo de visualização específico para volume inicial/nível de partida de usinas hidrelétricas.
Módulo separado e modularizado para reutilização.
"""

from typing import Dict, Any, Optional


def create_volume_inicial_visualization(
    volume_inicial: float,
    usina: Dict[str, Any],
    unidade: str,
    tool_name: str,
    data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria dados de visualização para volume inicial de usina hidrelétrica.
    
    Retorna uma tabela simples com as colunas: usina, código, REE, data, volume inicial.
    
    Args:
        volume_inicial: Valor do volume inicial em % do volume útil
        usina: Dict com informações da usina (código, nome, codigo_ree)
        unidade: Unidade de medida (ex: "% do volume útil")
        tool_name: Nome da tool que gerou os dados
        data: Data do registro (opcional, se não fornecido usa data atual)
        
    Returns:
        Dict com dados de visualização estruturados para o frontend
    """
    from datetime import datetime
    
    nome_usina = usina.get("nome", f"Usina {usina.get('codigo', 'N/A')}")
    codigo_usina = usina.get("codigo")
    codigo_ree = usina.get("codigo_ree")
    
    # Se data não fornecida, usar data atual
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    
    # Tabela simples com apenas as 4 colunas solicitadas: usina, código, data, volume_inicial
    # Formatar volume inicial apenas como "X%" (sem adicionar unidade completa)
    table_data = [
        {
            "usina": nome_usina,
            "codigo": codigo_usina,
            "data": data,
            "volume_inicial": f"{volume_inicial}%"
        }
    ]
    
    visualization_data = {
        "visualization_type": "table_only",
        "tool_name": tool_name,
        "table": table_data,
        "chart_data": None,
    }
    
    return visualization_data


def create_volume_inicial_comparison_visualization(
    volumes_iniciais: list[Dict[str, Any]],
    tool_name: str
) -> Dict[str, Any]:
    """
    Cria dados de visualização para comparação de volumes iniciais de múltiplas usinas.
    
    Módulo separado para visualização de comparação (útil para multi-deck no futuro).
    
    Args:
        volumes_iniciais: Lista de dicts com volume_inicial e usina
        tool_name: Nome da tool que gerou os dados
        
    Returns:
        Dict com dados de visualização para comparação
    """
    # Preparar dados para gráfico de barras
    chart_data = {
        "type": "bar",
        "labels": [v["usina"]["nome"] for v in volumes_iniciais],
        "datasets": [
            {
                "label": "Volume Inicial (%)",
                "data": [v["volume_inicial"] for v in volumes_iniciais],
            }
        ],
    }
    
    # Preparar dados para tabela
    table_data = [
        {
            "usina": v["usina"]["nome"],
            "codigo": v["usina"]["codigo"],
            "volume_inicial": v["volume_inicial"],
            "ree": v["usina"].get("codigo_ree"),
        }
        for v in volumes_iniciais
    ]
    
    return {
        "visualization_type": "volume_inicial_comparison",
        "tool_name": tool_name,
        "chart_data": chart_data,
        "table_data": table_data,
    }

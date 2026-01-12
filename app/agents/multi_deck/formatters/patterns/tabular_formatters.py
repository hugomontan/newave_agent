"""
Formatters para dados tabulares - multi-deck.
Dados tabulares: dados em formato de tabela simples.
"""

from typing import Dict, Any
from app.agents.multi_deck.formatters.base import ComparisonFormatter


class TableComparisonFormatter(ComparisonFormatter):
    """
    Formatter genérico para dados tabulares.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se o resultado contém dados tabulares."""
        # Verificar se tem estrutura de tabela (lista de dicionários)
        if "data" in result_structure:
            data = result_structure["data"]
            if isinstance(data, list) and len(data) > 0:
                return isinstance(data[0], dict)
        return False
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: str = None,
        deck_2_name: str = None
    ) -> Dict[str, Any]:
        """
        Formata comparação de dados tabulares.
        """
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "llm_free"
        }
    
    def get_priority(self) -> int:
        return 2

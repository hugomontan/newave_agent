"""
Formatter para CadicTool no single deck.
"""
from typing import Dict, Any
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.shared.formatting.data_processors.carga_processor import CargaDataProcessor
from app.agents.single_deck.formatters.text_formatters.simple import format_cadic_simple


class CadicSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para CadicTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar CadicTool."""
        return tool_name == "CadicTool" and (
            "data" in result_structure or "dados_por_submercado" in result_structure
        )
    
    def get_priority(self) -> int:
        """Alta prioridade."""
        return 90
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de CadicTool."""
        table_data = CargaDataProcessor.extract_table_data(tool_result)
        chart_data = CargaDataProcessor.extract_chart_data(tool_result)
        
        final_response = format_cadic_simple(table_data)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "table_with_line_chart",
                "chart_config": {
                    "type": "line",
                    "title": "Carga Adicional por Submercado",
                    "x_axis": "Período",
                    "y_axis": "Carga Adicional (MWméd)"
                },
                "tool_name": "CadicTool"
            }
        }

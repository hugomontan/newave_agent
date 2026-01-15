"""
Formatter para DsvaguaTool no single deck.
"""
from typing import Dict, Any
from newave_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from newave_agent.app.agents.shared.formatting.data_processors.vazoes_processor import VazoesDataProcessor
from newave_agent.app.agents.single_deck.formatters.text_formatters.simple import format_dsvagua_simple


class DsvaguaSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para DsvaguaTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar DsvaguaTool."""
        return tool_name == "DsvaguaTool" and ("dados" in result_structure or "data" in result_structure)
    
    def get_priority(self) -> int:
        """Prioridade média-alta."""
        return 80
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de DsvaguaTool."""
        table_data = VazoesDataProcessor.extract_table_data(tool_result)
        chart_data = VazoesDataProcessor.extract_chart_data(tool_result)
        
        final_response = format_dsvagua_simple(table_data)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "line_chart",
                "chart_config": {
                    "type": "line",
                    "title": "Desvios de Água",
                    "x_axis": "Período",
                    "y_axis": "Desvio (m³/s)"
                },
                "tool_name": "DsvaguaTool"
            }
        }

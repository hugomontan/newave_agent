"""
Formatter para VazoesTool no single deck.
"""
from typing import Dict, Any
from newave_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from newave_agent.app.agents.shared.formatting.data_processors.vazoes_processor import VazoesDataProcessor
from newave_agent.app.agents.single_deck.formatters.text_formatters.simple import format_vazoes_simple


class VazoesSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para VazoesTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar VazoesTool."""
        return tool_name == "VazoesTool" and "data" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade média-alta."""
        return 80
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de VazoesTool."""
        table_data = VazoesDataProcessor.extract_table_data(tool_result)
        chart_data = VazoesDataProcessor.extract_chart_data(tool_result)
        
        # Construir título dinâmico
        title_suffix = ""
        summary = tool_result.get("summary", {})
        filtro_info = summary.get("filtro_aplicado") or {}
        
        if filtro_info:
            nome_usina = filtro_info.get("nome_usina")
            posto = filtro_info.get("posto")
            
            if nome_usina:
                title_suffix = f" - {nome_usina}"
                if posto:
                    title_suffix += f" (Posto {posto})"
            elif posto:
                title_suffix = f" - Posto {posto}"
        
        # Se não encontrou no filtro, tentar pegar do primeiro registro
        if not title_suffix and table_data:
            nome_posto = table_data[0].get("nome_posto")
            if nome_posto:
                title_suffix = f" - {nome_posto}"
        
        chart_title = f"Vazões Históricas{title_suffix}"
        
        final_response = format_vazoes_simple(table_data, title_suffix)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "line_chart",
                "chart_config": {
                    "type": "line",
                    "title": chart_title,
                    "x_axis": "Período",
                    "y_axis": "Vazão (m³/s)"
                },
                "tool_name": "VazoesTool"
            }
        }

"""
Formatter para CargaMensalTool no single deck.
"""
from typing import Dict, Any
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.shared.formatting.data_processors.carga_processor import CargaDataProcessor
from backend.newave.agents.single_deck.formatters.text_formatters.simple import format_carga_mensal_simple


class CargaMensalSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para CargaMensalTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar CargaMensalTool."""
        return tool_name == "CargaMensalTool" and (
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
        """Formata resposta de CargaMensalTool."""
        table_data = CargaDataProcessor.extract_table_data(tool_result)
        chart_data = CargaDataProcessor.extract_chart_data(tool_result)
        
        # Extrair informações dos submercados para criar título descritivo
        submercados_info = []
        if table_data:
            # Agrupar por submercado para obter código e nome
            submercados_vistos = {}
            for row in table_data:
                codigo = row.get("codigo_submercado")
                nome = row.get("submercado", "")
                if codigo and codigo not in submercados_vistos:
                    submercados_vistos[codigo] = nome
            
            # Criar lista de informações
            for codigo, nome in submercados_vistos.items():
                if nome and nome != f"Subsistema {codigo}":
                    submercados_info.append(f"Subsistema {codigo} ({nome})")
                else:
                    submercados_info.append(f"Subsistema {codigo}")
        
        # Criar título descritivo
        if submercados_info:
            titulo = f"Carga Mensal - {', '.join(submercados_info)}"
        else:
            titulo = "Carga Mensal"
        
        final_response = format_carga_mensal_simple(table_data, titulo)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "table_with_line_chart",
                "chart_config": {
                    "type": "line",
                    "title": titulo,
                    "x_axis": "Período",
                    "y_axis": "Carga (MWméd)"
                },
                "tool_name": "CargaMensalTool"
            }
        }

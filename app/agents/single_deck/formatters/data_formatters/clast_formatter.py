"""
Formatter para ClastValoresTool no single deck.
"""
from typing import Dict, Any
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.shared.formatting.data_processors.clast_processor import ClastDataProcessor
from app.agents.single_deck.formatters.text_formatters.simple import format_clast_simple


class ClastSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para ClastValoresTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar ClastValoresTool."""
        return tool_name == "ClastValoresTool" and (
            "dados_estruturais" in result_structure or 
            "dados_conjunturais" in result_structure
        )
    
    def get_priority(self) -> int:
        """Alta prioridade - muito específico."""
        return 100
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de ClastValoresTool."""
        is_cvu = ClastDataProcessor._is_cvu_query(query)
        
        table_data = ClastDataProcessor.extract_table_data(tool_result, is_cvu)
        chart_data = ClastDataProcessor.extract_chart_data(tool_result, is_cvu)
        
        # Extrair informações da usina/classe para criar título descritivo
        titulo_base = "Custo Variável Unitário (CVU)" if is_cvu else "Custos de Classes Térmicas"
        titulo_completo = titulo_base
        
        filtros = tool_result.get("filtros", {})
        if filtros and "classe" in filtros:
            classe_info = filtros["classe"]
            nome_usina = classe_info.get("nome", "")
            codigo_usina = classe_info.get("codigo")
            
            if nome_usina and codigo_usina is not None:
                titulo_completo = f"{titulo_base} - {nome_usina.upper()} (USINA {codigo_usina})"
            elif nome_usina:
                titulo_completo = f"{titulo_base} - {nome_usina.upper()}"
            elif codigo_usina is not None:
                titulo_completo = f"{titulo_base} - USINA {codigo_usina}"
        
        final_response = format_clast_simple(table_data, is_cvu, titulo_completo)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "chart_data": chart_data,
                "visualization_type": "table_with_line_chart",
                "chart_config": {
                    "type": "line",
                    "title": titulo_completo,
                    "x_axis": "Ano",
                    "y_axis": "CVU (R$/MWh)" if is_cvu else "Custo (R$/MWh)"
                },
                "tool_name": "ClastValoresTool"
            }
        }

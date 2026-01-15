"""
Formatter para TermCadastroTool no single deck.
"""
from typing import Dict, Any
from newave_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from newave_agent.app.agents.shared.formatting.data_processors.cadastro_processor import CadastroDataProcessor
from newave_agent.app.agents.single_deck.formatters.text_formatters.simple import format_cadastro_term_simple


class CadastroTermSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para TermCadastroTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar TermCadastroTool."""
        return tool_name == "TermCadastroTool" and ("data" in result_structure or "dados_usina" in result_structure)
    
    def get_priority(self) -> int:
        """Prioridade média."""
        return 70
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de TermCadastroTool."""
        table_data = CadastroDataProcessor.extract_table_data(tool_result)
        
        final_response = format_cadastro_term_simple(table_data)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "visualization_type": "table_only",
                "tool_name": "TermCadastroTool"
            }
        }

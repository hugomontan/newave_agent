"""
Formatter genérico para single deck - usa LLM para formatar qualquer tool.
"""

from typing import Dict, Any
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class GenericSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter genérico que usa LLM para formatar qualquer tool.
    Fallback quando não há formatter específico.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Sempre pode formatar (fallback)."""
        return True
    
    def get_priority(self) -> int:
        """Prioridade muito baixa - apenas fallback."""
        return -1
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta usando LLM (simplificado por enquanto).
        TODO: Implementar integração com LLM quando helpers estiverem criados.
        """
        # Por enquanto, formatação básica
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"## Erro\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        if not data:
            return {
                "final_response": "## Resultado\n\nNenhum dado encontrado.",
                "visualization_data": None
            }
        
        # Formatação básica
        response_parts = ["## Resultado\n\n"]
        response_parts.append(f"Total de registros: {len(data)}\n\n")
        
        # Primeiros 10 registros
        for i, record in enumerate(data[:10], 1):
            response_parts.append(f"### Registro {i}\n\n")
            for key, value in record.items():
                response_parts.append(f"- **{key}**: {value}\n")
            response_parts.append("\n")
        
        if len(data) > 10:
            response_parts.append(f"\n*... e mais {len(data) - 10} registros*\n")
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": None
        }

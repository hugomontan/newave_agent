"""
Formatadores com liberdade total para LLM interpretar.
Para tools que não precisam de estruturação rígida.
"""
from typing import Dict, Any
from app.comparison.base import ComparisonFormatter


class LLMFreeFormatter(ComparisonFormatter):
    """
    Formatador genérico com liberdade total para LLM.
    Para tools como LimitesIntercambioTool, AgrintTool, RestricaoEletricaTool.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        # Este é o fallback - sempre retorna True mas com baixa prioridade
        return True
    
    def get_priority(self) -> int:
        return 1  # Prioridade muito baixa - usado apenas como fallback
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação com liberdade total para LLM.
        Retorna dados brutos sem estruturação pré-definida.
        """
        return {
            "comparison_table": None,
            "chart_data": None,
            "visualization_type": "llm_free",
            "raw_data_dec": result_dec,
            "raw_data_jan": result_jan,
            "llm_context": {
                "tool_name": tool_name,
                "query": query
            }
        }


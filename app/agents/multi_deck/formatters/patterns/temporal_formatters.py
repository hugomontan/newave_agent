"""
Formatters para dados temporais (multi-deck).
Dados temporais: dados que variam ao longo do tempo (anos, meses, períodos).
"""

from typing import Dict, Any, List, Optional
from app.agents.multi_deck.formatters.base import ComparisonFormatter
from app.config import safe_print


class ClastComparisonFormatter(ComparisonFormatter):
    """
    Formatter para comparação de dados do CLAST (valores estruturais e conjunturais).
    Dados temporais: custos por ano de estudo.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados do ClastValoresTool."""
        return tool_name == "ClastValoresTool"
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formata comparação de dados do CLAST.
        
        Args:
            result_dec: Resultado do deck de dezembro
            result_jan: Resultado do deck de janeiro
            tool_name: Nome da tool
            query: Query original
            deck_1_name: Nome do deck 1 (opcional)
            deck_2_name: Nome do deck 2 (opcional)
            
        Returns:
            Dict com comparison_table, chart_data, visualization_type
        """
        from app.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
        
        # Usar lógica do MultiDeckComparisonTool para construir tabela
        # Criar instância temporária apenas para usar métodos auxiliares
        temp_tool = MultiDeckComparisonTool(None, None, None, None)
        
        # Extrair dados
        data_dec = self._extract_data(result_dec)
        data_jan = self._extract_data(result_jan)
        
        if not data_dec or not data_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart"
            }
        
        # Construir tabela de comparação
        comparison_table, chart_data = temp_tool._build_comparison_table(data_dec, data_jan)
        
        # Formatar para o formato esperado pelo frontend
        formatted_table = []
        for item in comparison_table:
            formatted_table.append({
                "data": item.get("period", ""),
                "deck_1": item.get("deck_1_value", 0),
                "deck_2": item.get("deck_2_value", 0),
                "diferenca": item.get("difference", 0),
                "diferenca_percent": item.get("difference_percent", 0)
            })
        
        return {
            "comparison_table": formatted_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart"
        }
    
    def _extract_data(self, result: Dict[str, Any]) -> List[Dict]:
        """Extrai dados do resultado da tool."""
        # Tentar diferentes campos possíveis
        if "dados_estruturais" in result:
            return result["dados_estruturais"]
        if "dados_conjunturais" in result:
            return result["dados_conjunturais"]
        if "data" in result:
            return result["data"]
        return []
    
    def get_priority(self) -> int:
        return 10


class CargaComparisonFormatter(ComparisonFormatter):
    """
    Formatter para comparação de dados de carga mensal.
    Dados temporais: carga por mês e submercado.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados do CargaMensalTool."""
        return tool_name == "CargaMensalTool"
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formata comparação de dados de carga mensal.
        """
        from app.tools.multi_deck_comparison_tool import MultiDeckComparisonTool
        
        temp_tool = MultiDeckComparisonTool(None, None, None, None)
        
        data_dec = self._extract_data(result_dec)
        data_jan = self._extract_data(result_jan)
        
        if not data_dec or not data_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart"
            }
        
        comparison_table, chart_data = temp_tool._build_comparison_table(data_dec, data_jan)
        
        formatted_table = []
        for item in comparison_table:
            formatted_table.append({
                "data": item.get("period", ""),
                "deck_1": item.get("deck_1_value", 0),
                "deck_2": item.get("deck_2_value", 0),
                "diferenca": item.get("difference", 0),
                "diferenca_percent": item.get("difference_percent", 0)
            })
        
        return {
            "comparison_table": formatted_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart"
        }
    
    def _extract_data(self, result: Dict[str, Any]) -> List[Dict]:
        """Extrai dados do resultado da tool."""
        if "data" in result:
            return result["data"]
        if "dados_por_submercado" in result:
            # Flatten dados por submercado
            all_data = []
            for submercado_data in result["dados_por_submercado"].values():
                if isinstance(submercado_data, dict) and "dados" in submercado_data:
                    all_data.extend(submercado_data["dados"])
            return all_data
        return []
    
    def get_priority(self) -> int:
        return 10


class VazoesComparisonFormatter(ComparisonFormatter):
    """Formatter para comparação de vazões históricas."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "VazoesTool"
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formata comparação de vazões."""
        # Implementação básica - pode ser expandida
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "llm_free"
        }
    
    def get_priority(self) -> int:
        return 5


class UsinasNaoSimuladasFormatter(ComparisonFormatter):
    """Formatter para comparação de usinas não simuladas."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "UsinasNaoSimuladasTool"
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formata comparação de usinas não simuladas."""
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "llm_free"
        }
    
    def get_priority(self) -> int:
        return 5


class LimitesIntercambioComparisonFormatter(ComparisonFormatter):
    """Formatter para comparação de limites de intercâmbio."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "LimitesIntercambioTool"
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formata comparação de limites de intercâmbio."""
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "llm_free"
        }
    
    def get_priority(self) -> int:
        return 5

"""
Interface base para formatadores de comparação multi-deck.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ComparisonFormatter(ABC):
    """
    Classe base abstrata para formatadores de comparação.
    
    Cada formatador é especializado para um tipo específico de tool
    e gera visualizações otimizadas (tabelas, gráficos, diff lists).
    """
    
    @abstractmethod
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """
        Verifica se este formatador pode processar o resultado desta tool.
        
        Args:
            tool_name: Nome da tool (ex: "ClastValoresTool")
            result_structure: Estrutura do resultado da tool (para verificar campos)
            
        Returns:
            True se pode formatar, False caso contrário
        """
        pass
    
    @abstractmethod
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata a comparação entre dois decks.
        
        Args:
            result_dec: Resultado completo da tool para deck de dezembro
            result_jan: Resultado completo da tool para deck de janeiro
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com:
            - comparison_table: List[Dict] - Tabela comparativa (opcional)
            - chart_data: Dict - Dados para gráfico Chart.js (opcional)
            - visualization_type: str - Tipo de visualização
            - chart_config: Dict - Configurações específicas do gráfico (opcional)
            - llm_context: Dict - Contexto adicional para LLM (opcional)
        """
        pass
    
    def get_priority(self) -> int:
        """
        Retorna a prioridade do formatador.
        
        Formatadores com maior prioridade têm precedência quando múltiplos
        formatadores podem processar a mesma tool.
        
        Returns:
            Prioridade (maior = mais específico). Padrão: 0
        """
        return 0


"""
Interface base para formatters de single deck.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SingleDeckFormatter(ABC):
    """
    Interface base para formatters de single deck.
    Cada tool pode ter seu próprio formatter específico.
    """
    
    @abstractmethod
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """
        Verifica se este formatador pode processar o resultado desta tool.
        
        Args:
            tool_name: Nome da tool (ex: "UHUsinasHidrelétricasTool")
            result_structure: Estrutura do resultado da tool (para verificar campos)
            
        Returns:
            True se pode formatar, False caso contrário
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
    
    @abstractmethod
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta de uma tool para single deck.
        
        Args:
            tool_result: Resultado da execução da tool
            tool_name: Nome da tool
            query: Query original do usuário
            
        Returns:
            Dict com:
            - final_response: str - Resposta formatada em Markdown
            - visualization_data: Optional[Dict] - Dados de visualização estruturados (opcional)
        """
        pass

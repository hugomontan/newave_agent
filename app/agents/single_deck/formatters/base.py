"""
Interface base para formatters de single deck.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class SingleDeckFormatter(ABC):
    """
    Interface base para formatters de single deck.
    Cada tool pode ter seu próprio formatter específico.
    """
    
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
            - data: Any - Dados estruturados (opcional)
        """
        pass

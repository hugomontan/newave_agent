"""
Interface base para formatters de single deck do DESSEM.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class SingleDeckFormatter(ABC):
    """
    Interface base para formatters de single deck.
    Cada tool pode ter seu próprio formatter específico.
    """

    @abstractmethod
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se este formatador pode processar o resultado desta tool."""
        raise NotImplementedError

    def get_priority(self) -> int:
        """
        Prioridade do formatter.
        Maior prioridade tem precedência quando múltiplos formatters
        podem processar a mesma tool.
        """
        return 0

    @abstractmethod
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Formata resposta de uma tool para single deck.

        Deve retornar:
            - final_response: str (Markdown)
            - visualization_data: Optional[Dict]
        """
        raise NotImplementedError


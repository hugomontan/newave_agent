"""
Interface base para formatadores de comparação multi-deck.
Suporta N decks para comparação dinâmica.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DeckData:
    """
    Wrapper para dados de um deck individual.
    
    Attributes:
        name: Nome do deck (ex: "DC202501-sem1")
        display_name: Nome amigável (ex: "Janeiro 2025 - Semana 1")
        result: Resultado da tool para este deck
        success: Se a execução foi bem-sucedida
        error: Mensagem de erro (se houver)
    """
    name: str
    display_name: str
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    
    @property
    def has_data(self) -> bool:
        """Verifica se o deck tem dados válidos."""
        return self.success and self.result is not None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Acessa um campo do resultado."""
        if self.result is None:
            return default
        return self.result.get(key, default)


class ComparisonFormatter(ABC):
    """
    Classe base abstrata para formatadores de comparação.
    
    Cada formatador é especializado para um tipo específico de tool
    e gera visualizações otimizadas (tabelas, gráficos, diff lists).
    
    Suporta comparação de N decks com comportamento adaptativo:
    - 2 decks: comparação direta (antes/depois)
    - N decks: evolução histórica/temporal
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
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata a comparação entre N decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente (mais antigo primeiro)
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com:
            - comparison_table: List[Dict] - Tabela comparativa (opcional)
            - chart_data: Dict - Dados para gráfico Chart.js (opcional)
            - visualization_type: str - Tipo de visualização
            - chart_config: Dict - Configurações específicas do gráfico (opcional)
            - deck_names: List[str] - Nomes dos decks comparados
            - is_multi_deck: bool - True se >2 decks
        """
        pass

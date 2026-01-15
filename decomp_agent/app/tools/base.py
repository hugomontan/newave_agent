"""
Classe base para tools do DECOMP.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class DECOMPTool(ABC):
    """
    Classe base abstrata para todas as tools do DECOMP.
    
    Cada tool deve implementar:
    - can_handle(): Verifica se pode processar a query
    - execute(): Executa a tool e retorna dados
    - get_description(): Retorna descrição para o LLM
    """
    
    def __init__(self, deck_path: str):
        """
        Inicializa a tool com o caminho do deck.
        
        Args:
            deck_path: Caminho do diretório do deck DECOMP
        """
        self.deck_path = deck_path
    
    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a tool pode processar a query.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar, False caso contrário
        """
        pass
    
    @abstractmethod
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a tool e retorna os dados processados.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com:
            - success: bool - Se a execução foi bem-sucedida
            - data: List[Dict] - Dados processados (se success=True)
            - error: str - Mensagem de erro (se success=False)
            - summary: Dict - Estatísticas resumidas (opcional)
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada da tool
        """
        pass
    
    def get_name(self) -> str:
        """Retorna o nome da tool."""
        return self.__class__.__name__

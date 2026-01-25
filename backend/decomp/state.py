"""
Estado compartilhado entre os nodes do Single Deck Agent DECOMP.
"""
from typing import TypedDict, List, Optional, Any


class SingleDeckState(TypedDict):
    """Estado compartilhado entre os nodes do LangGraph para Single Deck DECOMP."""
    
    query: str
    deck_path: str
    final_response: str
    error: Optional[str]
    messages: List[Any]
    
    # Campos para Tools pré-programadas
    tool_route: bool  # True se tool foi executada
    tool_result: Optional[dict]  # Resultado da tool
    tool_used: Optional[str]  # Nome da tool usada
    
    # Campos para Disambiguation
    disambiguation: Optional[dict]
    
    # Campos para Comparação (usado para comparison_data do single deck)
    comparison_data: Optional[dict]  # Dados de comparação/visualização
    
    # Campos para Visualização Single Deck
    visualization_data: Optional[dict]  # Dados de visualização estruturados
    
    # Campos para escolha do usuário (requires_user_choice)
    requires_user_choice: Optional[bool]  # True quando tool requer escolha do usuário
    alternative_type: Optional[str]  # Tipo alternativo disponível

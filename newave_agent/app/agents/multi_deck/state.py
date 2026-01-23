"""
Estado compartilhado entre os nodes do Multi-Deck Agent.
Suporta N decks para comparação.
"""

from typing import TypedDict, List, Optional, Any, Dict


class MultiDeckState(TypedDict):
    """Estado compartilhado entre os nodes do LangGraph para Multi-Deck."""
    
    query: str
    deck_path: str  # Path do primeiro deck (para compatibilidade)
    
    # Campos para N decks dinâmicos
    selected_decks: List[str]  # Lista de nomes dos decks selecionados (ex: ["NW202501", "NW202512"])
    deck_paths: Dict[str, str]  # Mapeamento nome -> caminho (ex: {"NW202501": "/path/to/deck"})
    deck_display_names: Dict[str, str]  # Mapeamento nome -> nome amigável (ex: {"NW202501": "Janeiro 2025"})
    
    relevant_docs: List[str]
    generated_code: str
    execution_result: dict
    final_response: str
    error: Optional[str]
    messages: List[Any]
    
    # Campos para retry loop
    retry_count: int
    max_retries: int
    code_history: List[str]
    error_history: List[str]
    
    # Campos para RAG com Self-Reflection
    selected_files: List[str]
    validation_result: Optional[dict]
    rag_status: str  # "success" ou "fallback"
    fallback_response: Optional[str]
    tried_files: List[str]
    rejection_reasons: List[str]
    
    # Campos para Tools pré-programadas
    tool_route: bool  # True se tool foi executada
    tool_result: Optional[dict]  # Resultado da tool
    tool_used: Optional[str]  # Nome da tool usada
    
    # Campos para Disambiguation
    disambiguation: Optional[dict]
    
    # Campos para Comparação Multi-Deck
    comparison_data: Optional[dict]  # Dados de comparação multi-deck
    
    # Campos para escolha do usuário (requires_user_choice)
    requires_user_choice: Optional[bool]
    alternative_type: Optional[str]

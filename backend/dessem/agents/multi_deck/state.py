"""
Estado compartilhado entre os nodes do Multi-Deck Agent DESSEM.

Mantém a mesma forma do estado de multi-deck do NEWAVE, mas
sem lógica específica de comparação por enquanto.
"""

from typing import TypedDict, List, Optional, Any, Dict


class MultiDeckState(TypedDict):
    """Estado compartilhado entre os nodes do LangGraph para Multi-Deck DESSEM."""

    query: str
    deck_path: str

    # Decks selecionados e seus caminhos
    selected_decks: List[str]
    deck_paths: Dict[str, str]
    deck_display_names: Dict[str, str]

    final_response: str
    error: Optional[str]
    messages: List[Any]

    # Campos para Tools de comparação
    tool_route: bool
    tool_result: Optional[dict]
    tool_used: Optional[str]

    # Campos para Disambiguation
    disambiguation: Optional[dict]

    # Campos para dados de comparação agregados
    comparison_data: Optional[dict]

    # Campos para escolha do usuário (requires_user_choice)
    requires_user_choice: Optional[bool]
    alternative_type: Optional[str]


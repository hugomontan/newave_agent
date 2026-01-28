"""
Node de interpretação de comparações multi-deck para o DESSEM.

Enquanto não houver tools de comparação, apenas devolve uma
mensagem padrão informando que a funcionalidade ainda não
está disponível.
"""

from backend.dessem.agents.multi_deck.state import MultiDeckState
from backend.dessem.config import safe_print


def comparison_interpreter_node(state: MultiDeckState) -> dict:
    """
    Formata (futuramente) os resultados de comparação.

    Hoje devolve apenas uma mensagem estática avisando que
    o modo comparação do DESSEM ainda não foi implementado.
    """
    query = state.get("query", "")
    selected_decks = state.get("selected_decks", [])

    safe_print("[DESSEM MULTI-DECK INTERPRETER] Chamado para formatar comparação.")

    decks_str = ", ".join(selected_decks) if selected_decks else "nenhum deck selecionado"
    response = (
        "## Modo comparação DESSEM ainda não disponível\n\n"
        "A estrutura base para comparações multi-deck do DESSEM já está criada, "
        "mas as tools e formatadores específicos ainda não foram implementados.\n\n"
        f"- Consulta recebida: `{query}`\n"
        f"- Decks selecionados: `{decks_str}`\n"
    )

    return {
        "final_response": response,
        "comparison_data": None,
    }


"""
Node de interpretação de resultados para o Single Deck Agent DESSEM.

Reutiliza o interpreter genérico de `backend.core.nodes.interpreter`,
com um formatter genérico e uma mensagem padrão quando não há tools.
"""

from backend.dessem.state import SingleDeckState
from backend.dessem.agents.single_deck.formatters.registry import get_formatter_for_tool
from backend.dessem.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
from backend.dessem.tools import get_available_tools
from backend.core.nodes.interpreter import interpreter_node as shared_interpreter_node
from backend.core.utils.debug import write_debug_log


NO_TOOL_MESSAGE = """## Nenhuma tool DESSEM encontrada para esta consulta

Ainda não existem ferramentas DESSEM implementadas para responder a este tipo de pergunta.

Você pode reformular a consulta ou aguardar a implementação das tools específicas do modelo DESSEM."""


def interpreter_node(state: SingleDeckState) -> dict:
    """
    Node que formata os resultados e gera a resposta final em Markdown.

    No estágio atual, como não há tools DESSEM, ele sempre retorna a
    mensagem padrão acima, mas a estrutura já está pronta para receber
    formatters específicos quando as tools forem criadas.
    """
    return shared_interpreter_node(
        state=state,
        formatter_registry=None,
        no_tool_message=NO_TOOL_MESSAGE,
        get_available_tools_func=get_available_tools,
        get_formatter_for_tool_func=get_formatter_for_tool,
        get_generic_formatter_func=lambda: GenericSingleDeckFormatter(),
        debug_logger=write_debug_log,
    )


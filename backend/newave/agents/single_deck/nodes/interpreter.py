"""
Node que interpreta os resultados e gera a resposta final formatada em Markdown (single deck).
Usa o interpreter compartilhado em shared/agents/nodes/interpreter.py.
"""
from backend.newave.state import SingleDeckState
from backend.newave.agents.single_deck.formatters.registry import get_formatter_for_tool
from backend.newave.agents.single_deck.formatters.generic_formatter import GenericSingleDeckFormatter
from backend.newave.tools import get_available_tools
from backend.core.nodes.interpreter import interpreter_node as shared_interpreter_node
from backend.core.utils.debug import write_debug_log


# Mensagem padrão quando não há tool disponível
NO_TOOL_MESSAGE = """## Não foi encontrado sentido semântico entre o pedido e os dados disponíveis

Não foi possível identificar uma correspondência semântica entre sua consulta e os dados disponíveis no sistema.

Por favor, reformule sua pergunta ou consulte a documentação para ver os tipos de dados que podem ser consultados."""


def interpreter_node(state: SingleDeckState) -> dict:
    """
    Node que formata os resultados e gera a resposta final em Markdown.
    Delega para o interpreter compartilhado com as funções específicas do NEWAVE.
    """
    return shared_interpreter_node(
        state=state,
        formatter_registry=None,  # Não usado
        no_tool_message=NO_TOOL_MESSAGE,
        get_available_tools_func=get_available_tools,
        get_formatter_for_tool_func=get_formatter_for_tool,
        get_generic_formatter_func=lambda: GenericSingleDeckFormatter(),
        debug_logger=write_debug_log
    )


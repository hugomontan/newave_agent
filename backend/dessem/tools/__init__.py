"""
Ponto de entrada para tools DESSEM.

Mantém a mesma interface usada por NEWAVE/DECOMP. No momento não
há tools implementadas, então `get_available_tools` retorna uma
lista vazia, mas a classe base `DESSEMTool` já está disponível
para futuras implementações.
"""

from typing import List

from backend.core.base_tool import BaseTool


class DESSEMTool(BaseTool):
    """
    Classe base para todas as tools do DESSEM.

    Cada tool deverá herdar desta classe e implementar:
    - can_handle(): Verifica se pode processar a query
    - execute(): Executa a tool e retorna dados
    - get_description(): Descrição textual para o LLM
    """

    pass


def get_available_tools(deck_path: str) -> List[DESSEMTool]:  # noqa: ARG001
    """
    Retorna a lista de tools disponíveis para o deck DESSEM informado.

    Enquanto nenhuma tool estiver implementada, retorna sempre uma lista vazia.
    """
    return []


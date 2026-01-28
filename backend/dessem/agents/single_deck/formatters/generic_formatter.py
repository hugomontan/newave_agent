"""
Formatter genérico para respostas de single deck do DESSEM.

No momento é usado apenas como fallback quando existirem tools.
"""

from typing import Dict, Any

from .base import SingleDeckFormatter


class GenericSingleDeckFormatter(SingleDeckFormatter):
    """Formatter genérico simples: gera um resumo textual padrão."""

    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:  # noqa: ARG002
        # Pode formatar qualquer resultado (fallback)
        return True

    def get_priority(self) -> int:
        # Prioridade baixa, já que é fallback
        return -100

    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str,
        **_: Any,
    ) -> Dict[str, Any]:
        success = tool_result.get("success", False)
        data = tool_result.get("data") or []
        error = tool_result.get("error")

        if success:
            header = f"## Resultado da tool DESSEM: {tool_name}\n\n"
            body = f"- Registros retornados: **{len(data)}**\n"
        else:
            header = f"## Erro ao executar tool DESSEM: {tool_name}\n\n"
            body = f"- Erro: **{error or 'erro desconhecido'}**\n"

        response = header + body + "\n---\n\n" + f"Consulta original:\n> {query}"

        return {
            "final_response": response,
            "visualization_data": None,
        }


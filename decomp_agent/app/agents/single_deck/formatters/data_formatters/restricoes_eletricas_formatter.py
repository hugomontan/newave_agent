"""
Formatter para RestricoesEletricasDECOMPTool no single deck.
Entrega apenas a tabela via visualization_data, com mínimo texto.
"""

from typing import Dict, Any, List

from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class RestricoesEletricasSingleDeckFormatter(SingleDeckFormatter):
    """Formatter para RestricoesEletricasDECOMPTool."""

    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar RestricoesEletricasDECOMPTool."""
        return tool_name == "RestricoesEletricasDECOMPTool"

    def get_priority(self) -> int:
        """Prioridade semelhante a outros formatters de dados estruturados."""
        return 85

    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str,
    ) -> Dict[str, Any]:
        """Formata resposta de RestricoesEletricasDECOMPTool."""
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                # texto mínimo para o front renderizar algo
                "final_response": error,
                "visualization_data": None,
            }

        data: List[Dict[str, Any]] = tool_result.get("data", []) or []

        if not data:
            return {
                "final_response": "Nenhuma restrição encontrada para essa consulta.",
                "visualization_data": None,
            }

        # Helper para tratar valores numéricos (NaN/None -> 0)
        def _to_num(v):
            from math import isnan

            if v is None:
                return 0
            try:
                f = float(v)
                return 0 if isnan(f) else f
            except Exception:
                return v

        # Normalizar dados em uma tabela simples, com colunas renomeadas:
        # - Nome
        # - GMIN P1 / GMIN P2 / GMIN P3
        # - GMAX P1 / GMAX P2 / GMAX P3
        table_rows: List[Dict[str, Any]] = []

        for row in data:
            row_out: Dict[str, Any] = {}

            # Nome da restrição
            nome = ", ".join(row.get("nomes_possiveis", []) or [])
            if not nome and isinstance(row.get("nome"), str):
                nome = row.get("nome")  # fallback
            row_out["Nome"] = nome

            # GMIN por patamar
            row_out["GMIN P1"] = _to_num(row.get("limite_inferior_1"))
            row_out["GMIN P2"] = _to_num(row.get("limite_inferior_2"))
            row_out["GMIN P3"] = _to_num(row.get("limite_inferior_3"))

            # GMAX por patamar
            row_out["GMAX P1"] = _to_num(row.get("limite_superior_1"))
            row_out["GMAX P2"] = _to_num(row.get("limite_superior_2"))
            row_out["GMAX P3"] = _to_num(row.get("limite_superior_3"))

            table_rows.append(row_out)

        visualization_data = {
            "table": table_rows,
            "chart_data": None,
            "visualization_type": "table_only",
            "tool_name": tool_name,
            # dica para o front: pode expor botão de download CSV baseado nessa tabela
            "export": {
                "enabled": True,
                "format": "csv",
                "suggested_filename": "restricoes_eletricas.csv",
                "columns": [
                    "Nome",
                    "GMIN P1",
                    "GMIN P2",
                    "GMIN P3",
                    "GMAX P1",
                    "GMAX P2",
                    "GMAX P3",
                ],
            },
        }

        # Usar o primeiro registro bruto para montar o título:
        # "Restrições elétricas: {NOME_RESTRIÇÃO} {CÓDIGO}"
        first_raw = data[0]
        nome_titulo = ", ".join(first_raw.get("nomes_possiveis", []) or []) or "?"
        codigo = (
            first_raw.get("codigo_label_comentario")
            or first_raw.get("codigo_restricao")
            or "?"
        )
        titulo = f"Restrições elétricas: {nome_titulo} {codigo}"

        return {
            "final_response": titulo,
            "visualization_data": visualization_data,
        }


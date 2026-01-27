"""
Formatter para RestricoesEletricasDECOMPTool no single deck.
Entrega apenas a tabela via visualization_data, com mínimo texto.
"""

from typing import Dict, Any, List

import pandas as pd

from backend.decomp.agents.single_deck.formatters.base import SingleDeckFormatter


class RestricoesEletricasSingleDeckFormatter(SingleDeckFormatter):
    """Formatter para RestricoesEletricasDECOMPTool."""

    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar RestricoesEletricasDECOMPTool ou tools de vazão HQ."""
        return tool_name in (
            "RestricoesEletricasDECOMPTool",
            "RestricoesVazaoHQTool",
            "RestricoesVazaoHQConjuntaTool",
        )

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

        # Filtrar apenas registros do estágio 1
        data_filtrada = []
        for row in data:
            # Tentar diferentes nomes possíveis para o campo de estágio
            estagio = None
            for campo in ["estagio", "estágio", "estagio_inicial", "ip", "stage"]:
                if campo in row and row[campo] is not None:
                    try:
                        estagio = int(row[campo])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Se não encontrou campo de estágio ou estágio é 1, incluir o registro
            if estagio is None or estagio == 1:
                data_filtrada.append(row)

        data = data_filtrada

        if not data:
            return {
                "final_response": "Nenhuma restrição encontrada para essa consulta.",
                "visualization_data": None,
            }

        # Helper para tratar valores numéricos
        # allow_none=True: None = sem restrição; 0 = restrição zero (vazão e elétricas)
        def _to_num(v, allow_none=False):
            from math import isnan

            if v is None:
                return None if allow_none else 0
            
            # Tratar pandas NaN
            try:
                if pd.isna(v):
                    return None if allow_none else 0
            except (TypeError, ValueError):
                pass
            
            try:
                f = float(v)
                if isnan(f):
                    return None if allow_none else 0
                return f
            except (ValueError, TypeError):
                return None if allow_none else v

        # Usar sempre 3 patamares (P1, P2, P3)
        max_patamares = 3

        # Normalizar dados em uma tabela simples, com colunas renomeadas:
        # - Nome
        # - GMIN P1 / GMIN P2 / GMIN P3
        # - GMAX P1 / GMAX P2 / GMAX P3
        table_rows: List[Dict[str, Any]] = []
        is_vazao = tool_name in (
            "RestricoesVazaoHQTool",
            "RestricoesVazaoHQConjuntaTool",
        )
        is_eletricas = tool_name == "RestricoesEletricasDECOMPTool"
        # None = sem restrição; 0 = restrição zero (vazão e elétricas)
        allow_none_valores = is_vazao or is_eletricas
        is_vazao_conjunta = tool_name == "RestricoesVazaoHQConjuntaTool"

        for row in data:
            row_out: Dict[str, Any] = {}

            # Nome da restrição (adaptar para HQ se necessário)
            if is_vazao:
                if is_vazao_conjunta:
                    # Para restrições conjuntas, usar "usinas_envolvidas" como nome
                    usinas_env_nome = row.get("usinas_envolvidas")
                    if usinas_env_nome:
                        # Extrair apenas os nomes (antes dos parênteses) e juntar com " + "
                        nomes = []
                        for parte in usinas_env_nome.split(","):
                            parte_limpa = parte.strip()
                            if "(" in parte_limpa:
                                nome_so = parte_limpa.split("(")[0].strip()
                                if nome_so:
                                    nomes.append(nome_so)
                            else:
                                if parte_limpa:
                                    nomes.append(parte_limpa)
                        nome = " + ".join(nomes) if nomes else usinas_env_nome
                    else:
                        # Fallback
                        nome = row.get("nome_usina") or f"UHE {row.get('codigo_usina', '?')}"
                else:
                    # Para restrições unitárias, usar nome da usina
                    nome = row.get("nome_usina") or f"UHE {row.get('codigo_usina', '?')}"
            else:
                nome = ", ".join(row.get("nomes_possiveis", []) or [])
                if not nome and isinstance(row.get("nome"), str):
                    nome = row.get("nome")  # fallback
            row_out["Nome"] = nome

            # GMIN e GMAX por patamar (até max_patamares)
            # allow_none: None = sem restrição; 0 = restrição zero
            for i in range(1, max_patamares + 1):
                gmin_key = f"GMIN P{i}"
                gmax_key = f"GMAX P{i}"
                row_out[gmin_key] = _to_num(row.get(f"limite_inferior_{i}"), allow_none=allow_none_valores)
                row_out[gmax_key] = _to_num(row.get(f"limite_superior_{i}"), allow_none=allow_none_valores)

            table_rows.append(row_out)

        # Construir lista de colunas dinamicamente baseado no número de patamares
        columns = ["Nome"]
        for i in range(1, max_patamares + 1):
            columns.append(f"GMIN P{i}")
        for i in range(1, max_patamares + 1):
            columns.append(f"GMAX P{i}")
        
        visualization_data = {
            "table": table_rows,
            "chart_data": None,
            "visualization_type": "table_only",
            "tool_name": tool_name,
            # dica para o front: pode expor botão de download CSV baseado nessa tabela
            "export": {
                "enabled": True,
                "format": "csv",
                "suggested_filename": "restricoes_vazao.csv" if is_vazao else "restricoes_eletricas.csv",
                "columns": columns,
            },
        }

        # Usar o primeiro registro bruto para montar o título:
        # "Restrições elétricas: {NOME_RESTRIÇÃO} {CÓDIGO}" ou "Restrições de vazão: {USINA}"
        first_raw = data[0]
        
        # Adaptar título baseado no tipo de tool
        if tool_name == "RestricoesVazaoHQConjuntaTool":
            # Para restrições conjuntas, usar todas as usinas envolvidas
            usinas_env_titulo = first_raw.get("usinas_envolvidas") or ""
            if usinas_env_titulo:
                # Extrair apenas os nomes (antes dos parênteses) e juntar com " + "
                nomes_titulo = []
                for parte in usinas_env_titulo.split(","):
                    parte_limpa = parte.strip()
                    if "(" in parte_limpa:
                        nome_so = parte_limpa.split("(")[0].strip()
                        if nome_so:
                            nomes_titulo.append(nome_so.upper())
                    else:
                        if parte_limpa:
                            nomes_titulo.append(parte_limpa.upper())
                nomes_str = " + ".join(nomes_titulo) if nomes_titulo else usinas_env_titulo.upper()
                titulo = f"## RESTRIÇÃO DE VAZÃO CONJUNTA: {nomes_str}"
            else:
                # Fallback
                nome_usina = first_raw.get("nome_usina") or "?"
                codigo_usina = first_raw.get("codigo_usina") or "?"
                titulo = f"## RESTRIÇÃO DE VAZÃO CONJUNTA: UHE {nome_usina.upper()} {codigo_usina}"
        elif tool_name == "RestricoesVazaoHQTool":
            # Para restrições unitárias, usar nome e código da usina
            nome_usina = first_raw.get("nome_usina") or "?"
            codigo_usina = first_raw.get("codigo_usina") or "?"
            # Formatar título como heading markdown (##) em caixa alta para destaque visual
            titulo = f"## UHE {nome_usina.upper()} {codigo_usina}"
        else:
            # Restrições elétricas (RE)
            nome_titulo = ", ".join(first_raw.get("nomes_possiveis", []) or []) or "?"
            codigo = (
                first_raw.get("codigo_label_comentario")
                or first_raw.get("codigo_restricao")
                or "?"
            )
            # Formatar título como heading markdown (##) em caixa alta para destaque visual
            titulo = f"## RESTRIÇÕES ELÉTRICAS: {nome_titulo.upper()} {codigo}"

        return {
            "final_response": titulo,
            "visualization_data": visualization_data,
        }


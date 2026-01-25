"""
Tool específica para consultar **restrições de vazão conjuntas** (HQ/LQ/CQ)
envolvendo múltiplas usinas simultaneamente.

Reutiliza toda a infraestrutura da RestricoesVazaoHQTool, mas força a lógica
de interseção de HQ entre usinas e filtra apenas restrições multi-usina
(mais de uma usina no bloco CQ).
"""

from typing import Any, Dict, List

from backend.decomp.config import safe_print
from backend.decomp.tools.restricoes_vazao_hq_tool import RestricoesVazaoHQTool


class RestricoesVazaoHQConjuntaTool(RestricoesVazaoHQTool):
    """
    Consulta restrições de vazão conjuntas (multi-usina) do DECOMP associadas
    a duas ou mais usinas hidrelétricas.
    """

    def get_name(self) -> str:
        return "RestricoesVazaoHQConjuntaTool"

    def can_handle(self, query: str) -> bool:
        """
        Ativa apenas para queries explicitamente sobre restrição de vazão
        **conjunta** / somatório de defluências.
        """
        q = query.lower()

        # Palavras-chave que indicam intenção de restrição conjunta
        termos_conjunta = [
            "restricao de vazao conjunta",
            "restrição de vazão conjunta",
            "restricao conjunta de vazao",
            "restrição conjunta de vazão",
            "somatorio das defluencias",
            "somatório das defluências",
            "somatorio de vazao",
            "somatório de vazão",
        ]

        if not any(t in q for t in termos_conjunta):
            return False

        # Ainda assim, garantir que é uma query de vazão/HQ
        if "vazao" not in q and "vazão" not in q and "hq" not in q:
            return False

        return True

    def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        safe_print(f"[HQ-CONJ] Query: {query}")
        safe_print(f"[HQ-CONJ] Deck: {self.deck_path}")

        try:
            dadger = self._get_dadger()
            if dadger is None:
                return self._error(
                    "Arquivo dadger não encontrado (nenhum dadger.rv* / dadger.rvx)."
                )

            # Usina principal apenas para fallback/título
            codigo_usina, nome_usina = self._resolver_codigo_usina(query, dadger)
            if codigo_usina is None:
                return {
                    "success": False,
                    "error": "Não consegui identificar as UHEs na pergunta.",
                    "tool": self.get_name(),
                }

            # Todas as usinas mencionadas na query
            usinas_mencionadas = self._listar_usinas_na_query(query, dadger)
            if not usinas_mencionadas:
                usinas_mencionadas = [(codigo_usina, nome_usina)]
            else:
                codigos_mencionados = {c for c, _ in usinas_mencionadas}
                if codigo_usina not in codigos_mencionados:
                    usinas_mencionadas.insert(0, (codigo_usina, nome_usina))

            safe_print(
                f"[HQ-CONJ] Usinas mencionadas na query: "
                f"{[(c, n) for c, n in usinas_mencionadas]}"
            )

            # Se só existir uma usina mencionada, ainda assim queremos apenas
            # HQ multi-usina ligadas a ela.
            if len(usinas_mencionadas) == 1:
                cod_ref, nome_ref = usinas_mencionadas[0]
                restricoes_ref = self._buscar_restricoes_vazao_por_usina(
                    cod_ref,
                    nome_ref,
                    dadger,
                    somente_usina_exata=False,
                )
                # Filtrar apenas HQ multi-usina
                restricoes = [
                    r for r in restricoes_ref if r.get("multi_usina") is True
                ]
                codigo_usina, nome_usina = cod_ref, nome_ref
            else:
                # Modo multi-usina clássico: interseção de HQ entre TODAS as usinas
                cod_ref, nome_ref = usinas_mencionadas[0]
                safe_print(
                    f"[HQ-CONJ] Modo multi-usina. Usina de referência: "
                    f"{cod_ref} '{nome_ref}'"
                )

                restricoes_ref = self._buscar_restricoes_vazao_por_usina(
                    cod_ref,
                    nome_ref,
                    dadger,
                    somente_usina_exata=False,
                )

                if not restricoes_ref:
                    restricoes = []
                else:
                    codigos_comuns = {
                        r.get("codigo_restricao")
                        for r in restricoes_ref
                        if r.get("codigo_restricao") is not None
                    }

                    for cod_u, nome_u in usinas_mencionadas[1:]:
                        restricoes_u = self._buscar_restricoes_vazao_por_usina(
                            cod_u,
                            nome_u,
                            dadger,
                            somente_usina_exata=False,
                        )
                        codigos_u = {
                            r.get("codigo_restricao")
                            for r in restricoes_u
                            if r.get("codigo_restricao") is not None
                        }
                        safe_print(
                            f"[HQ-CONJ] Códigos HQ da usina {cod_u} ('{nome_u}'): "
                            f"{sorted(codigos_u)}"
                        )
                        codigos_comuns &= codigos_u

                    safe_print(
                        f"[HQ-CONJ] Códigos HQ em comum entre as usinas: "
                        f"{sorted(codigos_comuns)}"
                    )

                    if not codigos_comuns:
                        restricoes = []
                    else:
                        restricoes = [
                            r
                            for r in restricoes_ref
                            if r.get("codigo_restricao") in codigos_comuns
                            and r.get("multi_usina") is True
                        ]

                codigo_usina, nome_usina = cod_ref, nome_ref

            if not restricoes:
                nomes = " e ".join(n for _, n in usinas_mencionadas)
                return {
                    "success": False,
                    "error": (
                        f"As usinas {nomes} não possuem nenhuma restrição de vazão "
                        "HQ/LQ conjunta (multi-usina) neste deck."
                    ),
                    "tool": self.get_name(),
                }

            # Durações de patamar (mesmo cálculo da tool base)
            duracoes = self._extrair_duracoes_patamares(dadger)
            if duracoes and all(v is not None for v in duracoes.values()):
                safe_print(f"[HQ-CONJ] Durações de patamar encontradas: {duracoes}")
                for r in restricoes:
                    self._calcular_vazao_media_ponderada_inplace(r, duracoes)

            codigos_encontrados = sorted(
                {
                    r.get("codigo_restricao")
                    for r in restricoes
                    if r.get("codigo_restricao")
                }
            )

            return {
                "success": True,
                "usina": {
                    "codigo_usina": codigo_usina,
                    "nome_usina": nome_usina,
                },
                "codigos_encontrados": codigos_encontrados,
                "total_registros": len(restricoes),
                "duracoes": duracoes,
                "data": restricoes,
                "tool": self.get_name(),
            }

        except Exception as e:  # pragma: no cover
            safe_print(f"[HQ-CONJ] Erro: {e}")
            import traceback

            traceback.print_exc()
            return self._error(str(e))


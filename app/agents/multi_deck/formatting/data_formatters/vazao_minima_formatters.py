"""
Formatador para MudancasVazaoMinimaTool.
Visualização: Tabela de mudanças ordenadas por magnitude.
"""
from typing import Dict, Any
from app.agents.multi_deck.formatting.base import ComparisonFormatter
from app.agents.multi_deck.formatting.data_formatters.gtmin_formatters import (
    format_date_br,
    format_periodo_coluna
)


class MudancasVazaoMinimaFormatter(ComparisonFormatter):
    """
    Formatador para MudancasVazaoMinimaTool.
    Visualização: Tabela de mudanças ordenadas por magnitude, destacando variações de VAZMIN/VAZMINT.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "MudancasVazaoMinimaTool" and (
            "comparison_table" in result_structure or
            "is_comparison" in result_structure
        )
    
    def get_priority(self) -> int:
        return 95  # Alta prioridade - muito específico
    
    def _format_periodo_mm_yyyy(self, periodo_inicio: str) -> str:
        """
        Formata período de YYYY-MM para MM-YYYY.
        
        Args:
            periodo_inicio: Data no formato "YYYY-MM" ou "N/A"
            
        Returns:
            Período formatado como "MM-YYYY" (ex: "12-2025") ou string vazia se inválido
        """
        if not periodo_inicio or periodo_inicio == "N/A":
            return ""
        
        try:
            if "-" in periodo_inicio:
                parts = periodo_inicio.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = parts[1]
                    return f"{mes}-{ano}"
            return ""
        except:
            return ""
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de mudanças de vazão mínima.
        Similar ao formatador de GTMIN.
        """
        result_to_use = result_dec if result_dec.get("is_comparison") else result_jan
        
        if result_to_use.get("is_comparison") and "comparison_table" in result_to_use:
            raw_table = result_to_use.get("comparison_table", [])
            stats = result_to_use.get("stats", {})
            
            # Agrupar por tipo_vazao E tipo_mudanca (chave composta)
            # Estrutura: {tipo_vazao: {tipo_mudanca: [rows]}}
            mudancas_por_tipo_vazao = {
                "VAZMIN": {
                    "aumento": [],
                    "queda": [],
                    "remocao": [],
                    "novo": [],
                    "sem_mudanca": []
                },
                "VAZMINT": {
                    "aumento": [],
                    "queda": [],
                    "remocao": [],
                    "novo": [],
                    "sem_mudanca": []
                }
            }
            
            for row in raw_table:
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                tipo_vazao = row.get("tipo_vazao", "VAZMIN")
                
                # Garantir que tipo_vazao seja VAZMIN ou VAZMINT
                if tipo_vazao not in ["VAZMIN", "VAZMINT"]:
                    tipo_vazao = "VAZMIN"  # Fallback
                
                if tipo_mudanca in mudancas_por_tipo_vazao[tipo_vazao]:
                    mudancas_por_tipo_vazao[tipo_vazao][tipo_mudanca].append(row)
            
            # Converter para formato do frontend
            comparison_table = []
            comparison_by_type = {}
            
            tipo_labels = {
                "aumento": "Aumentos",
                "queda": "Reduções",
                "remocao": "Exclusões",
                "novo": "Inclusões",
                "sem_mudanca": "Sem Mudança"
            }
            
            tipo_vazao_labels = {
                "VAZMIN": "VAZMIN",
                "VAZMINT": "VAZMINT"
            }
            
            # Processar cada combinação de tipo_vazao e tipo_mudanca
            for tipo_vazao in ["VAZMIN", "VAZMINT"]:
                for tipo_mudanca, mudancas_tipo in mudancas_por_tipo_vazao[tipo_vazao].items():
                    if not mudancas_tipo:
                        continue
                    
                    tipo_table = []
                    for row in mudancas_tipo:
                        nome_usina = row.get("nome_usina", "N/A")
                        periodo_inicio = row.get("periodo_inicio", "N/A")
                        tipo_vazao_row = row.get("tipo_vazao", "VAZMIN")
                        
                        # Formatar período
                        # Para VAZMINT, período é OBRIGATÓRIO e deve ser sempre exibido
                        if tipo_vazao_row == "VAZMINT":
                            periodo_inicio_formatado = format_date_br(periodo_inicio)
                            # Se ainda for "N/A", usar o período original como fallback
                            if periodo_inicio_formatado == "N/A" and periodo_inicio != "N/A":
                                periodo_str = str(periodo_inicio)
                            else:
                                periodo_str = periodo_inicio_formatado if periodo_inicio_formatado != "N/A" else str(periodo_inicio)
                        else:
                            # Para VAZMIN, não há período
                            periodo_inicio_formatado = ""
                            periodo_str = ""
                        
                        # Formatar período para coluna no formato MM-YYYY
                        # Para VAZMINT, SEMPRE deve ter período_coluna no formato MM-YYYY
                        if tipo_vazao_row == "VAZMINT":
                            # Converter período de YYYY-MM para MM-YYYY
                            periodo_mm_yyyy = self._format_periodo_mm_yyyy(periodo_inicio)
                            periodo_coluna = periodo_mm_yyyy if periodo_mm_yyyy else ""
                        else:
                            periodo_coluna = ""  # VAZMIN não tem período
                        
                        vazao_dez = row.get("vazao_dezembro")
                        vazao_jan = row.get("vazao_janeiro")
                        diferenca = row.get("diferenca")
                        
                        # Para inclusões/exclusões, não calcular diferença percentual
                        is_inclusao_ou_exclusao = tipo_mudanca in ["novo", "remocao"]
                        
                        difference_percent = 0.0
                        if not is_inclusao_ou_exclusao:
                            if vazao_dez is not None and vazao_dez != 0:
                                if diferenca is not None:
                                    difference_percent = (diferenca / abs(vazao_dez)) * 100
                            elif vazao_jan is not None and vazao_jan != 0:
                                if diferenca is not None:
                                    difference_percent = (diferenca / abs(vazao_jan)) * 100
                        
                        row_formatted = {
                            "field": nome_usina,
                            "classe": tipo_vazao_row,  # Usar tipo_vazao como classe
                            "data": periodo_str,
                            "periodo_coluna": periodo_coluna,
                            "period": nome_usina,
                            "periodo_inicio": periodo_inicio,
                            "tipo_vazao": tipo_vazao_row,  # "VAZMIN" ou "VAZMINT"
                            "tipo_mudanca": tipo_mudanca,
                            # Chave composta: tipo_vazao-tipo_mudanca (ex: "VAZMIN-aumento", "VAZMINT-queda")
                            "tipo_mudanca_key": f"{tipo_vazao}-{tipo_mudanca}",
                            # Label composto: "Aumentos de VAZMIN" ou "Aumentos de VAZMINT"
                            "tipo_mudanca_label": f"{tipo_labels.get(tipo_mudanca, tipo_mudanca)} de {tipo_vazao_labels.get(tipo_vazao, tipo_vazao)}",
                            "is_inclusao_ou_exclusao": is_inclusao_ou_exclusao,
                            "deck_1": vazao_dez if vazao_dez is not None else 0,
                            "deck_1_value": vazao_dez if vazao_dez is not None else 0,
                            "deck_2": vazao_jan if vazao_jan is not None else 0,
                            "deck_2_value": vazao_jan if vazao_jan is not None else 0,
                            "diferenca": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "difference": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "diferenca_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                            "difference_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                            "magnitude": row.get("magnitude", 0),
                            "nome_usina": nome_usina,
                            "vazao_dezembro": vazao_dez,
                            "vazao_janeiro": vazao_jan,
                        }
                        
                        tipo_table.append(row_formatted)
                        comparison_table.append(row_formatted)
                
                    # Ordenar por magnitude
                    tipo_table.sort(key=lambda x: -abs(x.get("magnitude", 0)))
                    
                    # Criar chave composta para o agrupamento
                    chave_composta = f"{tipo_vazao}-{tipo_mudanca}"
                    comparison_by_type[chave_composta] = {
                        "tipo": tipo_mudanca,
                        "tipo_vazao": tipo_vazao,
                        "label": f"{tipo_labels.get(tipo_mudanca, tipo_mudanca)} de {tipo_vazao_labels.get(tipo_vazao, tipo_vazao)}",
                        "rows": tipo_table
                    }
            
            # Ordenar tabela geral
            # Ordem: primeiro por tipo_vazao (VAZMIN antes de VAZMINT), depois por tipo_mudanca, depois por magnitude
            ordem_tipo_vazao = {"VAZMIN": 0, "VAZMINT": 1}
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            comparison_table.sort(key=lambda x: (
                ordem_tipo_vazao.get(x.get("tipo_vazao", "VAZMIN"), 99),
                ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
                -abs(x.get("magnitude", 0))
            ))
            
            # Adicionar estatísticas por tipo (agregadas)
            stats_por_tipo = {
                "aumento": sum(len(mudancas_por_tipo_vazao[tv]["aumento"]) for tv in ["VAZMIN", "VAZMINT"]),
                "queda": sum(len(mudancas_por_tipo_vazao[tv]["queda"]) for tv in ["VAZMIN", "VAZMINT"]),
                "remocao": sum(len(mudancas_por_tipo_vazao[tv]["remocao"]) for tv in ["VAZMIN", "VAZMINT"]),
                "novo": sum(len(mudancas_por_tipo_vazao[tv]["novo"]) for tv in ["VAZMIN", "VAZMINT"])
            }
            stats["mudancas_por_tipo"] = stats_por_tipo
            
            # Adicionar estatísticas por tipo_vazao
            stats_por_tipo_vazao = {
                "VAZMIN": sum(len(mudancas_por_tipo_vazao["VAZMIN"][tm]) for tm in ["aumento", "queda", "remocao", "novo"]),
                "VAZMINT": sum(len(mudancas_por_tipo_vazao["VAZMINT"][tm]) for tm in ["aumento", "queda", "remocao", "novo"])
            }
            stats["mudancas_por_tipo_vazao"] = stats_por_tipo_vazao
            
            return {
                "comparison_table": comparison_table,
                "comparison_by_type": comparison_by_type,
                "chart_data": None,
                "visualization_type": "vazao_minima_changes_table",
                "stats": stats,
                "llm_context": {
                    "total_mudancas": len(comparison_table),
                    "deck_1_name": "Dezembro 2025",
                    "deck_2_name": "Janeiro 2026",
                    "description": result_to_use.get("description", f"Análise de {len(comparison_table)} mudanças de vazão mínima entre Dezembro 2025 e Janeiro 2026, ordenadas por magnitude."),
                    "tipos_vazao": {
                        "VAZMIN": stats_por_tipo_vazao.get("VAZMIN", 0),
                        "VAZMINT": stats_por_tipo_vazao.get("VAZMINT", 0)
                    },
                    "note": "Os resultados incluem mudanças de ambos os tipos: VAZMIN (vazão mínima sem período) e VAZMINT (vazão mínima com período). Os dados estão claramente separados por seções no frontend."
                }
            }
        
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "vazao_minima_changes_table",
            "llm_context": {
                "note": "Dados não formatados corretamente."
            }
        }
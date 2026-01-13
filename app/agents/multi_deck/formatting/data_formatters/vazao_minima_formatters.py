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
            
            # Agrupar por tipo de mudança
            mudancas_por_tipo = {
                "aumento": [],
                "queda": [],
                "remocao": [],
                "novo": []
            }
            
            for row in raw_table:
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                if tipo_mudanca in mudancas_por_tipo:
                    mudancas_por_tipo[tipo_mudanca].append(row)
            
            # Converter para formato do frontend
            comparison_table = []
            comparison_by_type = {}
            
            tipo_labels = {
                "aumento": "Aumentos de Vazão Mínima",
                "queda": "Reduções de Vazão Mínima",
                "remocao": "Exclusões de Vazão Mínima",
                "novo": "Inclusões de Vazão Mínima"
            }
            
            for tipo_mudanca, mudancas_tipo in mudancas_por_tipo.items():
                if not mudancas_tipo:
                    continue
                
                tipo_table = []
                for row in mudancas_tipo:
                    nome_usina = row.get("nome_usina", "N/A")
                    periodo_inicio = row.get("periodo_inicio", "N/A")
                    tipo_vazao = row.get("tipo_vazao", "VAZMIN")
                    
                    # Formatar período
                    periodo_inicio_formatado = format_date_br(periodo_inicio)
                    periodo_str = periodo_inicio_formatado if periodo_inicio_formatado != "N/A" else ""
                    
                    # Formatar período para coluna
                    periodo_coluna = format_periodo_coluna(periodo_inicio, None)
                    
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
                        "classe": "VAZMIN",
                        "data": periodo_str,
                        "periodo_coluna": periodo_coluna,
                        "period": nome_usina,
                        "periodo_inicio": periodo_inicio,
                        "tipo_vazao": tipo_vazao,  # "VAZMIN" ou "VAZMINT"
                        "tipo_mudanca": tipo_mudanca,
                        "tipo_mudanca_key": tipo_mudanca,
                        "tipo_mudanca_label": tipo_labels.get(tipo_mudanca, tipo_mudanca),
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
                
                comparison_by_type[tipo_mudanca] = {
                    "tipo": tipo_mudanca,
                    "label": tipo_labels.get(tipo_mudanca, tipo_mudanca),
                    "rows": tipo_table
                }
            
            # Ordenar tabela geral
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            comparison_table.sort(key=lambda x: (
                ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
                -abs(x.get("magnitude", 0))
            ))
            
            # Adicionar estatísticas por tipo
            stats_por_tipo = {
                "aumento": len(mudancas_por_tipo["aumento"]),
                "queda": len(mudancas_por_tipo["queda"]),
                "remocao": len(mudancas_por_tipo["remocao"]),
                "novo": len(mudancas_por_tipo["novo"])
            }
            stats["mudancas_por_tipo"] = stats_por_tipo
            
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
                    "description": result_to_use.get("description", f"Análise de {len(comparison_table)} mudanças de vazão mínima entre Dezembro 2025 e Janeiro 2026, ordenadas por magnitude.")
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
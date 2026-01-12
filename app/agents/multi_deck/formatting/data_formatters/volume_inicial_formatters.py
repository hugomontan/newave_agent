"""
Formatador para VariacaoVolumesIniciaisTool.
Visualização: Tabela de mudanças ordenadas por magnitude, agrupada por REE em seções separadas.
"""
from typing import Dict, Any
from app.agents.multi_deck.formatting.base import ComparisonFormatter


class VariacaoVolumesIniciaisFormatter(ComparisonFormatter):
    """
    Formatador para VariacaoVolumesIniciaisTool.
    Visualização: Tabela de mudanças ordenadas por magnitude, agrupada por REE em seções separadas.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "VariacaoVolumesIniciaisTool" and (
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
        Formata comparação de mudanças de volumes iniciais.
        A tool já retorna dados formatados, então apenas organizamos para visualização.
        Agrupa por REE em seções separadas.
        """
        # A VariacaoVolumesIniciaisTool já retorna dados comparativos diretamente
        # Como a tool é executada duas vezes (uma para cada deck), ambos os resultados
        # contêm os mesmos dados completos da comparação
        # Usamos result_dec (ou result_jan, ambos são iguais)
        result_to_use = result_dec if result_dec.get("is_comparison") else result_jan
        
        if result_to_use.get("is_comparison") and "comparison_table" in result_to_use:
            raw_table = result_to_use.get("comparison_table", [])
            stats = result_to_use.get("stats", {})
            
            # Agrupar por REE primeiro, depois por tipo de mudança
            mudancas_por_ree = {}
            
            for row in raw_table:
                ree = row.get("ree")
                if ree is None:
                    ree = "Sem REE"
                else:
                    ree = int(ree)
                
                if ree not in mudancas_por_ree:
                    mudancas_por_ree[ree] = {
                        "aumento": [],
                        "reducao": [],
                        "remocao": [],
                        "novo": []
                    }
                
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                # Mapear tipos se necessário
                tipo_mapeado = {
                    "alterado": "aumento",
                    "novo_registro": "novo",
                    "removido": "remocao",
                    "novo_valor": "novo",
                    "valor_removido": "remocao",
                    "queda": "reducao"
                }.get(tipo_mudanca, tipo_mudanca)
                
                if tipo_mapeado in mudancas_por_ree[ree]:
                    mudancas_por_ree[ree][tipo_mapeado].append(row)
                elif tipo_mudanca in mudancas_por_ree[ree]:
                    mudancas_por_ree[ree][tipo_mudanca].append(row)
            
            # Converter cada mudança para formato do frontend
            comparison_table = []
            comparison_by_ree = {}
            
            # Labels para tipos de mudança
            tipo_labels = {
                "aumento": "Aumentos",
                "reducao": "Reduções",
                "remocao": "Exclusões",
                "novo": "Inclusões"
            }
            
            # Processar cada REE
            for ree in sorted(mudancas_por_ree.keys(), key=lambda x: (x == "Sem REE", x if isinstance(x, int) else 0)):
                ree_mudancas = mudancas_por_ree[ree]
                ree_table = []
                
                # Processar cada tipo de mudança dentro do REE
                for tipo_mudanca in ["aumento", "reducao", "remocao", "novo"]:
                    mudancas_tipo = ree_mudancas.get(tipo_mudanca, [])
                    
                    for row in mudancas_tipo:
                        nome_usina = row.get("nome_usina", "N/A")
                        codigo_usina = row.get("codigo_usina")
                        
                        volume_dez = row.get("volume_dezembro")
                        volume_jan = row.get("volume_janeiro")
                        diferenca = row.get("diferenca")
                        diferenca_percentual = row.get("diferenca_percentual")
                        
                        # Para inclusões (novo) e exclusões (remocao), não calcular diferença/variacao
                        is_inclusao_ou_exclusao = tipo_mudanca in ["novo", "remocao"]
                        
                        # Usar nome da usina como field principal
                        if nome_usina and nome_usina != "N/A" and not nome_usina.startswith("Usina "):
                            period_display = nome_usina
                        else:
                            period_display = nome_usina if nome_usina else f"Usina {codigo_usina}"
                        
                        # Formatar volumes com "%"
                        def format_volume_percent(value):
                            """Formata valor numérico como percentual com vírgula."""
                            if value is None:
                                return None
                            try:
                                # Usar vírgula como separador decimal (formato brasileiro)
                                return f"{value:.2f}".replace(".", ",") + "%"
                            except (ValueError, TypeError):
                                return None
                        
                        volume_dez_formatted = format_volume_percent(volume_dez)
                        volume_jan_formatted = format_volume_percent(volume_jan)
                        
                        # Converter para formato esperado pelo frontend
                        row_formatted = {
                            "field": nome_usina,  # Nome da usina como field principal
                            "classe": "VOLUME_INICIAL",  # Classe para identificar como volume inicial
                            "period": period_display,  # Nome da usina para exibição na primeira coluna
                            "ree": ree,  # REE para agrupamento e exibição
                            "ree_display": f"REE {ree}" if isinstance(ree, int) else str(ree),  # REE formatado para exibição
                            "ree_key": f"REE_{ree}",  # Chave para agrupamento por REE
                            "tipo_mudanca": tipo_mudanca,  # Tipo interno (aumento, reducao, remocao, novo)
                            "tipo_mudanca_key": tipo_mudanca,  # Chave para agrupamento por tipo
                            "tipo_mudanca_label": tipo_labels.get(tipo_mudanca, tipo_mudanca),  # Label para exibição
                            "is_inclusao_ou_exclusao": is_inclusao_ou_exclusao,  # Flag para ocultar diferença/variação
                            "deck_1": volume_dez if volume_dez is not None else 0,
                            "deck_1_value": volume_dez if volume_dez is not None else 0,
                            "deck_1_display": volume_dez_formatted,  # Volume dezembro formatado com %
                            "deck_2": volume_jan if volume_jan is not None else 0,
                            "deck_2_value": volume_jan if volume_jan is not None else 0,
                            "deck_2_display": volume_jan_formatted,  # Volume janeiro formatado com %
                            "diferenca": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "difference": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "diferenca_percent": round(diferenca_percentual, 2) if (diferenca_percentual is not None and not is_inclusao_ou_exclusao) else None,
                            "difference_percent": round(diferenca_percentual, 2) if (diferenca_percentual is not None and not is_inclusao_ou_exclusao) else None,
                            "magnitude": row.get("magnitude_mudanca", 0),
                            # Manter campos originais para referência
                            "nome_usina": nome_usina,
                            "codigo_usina": codigo_usina,
                            "volume_dezembro": volume_dez,
                            "volume_janeiro": volume_jan,
                        }
                        
                        ree_table.append(row_formatted)
                        comparison_table.append(row_formatted)  # Também adicionar à tabela geral
                    
                    # Ordenar por magnitude dentro do tipo (maior primeiro)
                    mudancas_tipo_sorted = sorted(
                        [r for r in ree_table if r.get("tipo_mudanca") == tipo_mudanca],
                        key=lambda x: -abs(x.get("magnitude", 0))
                    )
                
                # Ordenar tabela do REE por magnitude (maior variação primeiro)
                ree_table.sort(key=lambda x: -abs(x.get("magnitude", 0)))
                
                # Adicionar ao agrupamento por REE
                comparison_by_ree[ree] = {
                    "ree": ree,
                    "ree_label": f"REE {ree}" if isinstance(ree, int) else str(ree),
                    "rows": ree_table,
                    "tipos_mudanca": {
                        "aumento": len(ree_mudancas["aumento"]),
                        "reducao": len(ree_mudancas["reducao"]),
                        "remocao": len(ree_mudancas["remocao"]),
                        "novo": len(ree_mudancas["novo"])
                    }
                }
            
            # Ordenar tabela geral por magnitude (maior variação primeiro)
            # Não considerar REE ou tipo - apenas magnitude
            comparison_table.sort(key=lambda x: -abs(x.get("magnitude", 0)))
            
            # Adicionar estatísticas por tipo
            stats_por_tipo = {
                "aumento": sum(len(ree_data["aumento"]) for ree_data in mudancas_por_ree.values()),
                "reducao": sum(len(ree_data["reducao"]) for ree_data in mudancas_por_ree.values()),
                "remocao": sum(len(ree_data["remocao"]) for ree_data in mudancas_por_ree.values()),
                "novo": sum(len(ree_data["novo"]) for ree_data in mudancas_por_ree.values())
            }
            stats["mudancas_por_tipo"] = stats_por_tipo
            
            return {
                "comparison_table": comparison_table,
                "comparison_by_ree": comparison_by_ree,  # Agrupamento por REE para renderização em seções
                "chart_data": None,  # Sem gráfico
                "visualization_type": "volume_inicial_changes_table",
                "stats": stats,
                "llm_context": {
                    "total_mudancas": len(comparison_table),
                    "deck_1_name": "Dezembro 2025",
                    "deck_2_name": "Janeiro 2026"
                }
            }
        
        # Fallback: se recebemos dois resultados separados (não deve acontecer)
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "volume_inicial_changes_table",
            "llm_context": {}
        }

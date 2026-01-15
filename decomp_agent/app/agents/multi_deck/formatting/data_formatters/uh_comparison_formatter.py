"""
Formatter de comparação para UHUsinasHidrelétricasTool no multi deck.
"""

from typing import Dict, Any, List
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class UHComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de resultados da UHUsinasHidrelétricasTool.
    Compara dados do Bloco UH entre múltiplos decks DECOMP.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da UHUsinasHidrelétricasTool."""
        return tool_name == "UHUsinasHidrelétricasTool" or "uh" in tool_name.lower()
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 10
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação do Bloco UH entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados formatados para visualização
        """
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        if not valid_decks:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "## Comparação Bloco UH\n\nNenhum dado válido encontrado para comparação."
            }
        
        # Extrair dados de cada deck
        all_usinas = {}  # codigo_usina -> {deck_name: dados}
        
        for deck in valid_decks:
            data = deck.result.get("data", [])
            for usina in data:
                codigo = usina.get("codigo_usina", usina.get("codigo", "unknown"))
                if codigo not in all_usinas:
                    all_usinas[codigo] = {}
                all_usinas[codigo][deck.display_name] = usina
        
        # Criar tabela comparativa
        comparison_table = []
        
        for codigo_usina in sorted(all_usinas.keys(), key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0):
            usina_decks = all_usinas[codigo_usina]
            
            # Linha base com código da usina
            row = {
                "codigo_usina": codigo_usina,
                "ree": usina_decks.get(list(usina_decks.keys())[0], {}).get("codigo_ree", "-")
            }
            
            # Adicionar dados de cada deck
            for deck_name in [d.display_name for d in decks_data if d.has_data]:
                usina_data = usina_decks.get(deck_name, {})
                row[f"{deck_name}_vini"] = usina_data.get("volume_inicial", usina_data.get("vini", "-"))
                row[f"{deck_name}_defmin"] = usina_data.get("vazao_minima", usina_data.get("defmin", "-"))
                row[f"{deck_name}_evap"] = usina_data.get("evaporacao", usina_data.get("evap", "-"))
            
            comparison_table.append(row)
        
        # Criar resposta em texto
        response_parts = ["## Comparação Bloco UH - Usinas Hidrelétricas\n\n"]
        response_parts.append(f"**Total de decks comparados**: {len(valid_decks)}\n\n")
        response_parts.append(f"**Total de usinas encontradas**: {len(comparison_table)}\n\n")
        
        response_parts.append("### Decks Comparados\n\n")
        for deck in valid_decks:
            total = len(deck.result.get("data", []))
            response_parts.append(f"- **{deck.display_name}**: {total} usinas\n")
        
        response_parts.append("\n### Tabela Comparativa\n\n")
        response_parts.append("*Use a visualização interativa abaixo para comparar os dados em detalhes.*\n\n")
        
        # Dados de visualização
        visualization_data = {
            "comparison_table": comparison_table[:100],  # Limitar para não sobrecarregar
            "chart_data": None,  # Pode ser expandido para gráficos
            "visualization_type": "table",
            "chart_config": {
                "type": "comparison_table",
                "title": "Comparação de Usinas Hidrelétricas (Bloco UH)",
                "x_axis": "Usina",
                "y_axis": "Valores",
                "tool_name": tool_name
            },
            "deck_names": [d.display_name for d in decks_data if d.has_data],
            "is_multi_deck": len(decks_data) > 2
        }
        
        return {
            "comparison_table": comparison_table,
            "chart_data": visualization_data.get("chart_data"),
            "visualization_type": "table",
            "chart_config": visualization_data.get("chart_config"),
            "deck_names": visualization_data["deck_names"],
            "is_multi_deck": visualization_data["is_multi_deck"],
            "final_response": "".join(response_parts)
        }

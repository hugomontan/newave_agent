"""
Formatter de comparação para DisponibilidadeUsinaTool no multi deck.
"""

from typing import Dict, Any, List
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class DisponibilidadeComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de resultados da DisponibilidadeUsinaTool.
    Compara disponibilidade de usinas térmicas entre múltiplos decks DECOMP.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da DisponibilidadeUsinaTool."""
        # Verificar por nome da tool
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "DisponibilidadeUsinaTool" or 
            tool_name == "DisponibilidadeMultiDeckTool" or
            "disponibilidade" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado (se tem disponibilidade_total)
        if result_structure and isinstance(result_structure, dict):
            if "disponibilidade_total" in result_structure:
                return True
            # Verificar se é um resultado de deck que contém disponibilidade_total
            if "usina" in result_structure and "disponibilidade_total" in result_structure:
                return True
        
        return False
    
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
        Formata comparação de disponibilidade entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados formatados para visualização (tabela + gráfico temporal)
        """
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        if not valid_decks:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "Nenhum dado válido encontrado para comparação."
            }
        
        # Extrair informações da usina (deve ser a mesma em todos os decks)
        usina_info = None
        for deck in valid_decks:
            usina = deck.result.get("usina", {})
            if usina:
                usina_info = usina
                break
        
        if not usina_info:
            # Tentar extrair do primeiro deck que tenha dados
            for deck in valid_decks:
                if deck.result:
                    usina_info = deck.result.get("usina", {})
                    if usina_info:
                        break
        
        nome_usina = usina_info.get("nome", "Usina Desconhecida") if usina_info else "Usina Desconhecida"
        codigo_usina = usina_info.get("codigo", "N/A") if usina_info else "N/A"
        
        # Criar tabela comparativa
        comparison_table = []
        chart_labels = []
        chart_data_points = []
        
        # Ordenar decks por data (se disponível) ou por nome
        sorted_decks = sorted(
            valid_decks,
            key=lambda d: (
                d.result.get("date") or "9999-99-99",
                d.name
            )
        )
        
        for deck in sorted_decks:
            result = deck.result
            disponibilidade = result.get("disponibilidade_total")
            
            if disponibilidade is None:
                continue
            
            # Extrair data do deck
            # A data pode estar no resultado (quando vem da tool multi-deck) ou precisamos extrair do nome do deck
            date = result.get("date")
            
            # Se não tem data no resultado, tentar extrair do nome do deck
            if not date:
                from decomp_agent.app.utils.deck_loader import parse_deck_name, calculate_week_thursday
                parsed = parse_deck_name(deck.name)
                if parsed and parsed.get("week"):
                    date = calculate_week_thursday(
                        parsed["year"],
                        parsed["month"],
                        parsed["week"]
                    )
            
            # Criar entrada na tabela
            table_row = {
                "data": date or deck.display_name,
                "deck": deck.name,
                "display_name": deck.display_name,
                "disponibilidade": float(disponibilidade),
                "usina_codigo": codigo_usina,
                "usina_nome": nome_usina
            }
            comparison_table.append(table_row)
            
            # Adicionar ao gráfico
            if date:
                chart_labels.append(date)
                chart_data_points.append(float(disponibilidade))
            else:
                # Se não tem data, usar display_name
                chart_labels.append(deck.display_name)
                chart_data_points.append(float(disponibilidade))
        
        # Criar dados do gráfico
        chart_data = {
            "labels": chart_labels,
            "datasets": [{
                "label": nome_usina,
                "data": chart_data_points,
                "borderColor": "rgb(59, 130, 246)",  # blue-500
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "tension": 0.1
            }]
        }
        
        # Configuração do gráfico
        chart_config = {
            "type": "line",
            "title": f"Evolução da Disponibilidade - {nome_usina}",
            "x_axis": "Data",
            "y_axis": "Disponibilidade (MW)",
            "tool_name": tool_name
        }
        
        # Resposta mínima - toda informação está na visualização (tabela + gráfico)
        # Usar uma string mínima para garantir que a resposta seja exibida
        final_response = f"Comparação de disponibilidade para {nome_usina}."
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": chart_config,
            "deck_names": [d.display_name for d in sorted_decks],
            "is_multi_deck": len(decks_data) > 2,
            "final_response": final_response
        }

"""
Formatter de comparação para volume inicial no multi deck DECOMP.
Específico para queries de volume inicial/nível de partida.
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.utils.deck_loader import parse_deck_name, calculate_week_thursday


class VolumeInicialComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de volume inicial entre múltiplos decks DECOMP.
    Retorna tabela + gráfico temporal mostrando a evolução do volume inicial ao longo do tempo.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """
        Verifica se pode formatar resultados de volume inicial.
        
        Verifica se:
        1. É a tool UHUsinasHidrelétricasTool ou VolumeInicialMultiDeckTool
        2. O resultado contém 'volume_inicial' e 'usina' (estrutura específica de volume inicial)
        """
        tool_name_lower = tool_name.lower() if tool_name else ""
        
        # Verificar por nome da tool
        is_volume_inicial_tool = (
            tool_name == "UHUsinasHidrelétricasTool" or
            tool_name == "VolumeInicialMultiDeckTool" or
            "volume inicial" in tool_name_lower or
            "volumeinicial" in tool_name_lower
        )
        
        if not is_volume_inicial_tool:
            return False
        
        # Verificar estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            # Se tem volume_inicial e usina diretamente, é resultado de volume inicial
            if "volume_inicial" in result_structure and "usina" in result_structure:
                volume_val = result_structure.get("volume_inicial")
                usina_val = result_structure.get("usina")
                if isinstance(volume_val, (int, float)) and isinstance(usina_val, dict):
                    return True
            
            # Verificar se é um resultado de deck que contém volume inicial
            if "result" in result_structure:
                deck_result = result_structure.get("result", {})
                if isinstance(deck_result, dict):
                    if "volume_inicial" in deck_result and "usina" in deck_result:
                        return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade muito alta para esta tool específica (maior que UHComparisonFormatter)."""
        return 95  # Maior que UHComparisonFormatter (10)
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata série temporal de volume inicial entre múltiplos decks.
        Cada deck contribui com um ponto na evolução temporal.
        
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
        
        # Extrair informações da usina (do primeiro deck)
        usina_info = None
        for deck in valid_decks:
            result = deck.result
            usina = result.get("usina", {})
            if usina and isinstance(usina, dict):
                usina_info = usina
                break
        
        nome_usina = usina_info.get("nome", "Usina Desconhecida") if usina_info else "Usina Desconhecida"
        codigo_usina = usina_info.get("codigo", "N/A") if usina_info else "N/A"
        
        # Coletar dados de volume inicial de cada deck com suas datas
        deck_data_map = {}  # {date: {deck_name: volume_inicial}}
        all_dates = set()
        all_deck_names = []
        
        for deck in valid_decks:
            result = deck.result
            
            # Extrair volume inicial
            volume_inicial = result.get("volume_inicial")
            if volume_inicial is None:
                continue
            
            # Obter data do deck (quinta-feira da semana)
            date = result.get("date")
            if not date:
                # Tentar calcular a partir do nome do deck
                parsed = parse_deck_name(deck.name)
                if parsed and parsed.get("week"):
                    date = calculate_week_thursday(
                        parsed["year"],
                        parsed["month"],
                        parsed["week"]
                    )
            
            if not date:
                continue
            
            all_dates.add(date)
            deck_display_name = deck.display_name
            
            if deck_display_name not in all_deck_names:
                all_deck_names.append(deck_display_name)
            
            if date not in deck_data_map:
                deck_data_map[date] = {}
            
            deck_data_map[date][deck_display_name] = float(volume_inicial)
        
        # Ordenar datas cronologicamente
        sorted_dates = sorted(all_dates)
        
        # Construir tabela no formato: Data | Volume Inicial (uma única coluna)
        comparison_table = []
        chart_labels = []
        chart_data_points = []
        
        # Processar cada data - cada deck contribui com uma linha na série temporal
        for date in sorted_dates:
            # Encontrar qual deck tem dados nesta data
            volume = None
            deck_name = None
            
            for deck_display_name in all_deck_names:
                if date in deck_data_map and deck_display_name in deck_data_map[date]:
                    volume = deck_data_map[date][deck_display_name]
                    deck_name = deck_display_name
                    break
            
            if volume is not None:
                row = {
                    "data": date,
                    "volume_inicial": f"{volume}%"
                }
                comparison_table.append(row)
                chart_labels.append(date)
                chart_data_points.append(volume)
        
        # Construir chart_data - uma única série temporal
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": f"Volume Inicial - {nome_usina}",
                    "data": chart_data_points,
                    "borderColor": "rgb(59, 130, 246)",  # blue-500
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }
            ]
        } if chart_labels else None
        
        # Configuração do gráfico
        chart_config = {
            "type": "line",
            "title": f"Evolução do Volume Inicial - {nome_usina}",
            "x_axis": "Data",
            "y_axis": "Volume Inicial (%)",
            "tool_name": tool_name
        }
        
        # Resposta mínima
        final_response = f"Série temporal de volume inicial para {nome_usina}."
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": chart_config,
            "deck_names": all_deck_names,
            "is_multi_deck": len(decks_data) > 2,
            "final_response": final_response
        }

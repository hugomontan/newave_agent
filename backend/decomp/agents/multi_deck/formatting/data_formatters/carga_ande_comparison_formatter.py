"""
Formatter de comparação para Carga ANDE no multi deck DECOMP.
Formata como timeseries de carga ANDE ponderada.
"""

from typing import Dict, Any, List, Optional
from backend.decomp.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from backend.decomp.agents.multi_deck.formatting.data_formatters.dp_comparison_formatter import format_compact_label


class CargaAndeComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de Carga ANDE entre múltiplos decks DECOMP.
    
    Formata como timeseries de carga ANDE ponderada, mostrando:
    - Tabela com datas de cada deck + Carga ANDE ponderada
    - Gráfico de linha mostrando a evolução temporal
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de Carga ANDE."""
        # Verificar por nome da tool
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "CargaAndeTool" or 
            tool_name == "CargaAndeMultiDeckTool" or
            "carga ande" in tool_name_lower or
            "ande" in tool_name_lower and "carga" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            # Verificar se tem tool_name indicando Carga ANDE
            if result_structure.get("tool_name") == "CargaAndeTool":
                return True
            # Verificar se é um resultado de deck que contém carga_ande_ponderada
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        # Verificar se tem carga_ande_ponderada
                        if "carga_ande_ponderada" in first_deck:
                            return True
                        # Verificar resultado interno
                        result = first_deck.get("result", {})
                        data = result.get("data", [])
                        if data and isinstance(data, list) and len(data) > 0:
                            if isinstance(data[0], dict) and "carga_ande_media_ponderada" in data[0]:
                                return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 10
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de Carga ANDE entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados formatados para visualização (tabela + gráfico temporal)
        """
        from backend.decomp.config import safe_print
        
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        if not valid_decks:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhum dado válido encontrado para comparação de Carga ANDE.",
                "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name mesmo quando não há dados
            }
        
        # Extrair carga ANDE de todos os decks (cada deck = um ponto na timeseries)
        all_dates = []
        carga_ande_por_deck = {}  # {deck_name: {"date": date, "mwmed": value, "display_name": ...}}
        
        # Primeiro, coletar todos os dados de todos os decks
        for deck in valid_decks:
            result = deck.result
            carga_ande_ponderada = None
            
            # Tentar extrair dos dados primeiro (mais confiável)
            if result.get("data"):
                data = result.get("data", [])
                if data and len(data) > 0:
                    primeiro_registro = data[0]
                    carga_ande_ponderada = (
                        primeiro_registro.get("carga_ande_media_ponderada") or
                        primeiro_registro.get("mw_medio")
                    )
            
            # Se ainda não encontrou, tentar campo direto no result (caso venha do multi-deck)
            if carga_ande_ponderada is None:
                carga_ande_ponderada = result.get("carga_ande_ponderada")
            
            # Extrair data do deck
            date = result.get("date")
            
            # Se não tem data no resultado, tentar extrair do nome do deck
            if not date:
                from backend.decomp.utils.deck_loader import parse_deck_name, calculate_week_thursday
                parsed = parse_deck_name(deck.name)
                if parsed and parsed.get("week"):
                    date = calculate_week_thursday(
                        parsed["year"],
                        parsed["month"],
                        parsed["week"]
                    )
            
            if date:
                all_dates.append(date)
            
            # Incluir valores zero (0.0) - apenas ignorar None
            if carga_ande_ponderada is None:
                continue
            
            # Garantir que seja float válido
            try:
                carga_ande_value = float(carga_ande_ponderada)
            except (ValueError, TypeError):
                continue
            
            # Armazenar dados do deck
            carga_ande_por_deck[deck.name] = {
                "date": date,
                "mwmed": round(carga_ande_value, 2),
                "display_name": deck.display_name
            }
        
        if not carga_ande_por_deck:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhuma carga ANDE encontrada para comparação.",
                "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name mesmo quando não há dados
            }
        
        # Ordenar datas
        sorted_dates = sorted(set(all_dates)) if all_dates else []
        
        # Construir tabela: uma linha por deck/data (cada deck = um ponto no tempo)
        comparison_table = []
        
        # Coletar todos os decks únicos com suas datas (como no DP/PQ)
        deck_date_map = {}
        for deck in valid_decks:
            if deck.name in carga_ande_por_deck:
                date = carga_ande_por_deck[deck.name]["date"]
                if date:
                    if date not in deck_date_map:
                        deck_date_map[date] = []
                    deck_date_map[date].append({
                        "name": deck.name,
                        "display_name": deck.display_name
                    })
        
        # Construir linhas da tabela (uma por data/deck)
        for date in sorted_dates:
            decks_for_date = deck_date_map.get(date, [])
            for deck_info in decks_for_date:
                deck_name = deck_info["name"]
                display_name = deck_info["display_name"]
                
                deck_data = carga_ande_por_deck.get(deck_name)
                if not deck_data:
                    continue
                
                # Tabela com 2 colunas: data e mwmed (formato clássico timeseries)
                table_row = {
                    "data": date,
                    "mwmed": deck_data["mwmed"]
                }
                comparison_table.append(table_row)
        
        # Construir dados do gráfico: uma única série temporal
        # Usar formato compacto para labels: "JAN25 - S1" (como no PQ/DP)
        chart_labels = [
            format_compact_label(
                carga_ande_por_deck[deck_info["name"]]["display_name"] if deck_info["name"] in carga_ande_por_deck else deck_info["display_name"],
                deck_info["name"]
            )
            for date in sorted_dates
            for deck_info in deck_date_map.get(date, [])
            if deck_info["name"] in carga_ande_por_deck
        ]
        
        chart_data_points = [
            carga_ande_por_deck[deck_info["name"]]["mwmed"]
            for date in sorted_dates
            for deck_info in deck_date_map.get(date, [])
            if deck_info["name"] in carga_ande_por_deck
        ]
        
        # Construir chart_data - uma única série temporal
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "Carga ANDE (MW médio)",
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
            "title": "Evolução da Carga ANDE",
            "x_axis": "Data",
            "y_axis": "Carga ANDE (MW médio)",
            "tool_name": tool_name
        }
        
        # Resposta final
        final_response = f"Evolução da Carga ANDE ao longo do tempo. Mostrando {len(comparison_table)} períodos."
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": chart_config,
            "deck_names": [d.display_name for d in valid_decks],
            "is_multi_deck": len(decks_data) >= 2,
            "final_response": final_response,
            "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name para o ComparisonRouter
        }

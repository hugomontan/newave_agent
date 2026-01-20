"""
Formatter de comparação para LimitesIntercambioDECOMPTool no multi deck.
Formata como timeseries de MW médio por par/sentido de intercâmbio.
Similar ao CargaAndeComparisonFormatter.
"""
from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.agents.multi_deck.formatting.data_formatters.dp_comparison_formatter import format_compact_label
from decomp_agent.app.config import safe_print


class LimitesIntercambioComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de Limites de Intercâmbio entre múltiplos decks DECOMP.
    
    Formata como timeseries de MW médio ponderado por par/sentido, mostrando:
    - Tabela com datas de cada deck + MW médio por sentido
    - Gráfico de linha mostrando a evolução temporal de cada sentido
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar LimitesIntercambioDECOMPTool."""
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "LimitesIntercambioDECOMPTool" or 
            tool_name == "LimitesIntercambioMultiDeckTool" or
            "limites" in tool_name_lower and "intercambio" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            if result_structure.get("tool_name") == "LimitesIntercambioDECOMPTool":
                return True
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        result = first_deck.get("result", {})
                        data = result.get("data", [])
                        if data and isinstance(data, list) and len(data) > 0:
                            if isinstance(data[0], dict) and ("mw_medio_de_para" in data[0] or "mw_medio_para_de" in data[0]):
                                return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 85  # Alta prioridade para garantir que seja selecionado
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de Limites de Intercâmbio entre múltiplos decks.
        
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
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhum dado válido encontrado para comparação de Limites de Intercâmbio.",
                "tool_name": tool_name
            }
        
        # Coletar todos os MW médios de todos os decks, agrupados por sentido
        # Estrutura: {sentido_key: {deck_name: {"date": date, "mwmed": value, "display_name": ...}}}
        all_sentidos = {}  # {sentido_key: {deck_name: {...}}}
        all_dates = []
        
        for deck in valid_decks:
            result = deck.result
            mw_medios_por_sentido = result.get("mw_medios_por_sentido", {})
            
            # Se não tem mw_medios_por_sentido, tentar extrair dos dados
            if not mw_medios_por_sentido and result.get("data"):
                data = result.get("data", [])
                mw_medios_por_sentido = {}
                for record in data:
                    # MW médio DE->PARA
                    mw_medio_de_para = record.get("mw_medio_de_para")
                    if mw_medio_de_para is not None:
                        sub_de = record.get("sub_de", "?")
                        sub_para = record.get("sub_para", "?")
                        sentido_key = f"{sub_de}→{sub_para}"
                        mw_medios_por_sentido[sentido_key] = {
                            "sentido": f"{sub_de} → {sub_para}",
                            "mw_medio": mw_medio_de_para,
                            "sub_de": sub_de,
                            "sub_para": sub_para
                        }
                    
                    # MW médio PARA->DE
                    mw_medio_para_de = record.get("mw_medio_para_de")
                    if mw_medio_para_de is not None:
                        sub_de = record.get("sub_de", "?")
                        sub_para = record.get("sub_para", "?")
                        sentido_key = f"{sub_para}→{sub_de}"
                        mw_medios_por_sentido[sentido_key] = {
                            "sentido": f"{sub_para} → {sub_de}",
                            "mw_medio": mw_medio_para_de,
                            "sub_de": sub_para,
                            "sub_para": sub_de
                        }
            
            # Extrair data do deck
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
            
            if date:
                all_dates.append(date)
            
            # Processar cada sentido encontrado neste deck
            for sentido_key, sentido_data in mw_medios_por_sentido.items():
                mw_medio = sentido_data.get("mw_medio")
                
                # Incluir valores zero (0.0) - apenas ignorar None
                if mw_medio is None:
                    continue
                
                # Garantir que seja float válido
                try:
                    mw_medio_value = float(mw_medio)
                except (ValueError, TypeError):
                    continue
                
                # Inicializar estrutura para este sentido se não existir
                if sentido_key not in all_sentidos:
                    all_sentidos[sentido_key] = {}
                
                # Armazenar dados do deck para este sentido
                all_sentidos[sentido_key][deck.name] = {
                    "date": date,
                    "mwmed": round(mw_medio_value, 2),
                    "display_name": deck.display_name,
                    "sentido_label": sentido_data.get("sentido", sentido_key)
                }
        
        if not all_sentidos:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhum limite de intercâmbio encontrado para comparação.",
                "tool_name": tool_name
            }
        
        # Ordenar datas
        sorted_dates = sorted(set(all_dates)) if all_dates else []
        
        # Construir tabela: uma linha por deck/data/sentido
        comparison_table = []
        
        # Coletar todos os decks únicos com suas datas
        deck_date_map = {}
        for deck in valid_decks:
            result = deck.result
            date = result.get("date")
            if not date:
                from decomp_agent.app.utils.deck_loader import parse_deck_name, calculate_week_thursday
                parsed = parse_deck_name(deck.name)
                if parsed and parsed.get("week"):
                    date = calculate_week_thursday(
                        parsed["year"],
                        parsed["month"],
                        parsed["week"]
                    )
            
            if date:
                if date not in deck_date_map:
                    deck_date_map[date] = []
                deck_date_map[date].append({
                    "name": deck.name,
                    "display_name": deck.display_name
                })
        
        # Construir linhas da tabela (uma por data/deck/sentido)
        for date in sorted_dates:
            decks_for_date = deck_date_map.get(date, [])
            for deck_info in decks_for_date:
                deck_name = deck_info["name"]
                
                # Para cada sentido, adicionar linha na tabela
                for sentido_key, sentido_decks in all_sentidos.items():
                    deck_data = sentido_decks.get(deck_name)
                    if not deck_data:
                        continue
                    
                    # Tabela com colunas: data, sentido, mwmed
                    table_row = {
                        "data": date,
                        "sentido": deck_data["sentido_label"],
                        "mwmed": deck_data["mwmed"]
                    }
                    comparison_table.append(table_row)
        
        # Construir dados do gráfico: uma série temporal por sentido
        # Cada sentido terá sua própria linha no gráfico
        chart_datasets = []
        colors = [
            "rgb(59, 130, 246)",   # blue-500
            "rgb(16, 185, 129)",   # emerald-500
            "rgb(245, 158, 11)",   # amber-500
            "rgb(239, 68, 68)",    # red-500
            "rgb(139, 92, 246)",   # violet-500
            "rgb(236, 72, 153)",   # pink-500
        ]
        
        # Labels do gráfico (uma por data/deck)
        chart_labels = [
            format_compact_label(
                deck_info["display_name"],
                deck_info["name"]
            )
            for date in sorted_dates
            for deck_info in deck_date_map.get(date, [])
        ]
        
        # Criar dataset para cada sentido
        for idx, (sentido_key, sentido_decks) in enumerate(all_sentidos.items()):
            sentido_label = list(sentido_decks.values())[0]["sentido_label"] if sentido_decks else sentido_key
            
            # Coletar valores deste sentido para cada data/deck
            sentido_data_points = []
            for date in sorted_dates:
                decks_for_date = deck_date_map.get(date, [])
                for deck_info in decks_for_date:
                    deck_name = deck_info["name"]
                    deck_data = sentido_decks.get(deck_name)
                    if deck_data:
                        sentido_data_points.append(deck_data["mwmed"])
                    else:
                        sentido_data_points.append(None)  # Deck não tem este sentido
            
            # Só adicionar dataset se houver pelo menos um valor não-nulo
            if any(v is not None for v in sentido_data_points):
                color = colors[idx % len(colors)]
                # Converter rgb para rgba com transparência
                rgba_color = color.replace("rgb(", "rgba(").replace(")", ", 0.1)")
                chart_datasets.append({
                    "label": sentido_label,
                    "data": sentido_data_points,
                    "borderColor": color,
                    "backgroundColor": rgba_color,
                    "fill": False,
                    "tension": 0.4
                })
        
        # Construir chart_data - múltiplas séries temporais (uma por sentido)
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels and chart_datasets else None
        
        # Configuração do gráfico
        chart_config = {
            "type": "line",
            "title": "Evolução dos Limites de Intercâmbio",
            "x_axis": "Data",
            "y_axis": "Limite de Intercâmbio (MW médio)",
            "tool_name": tool_name
        }
        
        # Resposta final
        num_sentidos = len(all_sentidos)
        final_response = f"Evolução dos Limites de Intercâmbio ao longo do tempo. Mostrando {num_sentidos} sentido(s) em {len(comparison_table)} períodos."
        
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

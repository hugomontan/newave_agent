"""
Formatter de comparação para carga dos subsistemas (DP) no multi deck DECOMP.
Formata como timeseries de MW médio por submercado.
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
import math
import re


# Mapeamento de códigos de submercado para nomes
SUBMERCADO_NAMES = {
    1: "SUDESTE",
    2: "SUL",
    3: "NORDESTE",
    4: "NORTE"
}

# Mapeamento de mês para abreviação
MONTH_ABBREV = {
    "Janeiro": "JAN",
    "Fevereiro": "FEV",
    "Março": "MAR",
    "Abril": "ABR",
    "Maio": "MAI",
    "Junho": "JUN",
    "Julho": "JUL",
    "Agosto": "AGO",
    "Setembro": "SET",
    "Outubro": "OUT",
    "Novembro": "NOV",
    "Dezembro": "DEZ"
}


def format_compact_label(display_name: str, deck_name: str = None) -> str:
    """
    Formata label compacta no formato "JAN25 - S1" a partir do display_name ou deck_name.
    
    Args:
        display_name: Nome amigável (ex: "Janeiro 2025 - Semana 1")
        deck_name: Nome do deck (ex: "DC202501-sem1")
        
    Returns:
        Label formatada (ex: "JAN25 - S1")
    """
    # Tentar extrair do display_name primeiro
    if display_name:
        # Padrão: "Janeiro 2025 - Semana 1" -> "JAN25 - S1"
        match = re.match(r'^(\w+)\s+(\d{4})\s*-\s*Semana\s+(\d+)$', display_name)
        if match:
            month_name = match.group(1)
            year = match.group(2)
            week = match.group(3)
            
            month_abbrev = MONTH_ABBREV.get(month_name, month_name[:3].upper())
            year_short = year[-2:]  # Últimos 2 dígitos do ano
            
            return f"{month_abbrev}{year_short} - S{week}"
        
        # Padrão sem semana: "Janeiro 2025" -> "JAN25"
        match = re.match(r'^(\w+)\s+(\d{4})$', display_name)
        if match:
            month_name = match.group(1)
            year = match.group(2)
            
            month_abbrev = MONTH_ABBREV.get(month_name, month_name[:3].upper())
            year_short = year[-2:]
            
            return f"{month_abbrev}{year_short}"
    
    # Fallback: tentar extrair do deck_name
    if deck_name:
        from decomp_agent.app.utils.deck_loader import parse_deck_name
        parsed = parse_deck_name(deck_name)
        if parsed:
            year = parsed.get("year")
            month = parsed.get("month")
            week = parsed.get("week")
            
            if year and month:
                month_names = [
                    "JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                    "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"
                ]
                month_abbrev = month_names[month - 1] if 1 <= month <= 12 else f"M{month}"
                year_short = str(year)[-2:]
                
                if week:
                    return f"{month_abbrev}{year_short} - S{week}"
                else:
                    return f"{month_abbrev}{year_short}"
    
    # Fallback final: retornar display_name ou deck_name truncado
    return display_name or deck_name or ""


class DPComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de carga dos subsistemas (DP) entre múltiplos decks DECOMP.
    
    Formata como timeseries de MW médio por submercado, mostrando:
    - Tabela com datas de cada deck + MW médio do estágio 1 por submercado
    - Gráfico de linha mostrando a evolução temporal
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de DP."""
        # Verificar por nome da tool
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "DPCargaSubsistemasTool" or 
            tool_name == "DPMultiDeckTool" or
            "dp" in tool_name_lower or
            "carga subsistemas" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado (se tem mw_medios SEM campo "tipo")
        # IMPORTANTE: Não aceitar dados que têm "tipo" (esses são de PQ, não DP)
        if result_structure and isinstance(result_structure, dict):
            if "mw_medios" in result_structure:
                mw_medios = result_structure.get("mw_medios", [])
                # Se mw_medios tem campo "tipo", é PQ, não DP
                if isinstance(mw_medios, list) and len(mw_medios) > 0:
                    if isinstance(mw_medios[0], dict) and "tipo" in mw_medios[0]:
                        return False  # É PQ, não DP
                return True
            # Verificar se é um resultado de deck que contém dados de MW médio
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        result = first_deck.get("result", {})
                        mw_medios = result.get("mw_medios", [])
                        # Se mw_medios tem campo "tipo", é PQ, não DP
                        if isinstance(mw_medios, list) and len(mw_medios) > 0:
                            if isinstance(mw_medios[0], dict) and "tipo" in mw_medios[0]:
                                return False  # É PQ, não DP
                        if mw_medios or result.get("calcular_media_ponderada"):
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
        Formata comparação de carga dos subsistemas entre múltiplos decks.
        
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
        
        # Extrair MW médios de todos os decks, agrupados por submercado
        # Estrutura: {codigo_submercado: {deck_name: mw_medio, ...}}
        mw_medios_por_submercado = {}
        all_dates = []
        
        for deck in valid_decks:
            result = deck.result
            date = result.get("date")
            
            if date:
                all_dates.append(date)
            
            # Extrair MW médios: pode estar em mw_medios ou nos dados individuais
            mw_medios = result.get("mw_medios", [])
            
            # Se não há mw_medios explícito, tentar extrair dos dados
            if not mw_medios and result.get("data"):
                data = result.get("data", [])
                for record in data:
                    mw_medio = record.get("mw_medio") or record.get("carga_media_ponderada")
                    codigo_submercado = (
                        record.get("codigo_submercado") or 
                        record.get("submercado") or 
                        record.get("s")
                    )
                    
                    if codigo_submercado is not None and mw_medio is not None:
                        mw_medios.append({
                            "codigo_submercado": codigo_submercado,
                            "mw_medio": mw_medio
                        })
            
            # Processar MW médios deste deck
            for mw_data in mw_medios:
                codigo_submercado = mw_data.get("codigo_submercado")
                mw_medio = mw_data.get("mw_medio")
                
                if codigo_submercado is not None and mw_medio is not None:
                    if codigo_submercado not in mw_medios_por_submercado:
                        mw_medios_por_submercado[codigo_submercado] = {}
                    
                    mw_medios_por_submercado[codigo_submercado][deck.name] = {
                        "mw_medio": mw_medio,
                        "date": date,
                        "display_name": deck.display_name
                    }
        
        if not mw_medios_por_submercado:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "Nenhum MW médio encontrado para comparação."
            }
        
        # Ordenar datas
        sorted_dates = sorted(set(all_dates)) if all_dates else []
        
        # Construir tabela: uma linha por deck/data, colunas por submercado
        comparison_table = []
        
        # Coletar todos os decks únicos com suas datas
        deck_date_map = {}
        for deck in valid_decks:
            result = deck.result
            date = result.get("date")
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
                
                table_row = {
                    "data": date,
                    "deck": deck_name,
                    "display_name": display_name
                }
                
                # Adicionar MW médio de cada submercado
                for codigo_submercado in sorted(mw_medios_por_submercado.keys()):
                    nome_submercado = SUBMERCADO_NAMES.get(codigo_submercado, f"Submercado {codigo_submercado}")
                    submercado_data = mw_medios_por_submercado[codigo_submercado].get(deck_name)
                    
                    if submercado_data:
                        table_row[f"submercado_{codigo_submercado}"] = submercado_data["mw_medio"]
                        table_row[f"submercado_{codigo_submercado}_nome"] = nome_submercado
                    else:
                        table_row[f"submercado_{codigo_submercado}"] = None
                        table_row[f"submercado_{codigo_submercado}_nome"] = nome_submercado
                
                comparison_table.append(table_row)
        
        # Construir dados do gráfico: uma série por submercado
        # Usar formato compacto para labels: "JAN25 - S1"
        chart_labels = [
            format_compact_label(row.get("display_name", ""), row.get("deck", ""))
            for row in comparison_table
        ]
        chart_datasets = []
        
        # Cores para cada submercado
        submercado_colors = {
            1: "rgb(239, 68, 68)",   # red-500 - Sudeste
            2: "rgb(34, 197, 94)",   # green-500 - Sul
            3: "rgb(234, 179, 8)",   # yellow-500 - Nordeste
            4: "rgb(59, 130, 246)",  # blue-500 - Norte
        }
        
        for codigo_submercado in sorted(mw_medios_por_submercado.keys()):
            nome_submercado = SUBMERCADO_NAMES.get(codigo_submercado, f"Submercado {codigo_submercado}")
            color = submercado_colors.get(codigo_submercado, "rgb(156, 163, 175)")
            
            dataset_data = []
            for row in comparison_table:
                mw_medio = row.get(f"submercado_{codigo_submercado}")
                dataset_data.append(mw_medio)
            
            chart_datasets.append({
                "label": nome_submercado,
                "data": dataset_data,
                "borderColor": color,
                "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.1)"),
            })
        
        # Construir chart_data
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Configuração do gráfico
        chart_config = {
            "type": "line",
            "title": "Evolução do MW Médio por Submercado",
            "x_axis": "Deck/Data",
            "y_axis": "MW Médio (MWmed)",
            "tool_name": tool_name
        }
        
        # Resposta mínima
        submercados_mencoes = []
        for codigo in sorted(mw_medios_por_submercado.keys()):
            nome = SUBMERCADO_NAMES.get(codigo, f"Submercado {codigo}")
            submercados_mencoes.append(nome)
        
        final_response = f"Comparação de carga média ponderada (MW médio) para {', '.join(submercados_mencoes)}."
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": chart_config,
            "deck_names": [d.display_name for d in valid_decks],
            "is_multi_deck": len(decks_data) > 2,
            "final_response": final_response,
            "submercados": [{"codigo": codigo, "nome": SUBMERCADO_NAMES.get(codigo, f"Submercado {codigo}")} 
                          for codigo in sorted(mw_medios_por_submercado.keys())]
        }

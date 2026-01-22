"""
Formatter de comparação para RestricoesVazaoHQTool no multi deck.
Consolida dados de múltiplos decks em uma tabela e dois gráficos (GMIN e GMAX).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.agents.multi_deck.formatting.data_formatters.dp_comparison_formatter import format_compact_label
import math


def _to_num(v):
    """Helper para converter valores numéricos (NaN/None -> None para vazão, 0 para outros)."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None


class RestricoesVazaoHQComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de Restrições de Vazão (HQ) entre múltiplos decks DECOMP.
    
    Formata como:
    - Tabela consolidada: uma linha por deck com GMIN/GMAX por patamar
    - Gráfico GMIN: evolução temporal dos limites mínimos (P1, P2, P3)
    - Gráfico GMAX: evolução temporal dos limites máximos (P1, P2, P3)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar RestricoesVazaoHQTool."""
        tool_name_lower = tool_name.lower() if tool_name else ""
        
        # Verificar por nome da tool
        if (
            tool_name == "RestricoesVazaoHQTool" or
            tool_name == "RestricoesVazaoHQConjuntaTool" or
            tool_name == "RestricoesVazaoHQMultiDeckTool" or
            "vazao" in tool_name_lower and "hq" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            # IMPORTANTE: Verificar primeiro se NÃO é GL (para evitar conflito)
            # Dados GL têm geracao_patamar_X, não GMIN/GMAX
            if "data" in result_structure:
                data = result_structure.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0] if isinstance(data[0], dict) else {}
                    # Se tem geracao_patamar_X, é GL, não restrição de vazão
                    if "geracao_patamar_1" in first_item or "geracao_pat_1" in first_item:
                        return False
                    # Verificar presença de campos específicos de restrições de vazão
                    if any(
                        key in first_item 
                        for key in [
                            "GMIN P1", "GMAX P1", 
                            "limite_inferior_1", "limite_superior_1",
                            "limites_inferiores_1", "limites_superiores_1"
                        ]
                    ):
                        return True
            
            # Verificar se é resultado de deck que contém dados de restrições de vazão
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        result = first_deck.get("result", {})
                        data = result.get("data", [])
                        if isinstance(data, list) and len(data) > 0:
                            first_item = data[0] if isinstance(data[0], dict) else {}
                            # Se tem geracao_patamar_X, é GL, não restrição de vazão
                            if "geracao_patamar_1" in first_item or "geracao_pat_1" in first_item:
                                return False
                            # Verificar presença de campos específicos de restrições de vazão
                            if any(
                                key in first_item 
                                for key in [
                                    "GMIN P1", "GMAX P1", 
                                    "limite_inferior_1", "limite_superior_1",
                                    "limites_inferiores_1", "limites_superiores_1"
                                ]
                            ):
                                return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 85  # Alta prioridade, similar a RestricoesEletricas
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de Restrições de Vazão entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados formatados para visualização (tabela + 2 gráficos)
        """
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        if not valid_decks:
            return {
                "comparison_table": [],
                "chart_data_gmin": None,
                "chart_data_gmax": None,
                "visualization_type": "restricoes_vazao_hq_comparison",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhum dado válido encontrado para comparação de Restrições de Vazão.",
                "tool_name": tool_name
            }
        
        # Coletar dados de todos os decks
        comparison_table = []
        nome_restricao = None
        
        for deck in valid_decks:
            result = deck.result
            data = result.get("data", []) or []
            
            # Pegar o primeiro registro (assumindo que query retorna apenas uma restrição)
            if not data:
                # Deck sem dados para esta restrição
                comparison_table.append({
                    "deck": deck.name,
                    "display_name": deck.display_name,
                    "Nome": None,
                    "GMIN P1": None,
                    "GMIN P2": None,
                    "GMIN P3": None,
                    "GMAX P1": None,
                    "GMAX P2": None,
                    "GMAX P3": None,
                })
                continue
            
            first_row = data[0] if isinstance(data[0], dict) else {}
            
            # Extrair nome da restrição/usina (usar do primeiro deck válido)
            if nome_restricao is None:
                # Para restrições de vazão, pode vir de diferentes campos
                nome_restricao = (
                    first_row.get("nome_usina") or
                    first_row.get("Nome") or
                    first_row.get("nome") or
                    "?"
                )
                # Se for restrição conjunta, pode ter formato especial
                if "usinas_envolvidas" in first_row:
                    usinas_env = first_row.get("usinas_envolvidas", "")
                    if usinas_env:
                        # Extrair apenas os nomes (antes dos parênteses) e juntar com " + "
                        nomes = []
                        for parte in usinas_env.split(","):
                            parte_limpa = parte.strip()
                            if "(" in parte_limpa:
                                nome_so = parte_limpa.split("(")[0].strip()
                                if nome_so:
                                    nomes.append(nome_so)
                            else:
                                if parte_limpa:
                                    nomes.append(parte_limpa)
                        if nomes:
                            nome_restricao = " + ".join(nomes)
            
            # Extrair GMIN/GMAX - verificar múltiplos formatos possíveis
            # Formato 1: "GMIN P1", "GMAX P1" (do single-deck formatter)
            # Formato 2: "limite_inferior_1", "limite_superior_1" (do tool bruto)
            # Para vazão, permitir None (será exibido como "-" ou 0)
            gmin_p1 = _to_num(
                first_row.get("GMIN P1") or 
                first_row.get("limite_inferior_1") or
                first_row.get("limites_inferiores_1")
            )
            gmin_p2 = _to_num(
                first_row.get("GMIN P2") or 
                first_row.get("limite_inferior_2") or
                first_row.get("limites_inferiores_2")
            )
            gmin_p3 = _to_num(
                first_row.get("GMIN P3") or 
                first_row.get("limite_inferior_3") or
                first_row.get("limites_inferiores_3")
            )
            
            gmax_p1 = _to_num(
                first_row.get("GMAX P1") or 
                first_row.get("limite_superior_1") or
                first_row.get("limites_superiores_1")
            )
            gmax_p2 = _to_num(
                first_row.get("GMAX P2") or 
                first_row.get("limite_superior_2") or
                first_row.get("limites_superiores_2")
            )
            gmax_p3 = _to_num(
                first_row.get("GMAX P3") or 
                first_row.get("limite_superior_3") or
                first_row.get("limites_superiores_3")
            )
            
            # Converter None para 0 para exibição (ou manter None se preferir "-")
            gmin_p1 = gmin_p1 if gmin_p1 is not None else 0
            gmin_p2 = gmin_p2 if gmin_p2 is not None else 0
            gmin_p3 = gmin_p3 if gmin_p3 is not None else 0
            gmax_p1 = gmax_p1 if gmax_p1 is not None else 0
            gmax_p2 = gmax_p2 if gmax_p2 is not None else 0
            gmax_p3 = gmax_p3 if gmax_p3 is not None else 0
            
            comparison_table.append({
                "deck": deck.name,
                "display_name": deck.display_name,
                "Nome": nome_restricao,
                "GMIN P1": gmin_p1,
                "GMIN P2": gmin_p2,
                "GMIN P3": gmin_p3,
                "GMAX P1": gmax_p1,
                "GMAX P2": gmax_p2,
                "GMAX P3": gmax_p3,
            })
        
        if not comparison_table:
            return {
                "comparison_table": [],
                "chart_data_gmin": None,
                "chart_data_gmax": None,
                "visualization_type": "restricoes_vazao_hq_comparison",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,
                "final_response": "Nenhuma restrição de vazão encontrada para comparação.",
                "tool_name": tool_name
            }
        
        # Construir labels compactas para os gráficos
        chart_labels = [
            format_compact_label(row.get("display_name", ""), row.get("deck", ""))
            for row in comparison_table
        ]
        
        # Construir gráfico GMIN (3 séries: P1, P2, P3)
        chart_data_gmin = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "GMIN P1",
                    "data": [row.get("GMIN P1") for row in comparison_table],
                    "borderColor": "rgb(59, 130, 246)",  # blue-500
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": False,
                    "tension": 0.4
                },
                {
                    "label": "GMIN P2",
                    "data": [row.get("GMIN P2") for row in comparison_table],
                    "borderColor": "rgb(16, 185, 129)",  # emerald-500
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": False,
                    "tension": 0.4
                },
                {
                    "label": "GMIN P3",
                    "data": [row.get("GMIN P3") for row in comparison_table],
                    "borderColor": "rgb(245, 158, 11)",  # amber-500
                    "backgroundColor": "rgba(245, 158, 11, 0.1)",
                    "fill": False,
                    "tension": 0.4
                }
            ]
        }
        
        # Construir gráfico GMAX (3 séries: P1, P2, P3)
        chart_data_gmax = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "GMAX P1",
                    "data": [row.get("GMAX P1") for row in comparison_table],
                    "borderColor": "rgb(239, 68, 68)",  # red-500
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    "fill": False,
                    "tension": 0.4
                },
                {
                    "label": "GMAX P2",
                    "data": [row.get("GMAX P2") for row in comparison_table],
                    "borderColor": "rgb(234, 179, 8)",  # yellow-500
                    "backgroundColor": "rgba(234, 179, 8, 0.1)",
                    "fill": False,
                    "tension": 0.4
                },
                {
                    "label": "GMAX P3",
                    "data": [row.get("GMAX P3") for row in comparison_table],
                    "borderColor": "rgb(139, 92, 246)",  # violet-500
                    "backgroundColor": "rgba(139, 92, 246, 0.1)",
                    "fill": False,
                    "tension": 0.4
                }
            ]
        }
        
        # Configurações dos gráficos
        chart_config_gmin = {
            "type": "line",
            "title": "Evolução dos Limites Mínimos de Vazão (GMIN) por Patamar",
            "x_axis": "Deck/Data",
            "y_axis": "GMIN (m³/s)",
            "tool_name": tool_name
        }
        
        chart_config_gmax = {
            "type": "line",
            "title": "Evolução dos Limites Máximos de Vazão (GMAX) por Patamar",
            "x_axis": "Deck/Data",
            "y_axis": "GMAX (m³/s)",
            "tool_name": tool_name
        }
        
        # Resposta final
        nome_display = nome_restricao or "?"
        final_response = f"Evolução das restrições de vazão: {nome_display} ao longo do tempo."
        
        return {
            "comparison_table": comparison_table,
            "chart_data_gmin": chart_data_gmin,
            "chart_data_gmax": chart_data_gmax,
            "visualization_type": "restricoes_vazao_hq_comparison",
            "chart_config_gmin": chart_config_gmin,
            "chart_config_gmax": chart_config_gmax,
            "deck_names": [d.display_name for d in valid_decks],
            "is_multi_deck": len(decks_data) >= 2,
            "final_response": final_response,
            "tool_name": tool_name
        }

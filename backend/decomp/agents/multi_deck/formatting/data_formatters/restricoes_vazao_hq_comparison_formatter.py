"""
Formatter de comparação para RestricoesVazaoHQTool no multi deck.
Consolida dados de múltiplos decks em uma tabela e dois gráficos (GMIN e GMAX).
"""

from typing import Dict, Any, List, Optional
from backend.decomp.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from backend.decomp.agents.multi_deck.formatting.data_formatters.dp_comparison_formatter import format_compact_label
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
        # Agrupar restrições por tipo_vazao (QTUR/QDEF)
        comparison_tables_by_type = {}  # {tipo_vazao: [rows]}
        nome_restricao = None
        
        for deck in valid_decks:
            result = deck.result
            data = result.get("data", []) or []
            
            if not data:
                # Deck sem dados - pular este deck
                continue
            
            # Agrupar restrições por tipo_vazao para este deck
            # Cada deck pode ter múltiplas restrições (QTUR e QDEF), cada uma com múltiplos estágios
            # Vamos pegar apenas um registro por tipo (preferencialmente o primeiro estágio)
            restricoes_por_tipo = {}  # {tipo_vazao: row}
            
            for row in data:
                if not isinstance(row, dict):
                    continue
                
                # Obter tipo de vazão (QTUR/QDEF) ou usar "UNKNOWN" se não houver
                tipo_vazao = row.get("tipo_vazao") or "UNKNOWN"
                
                # Se já temos uma restrição deste tipo para este deck, manter a primeira (ou escolher por estágio)
                if tipo_vazao not in restricoes_por_tipo:
                    restricoes_por_tipo[tipo_vazao] = row
                else:
                    # Se já existe, preferir estágio menor (ou manter a primeira)
                    estagio_atual = row.get("estagio")
                    estagio_existente = restricoes_por_tipo[tipo_vazao].get("estagio")
                    if estagio_atual is not None and (estagio_existente is None or estagio_atual < estagio_existente):
                        restricoes_por_tipo[tipo_vazao] = row
            
            # Processar cada tipo de restrição encontrado para este deck
            for tipo_vazao, row in restricoes_por_tipo.items():
                tipo_vazao_descricao = row.get("tipo_vazao_descricao") or tipo_vazao
                
                # Inicializar lista para este tipo se não existir
                if tipo_vazao not in comparison_tables_by_type:
                    comparison_tables_by_type[tipo_vazao] = []
                
                # Extrair nome da restrição/usina (usar do primeiro registro válido)
                if nome_restricao is None:
                    nome_restricao = (
                        row.get("nome_usina") or
                        row.get("Nome") or
                        row.get("nome") or
                        "?"
                    )
                    # Se for restrição conjunta, pode ter formato especial
                    if "usinas_envolvidas" in row:
                        usinas_env = row.get("usinas_envolvidas", "")
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
                    row.get("GMIN P1") or 
                    row.get("limite_inferior_1") or
                    row.get("limites_inferiores_1")
                )
                gmin_p2 = _to_num(
                    row.get("GMIN P2") or 
                    row.get("limite_inferior_2") or
                    row.get("limites_inferiores_2")
                )
                gmin_p3 = _to_num(
                    row.get("GMIN P3") or 
                    row.get("limite_inferior_3") or
                    row.get("limites_inferiores_3")
                )
                
                gmax_p1 = _to_num(
                    row.get("GMAX P1") or 
                    row.get("limite_superior_1") or
                    row.get("limites_superiores_1")
                )
                gmax_p2 = _to_num(
                    row.get("GMAX P2") or 
                    row.get("limite_superior_2") or
                    row.get("limites_superiores_2")
                )
                gmax_p3 = _to_num(
                    row.get("GMAX P3") or 
                    row.get("limite_superior_3") or
                    row.get("limites_superiores_3")
                )
                
                # Converter None para 0 para exibição (ou manter None se preferir "-")
                gmin_p1 = gmin_p1 if gmin_p1 is not None else 0
                gmin_p2 = gmin_p2 if gmin_p2 is not None else 0
                gmin_p3 = gmin_p3 if gmin_p3 is not None else 0
                gmax_p1 = gmax_p1 if gmax_p1 is not None else 0
                gmax_p2 = gmax_p2 if gmax_p2 is not None else 0
                gmax_p3 = gmax_p3 if gmax_p3 is not None else 0
                
                # Criar nome completo incluindo tipo de vazão
                nome_completo = f"{nome_restricao or '?'} ({tipo_vazao_descricao})"
                
                comparison_tables_by_type[tipo_vazao].append({
                    "deck": deck.name,
                    "display_name": deck.display_name,
                    "Nome": nome_completo,
                    "Tipo": tipo_vazao,
                    "TipoDescricao": tipo_vazao_descricao,
                    "GMIN P1": gmin_p1,
                    "GMIN P2": gmin_p2,
                    "GMIN P3": gmin_p3,
                    "GMAX P1": gmax_p1,
                    "GMAX P2": gmax_p2,
                    "GMAX P3": gmax_p3,
                })
        
        # Consolidar todas as tabelas em uma única tabela (com todas as restrições)
        comparison_table = []
        for tipo_vazao in sorted(comparison_tables_by_type.keys()):
            comparison_table.extend(comparison_tables_by_type[tipo_vazao])
        
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
        
        # Construir gráficos separados por tipo de vazão
        # Agrupar dados por tipo para criar séries separadas nos gráficos
        charts_by_type = {}
        
        for tipo_vazao, rows in comparison_tables_by_type.items():
            if not rows:
                continue
                
            # Construir labels compactas para os gráficos deste tipo
            chart_labels = [
                format_compact_label(row.get("display_name", ""), row.get("deck", ""))
                for row in rows
            ]
            
            # Construir gráfico GMIN para este tipo (3 séries: P1, P2, P3)
            chart_data_gmin = {
                "labels": chart_labels,
                "datasets": [
                    {
                        "label": f"GMIN P1 ({tipo_vazao})",
                        "data": [row.get("GMIN P1") for row in rows],
                        "borderColor": "rgb(59, 130, 246)",  # blue-500
                        "backgroundColor": "rgba(59, 130, 246, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    },
                    {
                        "label": f"GMIN P2 ({tipo_vazao})",
                        "data": [row.get("GMIN P2") for row in rows],
                        "borderColor": "rgb(16, 185, 129)",  # emerald-500
                        "backgroundColor": "rgba(16, 185, 129, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    },
                    {
                        "label": f"GMIN P3 ({tipo_vazao})",
                        "data": [row.get("GMIN P3") for row in rows],
                        "borderColor": "rgb(245, 158, 11)",  # amber-500
                        "backgroundColor": "rgba(245, 158, 11, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    }
                ]
            }
            
            # Construir gráfico GMAX para este tipo (3 séries: P1, P2, P3)
            chart_data_gmax = {
                "labels": chart_labels,
                "datasets": [
                    {
                        "label": f"GMAX P1 ({tipo_vazao})",
                        "data": [row.get("GMAX P1") for row in rows],
                        "borderColor": "rgb(239, 68, 68)",  # red-500
                        "backgroundColor": "rgba(239, 68, 68, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    },
                    {
                        "label": f"GMAX P2 ({tipo_vazao})",
                        "data": [row.get("GMAX P2") for row in rows],
                        "borderColor": "rgb(234, 179, 8)",  # yellow-500
                        "backgroundColor": "rgba(234, 179, 8, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    },
                    {
                        "label": f"GMAX P3 ({tipo_vazao})",
                        "data": [row.get("GMAX P3") for row in rows],
                        "borderColor": "rgb(139, 92, 246)",  # violet-500
                        "backgroundColor": "rgba(139, 92, 246, 0.1)",
                        "fill": False,
                        "tension": 0.4
                    }
                ]
            }
            
            charts_by_type[tipo_vazao] = {
                "gmin": chart_data_gmin,
                "gmax": chart_data_gmax
            }
        
        # Consolidar gráficos: combinar todos os tipos em um único gráfico
        # Para GMIN: combinar todas as séries de todos os tipos
        chart_data_gmin = None
        chart_data_gmax = None
        
        if charts_by_type:
            all_gmin_datasets = []
            all_gmax_datasets = []
            
            # Coletar labels de todos os tipos (devem ser os mesmos, mas vamos garantir)
            all_labels_list = []
            for tipo_vazao, charts in charts_by_type.items():
                all_gmin_datasets.extend(charts["gmin"]["datasets"])
                all_gmax_datasets.extend(charts["gmax"]["datasets"])
                # Labels devem ser os mesmos para todos os tipos (mesmos decks)
                if not all_labels_list:
                    all_labels_list = charts["gmin"]["labels"]
            
            # Se não há labels, criar a partir dos decks válidos
            if not all_labels_list:
                all_labels_list = [
                    format_compact_label(d.display_name, d.name)
                    for d in valid_decks
                ]
            
            # Construir gráfico GMIN consolidado (todas as séries de todos os tipos)
            if all_gmin_datasets and all_labels_list:
                chart_data_gmin = {
                    "labels": all_labels_list,
                    "datasets": all_gmin_datasets
                }
            
            # Construir gráfico GMAX consolidado (todas as séries de todos os tipos)
            if all_gmax_datasets and all_labels_list:
                chart_data_gmax = {
                    "labels": all_labels_list,
                    "datasets": all_gmax_datasets
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
        tipos_encontrados = sorted(comparison_tables_by_type.keys())
        if len(tipos_encontrados) > 1:
            tipos_str = " e ".join([f"{'QTUR' if t == 'QTUR' else 'QDEF' if t == 'QDEF' else t}" for t in tipos_encontrados])
            final_response = f"Evolução das restrições de vazão ({tipos_str}): {nome_display} ao longo do tempo."
        else:
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

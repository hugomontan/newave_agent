"""
Formatter de comparação para gerações GNL (Registro GL) no multi deck DECOMP.
Formata como tabela agregada por deck e 3 gráficos (um por patamar) com múltiplas séries.
"""
from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.config import safe_print


class GLComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de gerações GNL (Registro GL) entre múltiplos decks DECOMP.
    
    Formata como:
    - Tabela com uma linha por deck, mostrando totais agregados por patamar
    - 3 gráficos separados (um por patamar), cada um com múltiplas séries (uma linha por deck)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de GL."""
        # Verificar por nome da tool PRIMEIRO (prioridade)
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "GLGeracoesGNLTool" or 
            tool_name == "GLMultiDeckTool" or
            ("gl" in tool_name_lower and "gnl" in tool_name_lower) or
            (tool_name_lower.startswith("gl") and "geracoes" in tool_name_lower)
        ):
            return True
        
        # Verificar pela estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            # Verificar se tem dados de GL (data com geracao_patamar_1, geracao_patamar_2, etc)
            if "data" in result_structure:
                data = result_structure.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0] if isinstance(data[0], dict) else {}
                    if "geracao_patamar_1" in first_record or "geracao_pat_1" in first_record:
                        return True
            # Verificar se é um resultado de deck que contém dados de GL
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        result = first_deck.get("result", {})
                        data = result.get("data", [])
                        if isinstance(data, list) and len(data) > 0:
                            first_record = data[0] if isinstance(data[0], dict) else {}
                            if "geracao_patamar_1" in first_record or "geracao_pat_1" in first_record:
                                return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 85
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de gerações GNL entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            
        Returns:
            Dict com dados formatados para visualização (tabela + 3 gráficos)
        """
        # Verificar se há dados válidos
        valid_decks = [d for d in decks_data if d.has_data]
        safe_print(f"[GL COMPARISON FORMATTER] Total decks: {len(decks_data)}, Valid decks: {len(valid_decks)}")
        
        if not valid_decks:
            safe_print(f"[GL COMPARISON FORMATTER] ⚠️ Nenhum deck válido encontrado")
            for i, deck in enumerate(decks_data):
                safe_print(f"[GL COMPARISON FORMATTER] Deck {i}: {deck.name}, success={deck.success}, has_data={deck.has_data}, result_keys={list(deck.result.keys()) if deck.result else []}")
            return {
                "comparison_table": [],
                "charts_by_patamar": {},
                "visualization_type": "gl_comparison",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) > 2,
                "final_response": "Nenhum dado válido encontrado para comparação.",
                "tool_name": tool_name
            }
        
        # Extrair informações da usina
        usina_info = None
        for deck in valid_decks:
            if deck.result:
                # Tentar obter do resultado do deck
                if "usina" in deck.result:
                    usina_info = deck.result.get("usina", {})
                # Ou tentar obter do resultado da tool multi-deck (que vem no nível superior)
                elif "codigo_usina" in deck.result:
                    usina_info = {
                        "codigo": deck.result.get("codigo_usina"),
                        "nome": deck.result.get("nome_usina")
                    }
                if usina_info:
                    break
        
        # Se não encontrou no deck, tentar buscar no primeiro resultado válido
        if not usina_info and valid_decks:
            first_result = valid_decks[0].result
            if "codigo_usina" in first_result:
                usina_info = {
                    "codigo": first_result.get("codigo_usina"),
                    "nome": first_result.get("nome_usina")
                }
        
        nome_usina = usina_info.get("nome", "Usina Desconhecida") if usina_info else "Usina Desconhecida"
        codigo_usina = usina_info.get("codigo", "N/A") if usina_info else "N/A"
        
        # Criar tabela comparativa: uma linha por deck com totais agregados
        comparison_table = []
        
        # Ordenar decks por data (se disponível) ou por nome
        sorted_decks = sorted(
            valid_decks,
            key=lambda d: (
                d.result.get("date") or "9999-99-99",
                d.name
            )
        )
        
        # Preparar dados para gráficos: uma série por deck
        # Estrutura: {patamar_num: {deck_name: [valores ao longo do tempo]}}
        charts_data_by_patamar = {1: {}, 2: {}, 3: {}}
        all_dates = []
        
        for deck in sorted_decks:
            result = deck.result
            data = result.get("data", [])
            
            safe_print(f"[GL COMPARISON FORMATTER] Processando deck {deck.name}: data length={len(data) if data else 0}")
            
            if not data:
                safe_print(f"[GL COMPARISON FORMATTER] ⚠️ Deck {deck.name} não tem dados (data está vazio)")
                continue
            
            # Extrair data do deck
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
                all_dates.append(date)
            
            # Agregar gerações por patamar (soma de todos os registros do deck)
            geracao_pat_1_total = sum(
                r.get("geracao_patamar_1", 0) or 0 
                for r in data 
                if isinstance(r, dict)
            )
            geracao_pat_2_total = sum(
                r.get("geracao_patamar_2", 0) or 0 
                for r in data 
                if isinstance(r, dict)
            )
            geracao_pat_3_total = sum(
                r.get("geracao_patamar_3", 0) or 0 
                for r in data 
                if isinstance(r, dict)
            )
            
            # Criar entrada na tabela
            table_row = {
                "data": date or deck.display_name,
                "deck": deck.name,
                "display_name": deck.display_name,
                "geracao_pat_1_total": round(geracao_pat_1_total, 2),
                "geracao_pat_2_total": round(geracao_pat_2_total, 2),
                "geracao_pat_3_total": round(geracao_pat_3_total, 2),
                "total_registros": len(data),
                "usina_codigo": codigo_usina,
                "usina_nome": nome_usina
            }
            comparison_table.append(table_row)
            
            # Armazenar valores para gráficos (uma série por deck)
            # Cada deck terá um valor único (total agregado) no gráfico
            charts_data_by_patamar[1][deck.name] = {
                "value": geracao_pat_1_total,
                "date": date,
                "display_name": deck.display_name
            }
            charts_data_by_patamar[2][deck.name] = {
                "value": geracao_pat_2_total,
                "date": date,
                "display_name": deck.display_name
            }
            charts_data_by_patamar[3][deck.name] = {
                "value": geracao_pat_3_total,
                "date": date,
                "display_name": deck.display_name
            }
        
        # Criar 3 gráficos (um por patamar), cada um com múltiplas séries (uma por deck)
        charts_by_patamar = {}
        
        # Ordenar datas para labels do gráfico
        sorted_dates = sorted(set(all_dates)) if all_dates else []
        
        # Cores para os decks (usar cores diferentes para cada deck)
        deck_colors = [
            "rgb(239, 68, 68)",    # red-500
            "rgb(34, 197, 94)",    # green-500
            "rgb(59, 130, 246)",   # blue-500
            "rgb(234, 179, 8)",    # yellow-500
            "rgb(168, 85, 247)",  # purple-500
            "rgb(236, 72, 153)",  # pink-500
            "rgb(20, 184, 166)",   # teal-500
            "rgb(251, 146, 60)",   # orange-500
        ]
        
        for patamar_num in [1, 2, 3]:
            patamar_nome = {1: "PESADA", 2: "MÉDIA", 3: "LEVE"}[patamar_num]
            patamar_key = f"patamar_{patamar_num}"
            
            # Criar datasets: uma série por deck
            chart_datasets = []
            deck_index = 0
            
            for deck in sorted_decks:
                deck_data = charts_data_by_patamar[patamar_num].get(deck.name)
                if not deck_data:
                    continue
                
                # Cada deck terá um único ponto no gráfico (valor total agregado)
                # Criar série com um único valor posicionado na data do deck
                dataset_data = []
                dataset_labels = []
                
                # Adicionar valor para este deck
                dataset_data.append(deck_data["value"])
                dataset_labels.append(deck_data["date"] or deck.display_name)
                
                # Preencher com None para outros decks (para alinhar no gráfico)
                # Mas na verdade, vamos criar uma série por deck com seu próprio ponto
                # Melhor abordagem: cada série tem um ponto na posição correspondente à data do deck
                
                color = deck_colors[deck_index % len(deck_colors)]
                chart_datasets.append({
                    "label": deck.display_name,
                    "data": [deck_data["value"]],  # Um único valor
                    "borderColor": color,
                    "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.1)"),
                    "tension": 0.1,
                    "pointRadius": 6,
                    "pointHoverRadius": 8
                })
                deck_index += 1
            
            # Labels do gráfico: usar datas ordenadas ou display_names
            chart_labels = [
                row.get("data") or row.get("display_name", "")
                for row in comparison_table
            ]
            
            # Ajustar datasets para terem o mesmo número de pontos que labels
            # Cada série (deck) terá valores apenas na posição correspondente ao seu deck
            # Isso permite que cada deck tenha sua própria linha no gráfico
            adjusted_datasets = []
            for dataset in chart_datasets:
                adjusted_data = [None] * len(chart_labels)
                # Encontrar a posição do deck correspondente na tabela
                deck_name_for_dataset = dataset["label"]
                for j, row in enumerate(comparison_table):
                    if row.get("display_name") == deck_name_for_dataset:
                        adjusted_data[j] = dataset["data"][0]  # Valor único do deck nesta posição
                        break
                adjusted_datasets.append({
                    **dataset,
                    "data": adjusted_data,
                    "spanGaps": True,  # Conectar pontos mesmo com gaps
                    "showLine": True   # Mostrar linha conectando os pontos
                })
            
            chart_data = {
                "labels": chart_labels,
                "datasets": adjusted_datasets
            } if chart_labels and adjusted_datasets else None
            
            charts_by_patamar[patamar_key] = {
                "patamar": patamar_nome,
                "patamar_numero": patamar_num,
                "chart_data": chart_data,
                "chart_config": {
                    "type": "line",
                    "title": f"Evolução da Geração - Patamar {patamar_num} ({patamar_nome})",
                    "x_axis": "Data/Deck",
                    "y_axis": "Geração Total (MW)",
                    "tool_name": tool_name
                }
            }
        
        # Resposta mínima
        final_response = f"Comparação de gerações GNL para {nome_usina}."
        
        return {
            "comparison_table": comparison_table,
            "charts_by_patamar": charts_by_patamar,
            "visualization_type": "gl_comparison",
            "chart_config": None,  # Não usado, cada patamar tem seu próprio chart_config
            "deck_names": [d.display_name for d in sorted_decks],
            "is_multi_deck": len(decks_data) > 2,
            "final_response": final_response,
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina
            },
            "tool_name": tool_name
        }

"""
Formatter de comparação para gerações GNL (Registro GL) no multi deck DECOMP.
Formata como tabela com série temporal completa (uma linha por registro) e 3 gráficos (um por patamar) com múltiplas séries temporais.
"""
from typing import Dict, Any, List
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.config import safe_print


class GLComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de gerações GNL (Registro GL) entre múltiplos decks DECOMP.
    
    Formata como:
    - Tabela com série temporal completa (uma linha por registro/semana, não agregada)
    - 3 gráficos separados (um por patamar), cada um com múltiplas séries temporais (uma linha por deck)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de GL."""
        safe_print(f"[GL COMPARISON FORMATTER] can_format chamado - tool_name: {tool_name}")
        safe_print(f"[GL COMPARISON FORMATTER] result_structure type: {type(result_structure)}, keys: {list(result_structure.keys()) if isinstance(result_structure, dict) else 'not a dict'}")
        
        # Verificar por nome da tool PRIMEIRO (prioridade)
        tool_name_lower = tool_name.lower() if tool_name else ""
        tool_name_match = (
            tool_name == "GLGeracoesGNLTool" or 
            tool_name == "GLMultiDeckTool" or
            ("gl" in tool_name_lower and "gnl" in tool_name_lower) or
            (tool_name_lower.startswith("gl") and "geracoes" in tool_name_lower)
        )
        
        if tool_name_match:
            safe_print(f"[GL COMPARISON FORMATTER] ✅ Match por nome da tool: {tool_name}")
            return True
        
        # Verificar pela estrutura do resultado
        if result_structure and isinstance(result_structure, dict):
            # Verificar se tem dados de GL (data com geracao_patamar_1, geracao_patamar_2, etc)
            if "data" in result_structure:
                data = result_structure.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0] if isinstance(data[0], dict) else {}
                    has_gl_fields = "geracao_patamar_1" in first_record or "geracao_pat_1" in first_record
                    if has_gl_fields:
                        safe_print(f"[GL COMPARISON FORMATTER] ✅ Match por estrutura (data com campos GL)")
                        return True
                    else:
                        safe_print(f"[GL COMPARISON FORMATTER] ⚠️ Tem 'data' mas sem campos GL. Primeiro record keys: {list(first_record.keys()) if isinstance(first_record, dict) else 'not a dict'}")
            
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
                            has_gl_fields = "geracao_patamar_1" in first_record or "geracao_pat_1" in first_record
                            if has_gl_fields:
                                safe_print(f"[GL COMPARISON FORMATTER] ✅ Match por estrutura (decks com dados GL)")
                                return True
        
        safe_print(f"[GL COMPARISON FORMATTER] ❌ Não pode formatar - tool_name: {tool_name}")
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
        
        # Criar tabela comparativa: UMA LINHA POR REGISTRO (série temporal completa)
        comparison_table = []
        
        # Ordenar decks por data (se disponível) ou por nome
        sorted_decks = sorted(
            valid_decks,
            key=lambda d: (
                d.result.get("date") or "9999-99-99",
                d.name
            )
        )
        
        # Preparar dados para gráficos: séries temporais por patamar para cada deck
        # Estrutura: {patamar_num: {deck_name: {labels: [datas], values: [valores]}}}
        charts_data_by_patamar = {1: {}, 2: {}, 3: {}}
        all_week_labels = set()  # Conjunto de todas as semanas únicas de todos os decks
        
        for deck in sorted_decks:
            result = deck.result
            data = result.get("data", [])
            
            safe_print(f"[GL COMPARISON FORMATTER] Processando deck {deck.name}: data length={len(data) if data else 0}")
            
            if not data:
                safe_print(f"[GL COMPARISON FORMATTER] ⚠️ Deck {deck.name} não tem dados (data está vazio)")
                continue
            
            # DEBUG: Verificar estrutura do primeiro registro
            if data and len(data) > 0:
                first_record = data[0] if isinstance(data[0], dict) else {}
                safe_print(f"[GL COMPARISON FORMATTER] 🔍 DEBUG - Estrutura do primeiro registro do deck {deck.name}:")
                safe_print(f"[GL COMPARISON FORMATTER]   - Record type: {type(first_record)}")
                safe_print(f"[GL COMPARISON FORMATTER]   - Record keys: {list(first_record.keys()) if isinstance(first_record, dict) else 'not a dict'}")
                if isinstance(first_record, dict):
                    safe_print(f"[GL COMPARISON FORMATTER]   - Tem 'geracao_patamar_1'? {('geracao_patamar_1' in first_record)}")
                    safe_print(f"[GL COMPARISON FORMATTER]   - Valor 'geracao_patamar_1': {first_record.get('geracao_patamar_1')} (type: {type(first_record.get('geracao_patamar_1'))})")
            
            # Ordenar registros por semana/estagio/data_inicio
            sorted_data = sorted(
                data,
                key=lambda r: (
                    r.get("estagio", 999),
                    r.get("semana", 999),
                    r.get("data_inicio", "") or r.get("data_inicio_raw", "")
                )
            )
            
            # Extrair vetores de valores por patamar para este deck (para gráficos)
            pat_1_values = []
            pat_2_values = []
            pat_3_values = []
            week_labels = []
            
            # Processar cada registro e criar UMA LINHA NA TABELA POR REGISTRO
            for idx, record in enumerate(sorted_data):
                if not isinstance(record, dict):
                    continue
                
                # DEBUG: Log do primeiro registro para diagnóstico
                if idx == 0:
                    safe_print(f"[GL COMPARISON FORMATTER] 🔍 DEBUG - Primeiro registro do deck {deck.name}:")
                    safe_print(f"[GL COMPARISON FORMATTER]   - Record keys: {list(record.keys())}")
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_patamar_1 (raw): {record.get('geracao_patamar_1')} (type: {type(record.get('geracao_patamar_1'))})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_patamar_2 (raw): {record.get('geracao_patamar_2')} (type: {type(record.get('geracao_patamar_2'))})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_patamar_3 (raw): {record.get('geracao_patamar_3')} (type: {type(record.get('geracao_patamar_3'))})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - data_inicio: {record.get('data_inicio')}")
                    safe_print(f"[GL COMPARISON FORMATTER]   - estagio: {record.get('estagio')}")
                
                # Extrair data_inicio (formato DD/MM/YYYY ou DDMMYYYY)
                data_inicio = record.get("data_inicio") or record.get("data_inicio_raw", "")
                semana = record.get("semana") or record.get("estagio", "")
                estagio = record.get("estagio")
                
                # Converter data para formatos: YYYY-MM-DD (ordenação) e DD/MM/YYYY (exibição)
                data_formatted = ""  # Para ordenação (YYYY-MM-DD)
                data_display = ""    # Para exibição (DD/MM/YYYY)
                
                if data_inicio:
                    # Se está no formato DDMMYYYY, converter
                    if len(data_inicio) == 8 and "/" not in data_inicio:
                        # DDMMYYYY -> YYYY-MM-DD e DD/MM/YYYY
                        data_formatted = f"{data_inicio[4:]}-{data_inicio[2:4]}-{data_inicio[:2]}"
                        data_display = f"{data_inicio[:2]}/{data_inicio[2:4]}/{data_inicio[4:]}"
                    elif "/" in data_inicio and len(data_inicio) == 10:
                        # DD/MM/YYYY -> YYYY-MM-DD
                        parts = data_inicio.split("/")
                        if len(parts) == 3:
                            data_formatted = f"{parts[2]}-{parts[1]}-{parts[0]}"
                            data_display = data_inicio
                        else:
                            data_formatted = data_inicio
                            data_display = data_inicio
                    else:
                        data_formatted = data_inicio
                        data_display = data_inicio
                elif semana:
                    # Usar semana como data (para ordenação)
                    data_formatted = f"Semana {semana}"
                    data_display = f"Semana {semana}"
                else:
                    data_formatted = f"Registro {len(week_labels) + 1}"
                    data_display = data_formatted
                
                # Criar label para gráfico (usar data_display)
                label = data_display
                week_labels.append(label)
                all_week_labels.add(label)
                
                # ✅ CORRIGIDO: Extrair valores por patamar preservando None quando não houver valor
                # Não usar "or 0" para preservar None (que será exibido como "-" no frontend)
                geracao_pat_1_raw = record.get("geracao_patamar_1")
                geracao_pat_2_raw = record.get("geracao_patamar_2")
                geracao_pat_3_raw = record.get("geracao_patamar_3")
                
                # Converter para float apenas se não for None, caso contrário preservar None
                def safe_float(value):
                    """Converte para float se possível, preserva None se não houver valor."""
                    if value is None:
                        return None
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
                
                geracao_pat_1 = safe_float(geracao_pat_1_raw)
                geracao_pat_2 = safe_float(geracao_pat_2_raw)
                geracao_pat_3 = safe_float(geracao_pat_3_raw)
                
                # DEBUG: Log dos valores processados (apenas primeiro registro)
                if idx == 0:
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_pat_1 (processed): {geracao_pat_1} (type: {type(geracao_pat_1)})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_pat_2 (processed): {geracao_pat_2} (type: {type(geracao_pat_2)})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - geracao_pat_3 (processed): {geracao_pat_3} (type: {type(geracao_pat_3)})")
                
                # Armazenar valores para gráficos (usar 0 se None para gráficos)
                pat_1_values.append(geracao_pat_1 if geracao_pat_1 is not None else 0)
                pat_2_values.append(geracao_pat_2 if geracao_pat_2 is not None else 0)
                pat_3_values.append(geracao_pat_3 if geracao_pat_3 is not None else 0)
                
                # ✅ CRIAR UMA LINHA NA TABELA PARA ESTE REGISTRO (série temporal)
                # Round apenas se não for None, caso contrário preservar None
                table_row = {
                    "data": data_formatted,  # Data formatada para ordenação (YYYY-MM-DD)
                    "data_display": data_display,  # Data para exibição (DD/MM/YYYY)
                    "deck": deck.name,
                    "display_name": deck.display_name,
                    "semana": semana or estagio or "",
                    "estagio": estagio or "",
                    "geracao_pat_1": round(geracao_pat_1, 2) if geracao_pat_1 is not None else None,  # ✅ Preservar None
                    "geracao_pat_2": round(geracao_pat_2, 2) if geracao_pat_2 is not None else None,  # ✅ Preservar None
                    "geracao_pat_3": round(geracao_pat_3, 2) if geracao_pat_3 is not None else None,  # ✅ Preservar None
                    "usina_codigo": codigo_usina,
                    "usina_nome": nome_usina
                }
                
                # DEBUG: Log da linha da tabela criada (apenas primeiro registro)
                if idx == 0:
                    safe_print(f"[GL COMPARISON FORMATTER]   - table_row geracao_pat_1: {table_row.get('geracao_pat_1')} (type: {type(table_row.get('geracao_pat_1'))})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - table_row geracao_pat_2: {table_row.get('geracao_pat_2')} (type: {type(table_row.get('geracao_pat_2'))})")
                    safe_print(f"[GL COMPARISON FORMATTER]   - table_row geracao_pat_3: {table_row.get('geracao_pat_3')} (type: {type(table_row.get('geracao_pat_3'))})")
                
                comparison_table.append(table_row)
            
            safe_print(f"[GL COMPARISON FORMATTER] ✅ PROCESSAMENTO CONCLUÍDO: {len(comparison_table)} linhas criadas para deck {deck.name}")
            
            # Armazenar séries temporais por patamar para este deck (para gráficos)
            charts_data_by_patamar[1][deck.name] = {
                "labels": week_labels,
                "values": pat_1_values,
                "display_name": deck.display_name
            }
            charts_data_by_patamar[2][deck.name] = {
                "labels": week_labels,
                "values": pat_2_values,
                "display_name": deck.display_name
            }
            charts_data_by_patamar[3][deck.name] = {
                "labels": week_labels,
                "values": pat_3_values,
                "display_name": deck.display_name
            }
        
        # Ordenar tabela por data e deck (para mostrar série temporal ordenada)
        comparison_table.sort(key=lambda r: (
            r.get("data", ""),  # Ordenar por data primeiro (YYYY-MM-DD)
            r.get("display_name", "")  # Depois por deck
        ))
        
        # Criar 3 gráficos (um por patamar), cada um com múltiplas séries temporais (uma por deck)
        charts_by_patamar = {}
        
        # Criar conjunto unificado de labels (todas as semanas de todos os decks)
        # Ordenar labels: tentar ordenar por data, caso contrário manter ordem original
        def sort_label(label):
            """Tenta extrair data do label para ordenação."""
            # Formato YYYY-MM-DD (prioridade - formato de ordenação)
            if "-" in label and len(label) == 10:
                parts = label.split("-")
                if len(parts) == 3:
                    try:
                        return (int(parts[0]), int(parts[1]), int(parts[2]))  # YYYY, MM, DD
                    except:
                        pass
            # Formato DD/MM/YYYY
            if "/" in label and len(label) == 10:
                parts = label.split("/")
                if len(parts) == 3:
                    try:
                        return (int(parts[2]), int(parts[1]), int(parts[0]))  # YYYY, MM, DD
                    except:
                        pass
            # Formato "Semana N"
            if "Semana" in label:
                try:
                    num = int(label.split()[-1])
                    return (0, 0, num)  # Ordenar por número da semana
                except:
                    pass
            return (9999, 9999, 9999)  # Manter no final
        
        sorted_all_labels = sorted(all_week_labels, key=sort_label)
        
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
            
            # Criar datasets: uma série temporal por deck
            chart_datasets = []
            deck_index = 0
            
            for deck in sorted_decks:
                deck_timeseries = charts_data_by_patamar[patamar_num].get(deck.name)
                if not deck_timeseries or not deck_timeseries.get("values"):
                    continue
                
                # Criar mapeamento de label para valor para este deck
                deck_label_to_value = dict(zip(
                    deck_timeseries["labels"],
                    deck_timeseries["values"]
                ))
                
                # Criar vetor de valores alinhado com labels unificados
                # Se o label existe neste deck, usar o valor; caso contrário, None
                aligned_values = [
                    deck_label_to_value.get(label, None)
                    for label in sorted_all_labels
                ]
                
                color = deck_colors[deck_index % len(deck_colors)]
                chart_datasets.append({
                    "label": deck.display_name,
                    "data": aligned_values,  # Vetor de valores alinhado com labels unificados
                    "borderColor": color,
                    "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.1)"),
                    "tension": 0.1,
                    "pointRadius": 4,
                    "pointHoverRadius": 6,
                    "spanGaps": False,  # Não conectar pontos com gaps (None)
                    "showLine": True   # Mostrar linha conectando os pontos
                })
                deck_index += 1
            
            chart_data = {
                "labels": sorted_all_labels,
                "datasets": chart_datasets
            } if sorted_all_labels and chart_datasets else None
            
            charts_by_patamar[patamar_key] = {
                "patamar": patamar_nome,
                "patamar_numero": patamar_num,
                "chart_data": chart_data,
                "chart_config": {
                    "type": "line",
                    "title": f"Geração GNL - Patamar {patamar_num} ({patamar_nome}) - Série Temporal",
                    "x_axis": "Data Início (Semana)",
                    "y_axis": "Geração (MW)",
                    "tool_name": tool_name
                }
            }
        
        # Resposta mínima
        final_response = f"Comparação de gerações GNL para {nome_usina}."
        
        safe_print(f"[GL COMPARISON FORMATTER] 🎯 RESULTADO FINAL:")
        safe_print(f"[GL COMPARISON FORMATTER]   - Total de linhas na tabela: {len(comparison_table)}")
        safe_print(f"[GL COMPARISON FORMATTER]   - Total de decks processados: {len(sorted_decks)}")
        if comparison_table and len(comparison_table) > 0:
            first_row = comparison_table[0]
            safe_print(f"[GL COMPARISON FORMATTER]   - Primeira linha da tabela:")
            safe_print(f"[GL COMPARISON FORMATTER]     * Keys: {list(first_row.keys())}")
            safe_print(f"[GL COMPARISON FORMATTER]     * geracao_pat_1: {first_row.get('geracao_pat_1')} (type: {type(first_row.get('geracao_pat_1'))})")
            safe_print(f"[GL COMPARISON FORMATTER]     * geracao_pat_2: {first_row.get('geracao_pat_2')} (type: {type(first_row.get('geracao_pat_2'))})")
            safe_print(f"[GL COMPARISON FORMATTER]     * geracao_pat_3: {first_row.get('geracao_pat_3')} (type: {type(first_row.get('geracao_pat_3'))})")
        
        return {
            "comparison_table": comparison_table,
            "charts_by_patamar": charts_by_patamar,
            "visualization_type": "gl_comparison",
            "chart_config": None,  # Não usado, cada patamar tem seu próprio chart_config
            "deck_names": [d.display_name for d in sorted_decks],
            "is_multi_deck": len(decks_data) >= 2,  # >= 2 para comparação (mesmo com 2 decks é multi-deck)
            "final_response": final_response,
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina
            },
            "tool_name": tool_name
        }

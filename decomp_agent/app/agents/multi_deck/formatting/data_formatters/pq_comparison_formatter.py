"""
Formatter de comparação para gerações de pequenas usinas (PQ) no multi deck DECOMP.
Formata como timeseries de MW médio por tipo de geração.
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from decomp_agent.app.agents.multi_deck.formatting.data_formatters.dp_comparison_formatter import format_compact_label


class PQComparisonFormatter(ComparisonFormatter):
    """
    Formatter específico para comparação de gerações de pequenas usinas (PQ) entre múltiplos decks DECOMP.
    
    Formata como timeseries de MW médio por tipo de geração, mostrando:
    - Tabela com datas de cada deck + MW médio por tipo de geração
    - Gráfico de linha mostrando a evolução temporal de cada tipo
    - Segmentação importante: distingue tipos com e sem "gd" (ex: EOL vs EOLgd)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados de PQ."""
        # Verificar por nome da tool
        tool_name_lower = tool_name.lower() if tool_name else ""
        if (
            tool_name == "PQPequenasUsinasTool" or 
            tool_name == "PQMultiDeckTool" or
            "pq" in tool_name_lower or
            "pequenas usinas" in tool_name_lower
        ):
            return True
        
        # Verificar pela estrutura do resultado (se tem mw_medios com tipo)
        if result_structure and isinstance(result_structure, dict):
            if "mw_medios" in result_structure:
                # Verificar se mw_medios tem campo "tipo"
                mw_medios = result_structure.get("mw_medios", [])
                if isinstance(mw_medios, list) and len(mw_medios) > 0:
                    if isinstance(mw_medios[0], dict) and "tipo" in mw_medios[0]:
                        return True
            # Verificar se é um resultado de deck que contém dados de MW médio por tipo
            if "decks" in result_structure:
                decks = result_structure.get("decks", [])
                if isinstance(decks, list) and len(decks) > 0:
                    first_deck = decks[0]
                    if isinstance(first_deck, dict):
                        result = first_deck.get("result", {})
                        mw_medios = result.get("mw_medios", [])
                        if isinstance(mw_medios, list) and len(mw_medios) > 0:
                            if isinstance(mw_medios[0], dict) and "tipo" in mw_medios[0]:
                                return True
            # Verificar se tem "data" com registros que têm "tipo" e "mw_medio"
            if "data" in result_structure:
                data = result_structure.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0]
                    if isinstance(first_record, dict) and "tipo" in first_record and "mw_medio" in first_record:
                        return True
        
        return False
    
    def get_priority(self) -> int:
        """Prioridade muito alta para esta tool específica (maior que DP)."""
        return 15  # Maior que DP (10) para garantir que seja selecionado primeiro
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Formata comparação de gerações de pequenas usinas entre múltiplos decks.
        
        Args:
            decks_data: Lista de DeckData ordenados cronologicamente
            tool_name: Nome da tool usada
            query: Query original do usuário
            **kwargs: Pode conter tipo_filtrado e outras informações
            
        Returns:
            Dict com dados formatados para visualização (tabela + gráfico temporal por tipo)
        """
        from decomp_agent.app.config import safe_print
        
        # Extrair tipo encontrado REAL (prioridade) ou tipo filtrado (fallback)
        tipo_encontrado = kwargs.get("tipo_encontrado")  # Tipo REAL encontrado nos dados
        tipo_filtrado = kwargs.get("tipo_filtrado")  # Tipo da query
        tipo_para_exibir = tipo_encontrado or tipo_filtrado  # Usar tipo REAL se disponível
        safe_print(f"[PQ FORMATTER] Tipo para exibir: {tipo_para_exibir or 'TODOS'} (encontrado: {tipo_encontrado}, filtrado: {tipo_filtrado})")
        
        try:
            # Verificar se há dados válidos
            valid_decks = [d for d in decks_data if d.has_data]
            
            if not valid_decks:
                return {
                    "comparison_table": [],
                    "chart_data": None,
                    "visualization_type": "table_with_line_chart",
                    "deck_names": [d.display_name for d in decks_data],
                    "is_multi_deck": len(decks_data) >= 2,  # >= 2 para comparação multi-deck
                    "final_response": "Nenhum dado válido encontrado para comparação.",
                    "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name mesmo quando não há dados
                }
            
            # Extrair MW médios de todos os decks, agrupados por tipo de geração
            # Estrutura: {tipo: {deck_name: mw_medio, ...}}
            mw_medios_por_tipo = {}
            all_dates = []
            
            # Coletar todos os tipos esperados de todos os decks (para garantir que todos os decks tenham entrada)
            tipos_esperados = set()
            
            for deck in valid_decks:
                result = deck.result
                date = result.get("date")
                
                if date:
                    all_dates.append(date)
                
                # Verificar se deck não tem dados (será tratado como 0)
                sem_dados = result.get("sem_dados", False)
                data_vazio = not result.get("data") or len(result.get("data", [])) == 0
                
                # Extrair MW médios: pode estar em mw_medios ou nos dados individuais
                mw_medios = result.get("mw_medios", [])
                
                # Se não há mw_medios explícito, tentar extrair dos dados
                if not mw_medios and result.get("data"):
                    data = result.get("data", [])
                    for record in data:
                        mw_medio = record.get("mw_medio")
                        tipo = record.get("tipo")
                        nome = record.get("nome")
                        regiao = record.get("regiao")
                        
                        if tipo and mw_medio is not None:
                            tipos_esperados.add(tipo)
                            mw_medios.append({
                                "tipo": tipo,
                                "nome": nome,
                                "regiao": regiao,
                                "mw_medio": mw_medio
                            })
                
                # Se deck não tem dados, usar tipo_encontrado ou tipo_filtrado para criar entrada com 0
                if (sem_dados or data_vazio) and not mw_medios:
                    tipo_para_zero = result.get("tipo_encontrado") or result.get("filtros", {}).get("tipo_encontrado")
                    if not tipo_para_zero:
                        # Tentar obter do tipo filtrado da query
                        tipo_para_zero = result.get("filtros", {}).get("tipo")
                    
                    if tipo_para_zero:
                        tipos_esperados.add(tipo_para_zero)
                        # Criar entrada com MW médio = 0
                        mw_medios.append({
                            "tipo": tipo_para_zero,
                            "nome": None,
                            "regiao": None,
                            "mw_medio": 0.0
                        })
                
                # Processar MW médios deste deck
                for mw_data in mw_medios:
                    tipo = mw_data.get("tipo")
                    mw_medio = mw_data.get("mw_medio")
                    
                    # IMPORTANTE: Agrupar por tipo, distinguindo tipos com e sem "gd"
                    # Ex: PCH vs PCHgd, EOL vs EOLgd
                    if tipo:
                        tipos_esperados.add(tipo)
                        if tipo not in mw_medios_por_tipo:
                            mw_medios_por_tipo[tipo] = {}
                        
                        # Para cada tipo, pode haver múltiplos registros (diferentes nomes/regiões)
                        # Vamos somar ou fazer média? Por enquanto, vamos somar todos os MW médios do mesmo tipo
                        # Mas manter informação do nome para referência
                        if deck.name not in mw_medios_por_tipo[tipo]:
                            mw_medios_por_tipo[tipo][deck.name] = {
                                "mw_medio": 0.0,
                                "date": date,
                                "display_name": deck.display_name,
                                "registros": []
                            }
                        
                        # IMPORTANTE: Somar MW médios do mesmo tipo no mesmo deck
                        # Isso agrega múltiplos registros do mesmo tipo (ex: múltiplas usinas EOL)
                        # Se mw_medio é None, tratar como 0
                        mw_medio_valor = mw_medio if mw_medio is not None else 0.0
                        mw_medios_por_tipo[tipo][deck.name]["mw_medio"] += mw_medio_valor
                        mw_medios_por_tipo[tipo][deck.name]["registros"].append({
                            "nome": mw_data.get("nome"),
                            "regiao": mw_data.get("regiao")
                        })
            
            # Garantir que todos os decks tenham entrada para todos os tipos esperados (com 0 se não tiver dados)
            for tipo in tipos_esperados:
                for deck in valid_decks:
                    if deck.name not in mw_medios_por_tipo.get(tipo, {}):
                        date = deck.result.get("date")
                        mw_medios_por_tipo.setdefault(tipo, {})[deck.name] = {
                            "mw_medio": 0.0,
                            "date": date,
                            "display_name": deck.display_name,
                            "registros": []
                        }
            
            if not mw_medios_por_tipo:
                return {
                    "comparison_table": [],
                    "chart_data": None,
                    "visualization_type": "table_with_line_chart",
                    "deck_names": [d.display_name for d in decks_data],
                    "is_multi_deck": len(decks_data) >= 2,  # >= 2 para comparação multi-deck
                    "final_response": "Nenhum MW médio encontrado para comparação.",
                    "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name mesmo quando não há dados
                }
            
            # Ordenar datas
            sorted_dates = sorted(set(all_dates)) if all_dates else []
            
            # Construir tabela: uma linha por deck/data, colunas por tipo
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
                    
                    # Adicionar MW médio de cada tipo
                    for tipo in sorted(mw_medios_por_tipo.keys()):
                        tipo_data = mw_medios_por_tipo[tipo].get(deck_name)
                        
                        if tipo_data:
                            table_row[f"tipo_{tipo}"] = round(tipo_data["mw_medio"], 2)
                        else:
                            table_row[f"tipo_{tipo}"] = None
                    
                    comparison_table.append(table_row)
            
            # Construir dados do gráfico: uma série por tipo de geração
            # Usar formato compacto para labels: "JAN25 - S1"
            chart_labels = [
                format_compact_label(row.get("display_name", ""), row.get("deck", ""))
                for row in comparison_table
            ]
            chart_datasets = []
            
            # Cores para cada tipo de geração
            tipo_colors = {
                "PCH": "rgb(239, 68, 68)",      # red-500
                "PCT": "rgb(34, 197, 94)",      # green-500
                "EOL": "rgb(59, 130, 246)",     # blue-500
                "UFV": "rgb(234, 179, 8)",      # yellow-500
                "PCHgd": "rgb(239, 68, 68)",   # red-500 (mais escuro)
                "PCTgd": "rgb(34, 197, 94)",   # green-500 (mais escuro)
                "EOLgd": "rgb(59, 130, 246)",   # blue-500 (mais escuro)
                "UFVgd": "rgb(234, 179, 8)",   # yellow-500 (mais escuro)
            }
            
            # Ordenar tipos: primeiro sem "gd", depois com "gd"
            tipos_ordenados = sorted(mw_medios_por_tipo.keys(), key=lambda x: (x.endswith("gd"), x))
            
            for tipo in tipos_ordenados:
                color = tipo_colors.get(tipo, "rgb(156, 163, 175)")
                
                dataset_data = []
                for row in comparison_table:
                    mw_medio = row.get(f"tipo_{tipo}")
                    dataset_data.append(mw_medio)
                
                chart_datasets.append({
                    "label": tipo,
                    "data": dataset_data,
                    "borderColor": color,
                    "backgroundColor": color.replace("rgb", "rgba").replace(")", ", 0.1)"),
                })
            
            # Construir chart_data
            chart_data = {
                "labels": chart_labels,
                "datasets": chart_datasets
            } if chart_labels else None
            
            # Definir título baseado no tipo encontrado REAL
            if tipo_para_exibir:
                chart_title = f"Evolução do MW Médio - {tipo_para_exibir}"
            else:
                chart_title = "Evolução do MW Médio por Tipo de Geração"
            
            # Configuração do gráfico
            chart_config = {
                "type": "line",
                "title": chart_title,
                "x_axis": "Deck/Data",
                "y_axis": "MW Médio (MWmed)",
                "tool_name": tool_name,
                "tipo_encontrado": tipo_para_exibir  # IMPORTANTE: Tipo REAL encontrado nos dados
            }
            
            # Resposta mínima - incluir tipo encontrado e região se especificado
            tipos_mencoes = sorted(mw_medios_por_tipo.keys())
            # Tentar obter região do primeiro deck válido
            regiao_info = ""
            if valid_decks:
                primeiro_deck = valid_decks[0]
                regiao = primeiro_deck.result.get("filtros", {}).get("regiao")
                if regiao:
                    regiao_info = f" na região '{regiao}'"
            
            if tipo_para_exibir:
                final_response = f"Comparação de geração média ponderada (MW médio) para tipo: {tipo_para_exibir}{regiao_info}."
            else:
                final_response = f"Comparação de geração média ponderada (MW médio) para tipos: {', '.join(tipos_mencoes)}{regiao_info}."
            
            return {
                "comparison_table": comparison_table,
                "chart_data": chart_data,
                "visualization_type": "table_with_line_chart",
                "chart_config": chart_config,
                "deck_names": [d.display_name for d in valid_decks],
                "is_multi_deck": len(decks_data) >= 2,  # >= 2 para comparação multi-deck
                "final_response": final_response,
                "tipos": [{"tipo": tipo} for tipo in tipos_ordenados],
                "tipo_filtrado": tipo_para_exibir,  # IMPORTANTE: Tipo REAL para o frontend
                "tipo_encontrado": tipo_para_exibir,  # IMPORTANTE: Tipo REAL encontrado nos dados
                "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name para o ComparisonRouter
            }
        except Exception as e:
            from decomp_agent.app.config import safe_print
            safe_print(f"[PQ FORMATTER] ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "deck_names": [d.display_name for d in decks_data],
                "is_multi_deck": len(decks_data) >= 2,  # >= 2 para comparação multi-deck
                "final_response": f"Erro ao formatar comparação: {str(e)}",
                "tool_name": tool_name  # IMPORTANTE: Adicionar tool_name mesmo em caso de erro
            }

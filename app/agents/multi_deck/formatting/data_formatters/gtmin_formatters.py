"""
Formatador para MudancasGeracoesTermicasTool.
Visualização: Tabela de mudanças ordenadas por magnitude.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List
from app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


def format_date_br(date_str: str) -> str:
    """
    Converte data no formato "YYYY-MM" para "Mês/YYYY" em português.
    
    Args:
        date_str: Data no formato "YYYY-MM" ou "N/A"
        
    Returns:
        Data formatada como "Mês/YYYY" (ex: "Dez/2025") ou string original se inválida
    """
    if not date_str or date_str == "N/A":
        return date_str
    
    try:
        # Mapeamento de meses
        meses = {
            "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
            "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
        }
        
        # Tentar parsear formato "YYYY-MM"
        if "-" in date_str:
            parts = date_str.split("-")
            if len(parts) == 2:
                ano = parts[0]
                mes = parts[1]
                if mes in meses:
                    return f"{meses[mes]}/{ano}"
        
        # Se não conseguir parsear, retornar original
        return date_str
    except:
        return date_str


def format_periodo_coluna(periodo_inicio: str, periodo_fim: str) -> str:
    """
    Formata período para coluna no formato "MM-YYYY até MM-YYYY".
    
    Args:
        periodo_inicio: Data no formato "YYYY-MM" ou "N/A"
        periodo_fim: Data no formato "YYYY-MM" ou "N/A"
        
    Returns:
        Período formatado como "MM-YYYY até MM-YYYY" (ex: "12-2025 até 01-2026")
    """
    if not periodo_inicio or periodo_inicio == "N/A":
        return ""
    
    try:
        # Converter "YYYY-MM" para "MM-YYYY"
        def convert_to_mm_yyyy(date_str: str) -> str:
            if not date_str or date_str == "N/A":
                return ""
            if "-" in date_str:
                parts = date_str.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = parts[1]
                    return f"{mes}-{ano}"
            return date_str
        
        inicio_formatado = convert_to_mm_yyyy(periodo_inicio)
        fim_formatado = convert_to_mm_yyyy(periodo_fim)
        
        if inicio_formatado and fim_formatado:
            return f"{inicio_formatado} até {fim_formatado}"
        elif inicio_formatado:
            return inicio_formatado
        elif fim_formatado:
            return fim_formatado
        else:
            return ""
    except:
        return ""


class MudancasGeracoesTermicasFormatter(ComparisonFormatter):
    """
    Formatador para MudancasGeracoesTermicasTool.
    Visualização: Tabela de mudanças ordenadas por magnitude, destacando variações de GTMIN.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "MudancasGeracoesTermicasTool" and (
            "comparison_table" in result_structure or
            "is_comparison" in result_structure
        )
    
    def get_priority(self) -> int:
        return 95  # Alta prioridade - muito específico
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de mudanças de GTMIN para N decks."""
        if len(decks_data) < 2:
            return {"comparison_table": [], "visualization_type": "gtmin_table"}
        
        # Verificar se o primeiro deck tem matrix_data (indica que foi usado método de matriz)
        first_result = decks_data[0].result if decks_data else {}
        if "matrix_data" in first_result:
            # Usar formatação de matriz
            return self._format_matrix_comparison(decks_data, tool_name, query)
        
        # Se há apenas 2 decks, usar método legado
        if len(decks_data) == 2:
            result = self._format_comparison_internal(
                decks_data[0].result,
                decks_data[-1].result,
                tool_name,
                query
            )
            result["deck_names"] = self.get_deck_names(decks_data)
            result["is_multi_deck"] = False
            result["visualization_type"] = "gtmin_changes_table"
            return result
        
        # Para N decks (sem matrix_data), comparar cada par consecutivo e agregar
        all_comparisons = []
        transitions = []  # Lista de transições: [(deck_0 -> deck_1), (deck_1 -> deck_2), ...]
        
        for i in range(len(decks_data) - 1):
            deck_from = decks_data[i]
            deck_to = decks_data[i + 1]
            
            transition_result = self._format_comparison_internal(
                deck_from.result,
                deck_to.result,
                tool_name,
                query
            )
            
            transition_info = {
                "from_deck": deck_from.display_name,
                "to_deck": deck_to.display_name,
                "from_index": i,
                "to_index": i + 1,
                "result": transition_result
            }
            transitions.append(transition_info)
            all_comparisons.append(transition_result)
        
        # Agregar todas as mudanças de todas as transições
        aggregated = self._aggregate_transitions(transitions, tool_name, query)
        aggregated["deck_names"] = self.get_deck_names(decks_data)
        aggregated["is_multi_deck"] = len(decks_data) > 2
        aggregated["visualization_type"] = "gtmin_changes_table"
        return aggregated
    
    def _format_comparison_internal(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de mudanças de GTMIN.
        A tool já retorna dados formatados, então apenas organizamos para visualização.
        Converte para o formato esperado pelo frontend.
        """
        # A MudancasGeracoesTermicasTool já retorna dados comparativos diretamente
        # Como a tool é executada duas vezes (uma para cada deck), ambos os resultados
        # contêm os mesmos dados completos da comparação
        # Usamos result_dec (ou result_jan, ambos são iguais)
        result_to_use = result_dec if result_dec.get("is_comparison") else result_jan
        
        if result_to_use.get("is_comparison") and "comparison_table" in result_to_use:
            raw_table = result_to_use.get("comparison_table", [])
            stats = result_to_use.get("stats", {})
            
            # Agrupar por tipo de mudança ANTES de converter
            mudancas_por_tipo = {
                "aumento": [],
                "queda": [],
                "remocao": [],
                "novo": []
            }
            
            for row in raw_table:
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                # Mapear tipos antigos para novos se necessário
                tipo_mapeado = {
                    "alterado": "aumento",  # Fallback - será recalculado
                    "novo_registro": "novo",
                    "removido": "remocao",
                    "novo_valor": "novo",
                    "valor_removido": "remocao"
                }.get(tipo_mudanca, tipo_mudanca)
                
                if tipo_mapeado in mudancas_por_tipo:
                    mudancas_por_tipo[tipo_mapeado].append(row)
                elif tipo_mudanca in mudancas_por_tipo:
                    mudancas_por_tipo[tipo_mudanca].append(row)
            
            # Converter cada mudança para formato do frontend
            # Criar estrutura agrupada similar ao groupedByPar
            comparison_table = []
            comparison_by_type = {}
            
            # Processar cada tipo de mudança
            tipo_labels = {
                "aumento": "Aumentos de GTMIN",
                "queda": "Reduções de GTMIN",
                "remocao": "Exclusões de GTMIN",
                "novo": "Inclusões de GTMIN"
            }
            
            for tipo_mudanca, mudancas_tipo in mudancas_por_tipo.items():
                if not mudancas_tipo:
                    continue
                
                tipo_table = []
                for row in mudancas_tipo:
                    nome_usina = row.get("nome_usina", "N/A")
                    periodo_inicio = row.get("periodo_inicio", "N/A")
                    periodo_fim = row.get("periodo_fim", "N/A")
                    
                    # Se nome_usina está vazio, "N/A" ou começa com "Usina ", tentar melhorar
                    # Nota: O mapeamento já foi feito na tool, mas se ainda veio "N/A" ou "Usina X",
                    # pode ser que o nome não esteja disponível. Vamos manter o que veio.
                    if not nome_usina or nome_usina == "N/A" or nome_usina.startswith("Usina "):
                        # Se temos código da usina, podemos tentar buscar do TERM.DAT aqui também
                        # Mas por enquanto, vamos manter o que veio da tool
                        pass
                    
                    # Formatar período para exibição separada (formato brasileiro)
                    periodo_inicio_formatado = format_date_br(periodo_inicio)
                    periodo_fim_formatado = format_date_br(periodo_fim)
                    
                    if periodo_inicio_formatado != "N/A" and periodo_fim_formatado != "N/A":
                        periodo_str = f"{periodo_inicio_formatado} a {periodo_fim_formatado}"
                    elif periodo_inicio_formatado != "N/A":
                        periodo_str = periodo_inicio_formatado
                    elif periodo_fim_formatado != "N/A":
                        periodo_str = periodo_fim_formatado
                    else:
                        periodo_str = ""
                    
                    # Formatar período para coluna separada (formato "MM-YYYY até MM-YYYY")
                    periodo_coluna = format_periodo_coluna(periodo_inicio, periodo_fim)
                    
                    # Usar apenas o nome da usina no period (coluna "Usina")
                    # O período será exibido na coluna "Período" separada
                    if nome_usina and nome_usina != "N/A" and not nome_usina.startswith("Usina "):
                        period_display = nome_usina
                    else:
                        # Se não temos nome válido, usar código ou período como fallback
                        period_display = nome_usina if nome_usina else periodo_str
                    
                    gtmin_dez = row.get("gtmin_dezembro")
                    gtmin_jan = row.get("gtmin_janeiro")
                    diferenca = row.get("diferenca")
                    
                    # Para inclusões (novo) e exclusões (remocao), não calcular diferença/variacao
                    is_inclusao_ou_exclusao = tipo_mudanca in ["novo", "remocao"]
                    
                    # Calcular diferença percentual apenas se não for inclusão/exclusão
                    difference_percent = 0.0
                    if not is_inclusao_ou_exclusao:
                        if gtmin_dez is not None and gtmin_dez != 0:
                            if diferenca is not None:
                                difference_percent = (diferenca / abs(gtmin_dez)) * 100
                        elif gtmin_jan is not None and gtmin_jan != 0:
                            if diferenca is not None:
                                difference_percent = (diferenca / abs(gtmin_jan)) * 100
                    
                    # Converter para formato esperado pelo frontend
                    # Usar padrão similar ao groupedByPar: adicionar tipo_mudanca_key para agrupamento
                    row_formatted = {
                        "field": nome_usina,  # Nome da usina como field principal
                        "classe": "GTMIN",  # Classe para identificar como GTMIN
                        "data": periodo_str,  # Período separado (formato "Dez/2025 a Jan/2026")
                        "periodo_coluna": periodo_coluna,  # Período para coluna separada (formato "12-2025 até 01-2026")
                        "period": period_display,  # Nome da usina + período para exibição na primeira coluna
                        "periodo_inicio": periodo_inicio,
                        "periodo_fim": periodo_fim,
                        "tipo_mudanca": tipo_mudanca,  # Tipo interno (aumento, queda, remocao, novo)
                        "tipo_mudanca_key": tipo_mudanca,  # Chave para agrupamento (similar a par_key)
                        "tipo_mudanca_label": tipo_labels.get(tipo_mudanca, tipo_mudanca),  # Label para exibição
                        "is_inclusao_ou_exclusao": is_inclusao_ou_exclusao,  # Flag para ocultar diferença/variação
                        "deck_1": gtmin_dez if gtmin_dez is not None else 0,
                        "deck_1_value": gtmin_dez if gtmin_dez is not None else 0,
                        "deck_2": gtmin_jan if gtmin_jan is not None else 0,
                        "deck_2_value": gtmin_jan if gtmin_jan is not None else 0,
                        "diferenca": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                        "difference": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                        "diferenca_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                        "difference_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                        "magnitude": row.get("magnitude", 0),
                        # Manter campos originais para referência
                        "nome_usina": nome_usina,
                        "gtmin_dezembro": gtmin_dez,
                        "gtmin_janeiro": gtmin_jan,
                    }
                    
                    tipo_table.append(row_formatted)
                    comparison_table.append(row_formatted)  # Também adicionar à tabela geral
                
                # Ordenar por magnitude dentro do tipo (maior primeiro)
                tipo_table.sort(key=lambda x: -abs(x.get("magnitude", 0)))
                
                # Adicionar ao agrupamento por tipo (para referência, mas o frontend usa tipo_mudanca_key)
                comparison_by_type[tipo_mudanca] = {
                    "tipo": tipo_mudanca,
                    "label": tipo_labels.get(tipo_mudanca, tipo_mudanca),
                    "rows": tipo_table
                }
            
            # Ordenar tabela geral por tipo e magnitude
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            comparison_table.sort(key=lambda x: (
                ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
                -abs(x.get("magnitude", 0))  # Maior magnitude primeiro dentro do mesmo tipo
            ))
            
            # Adicionar estatísticas por tipo
            stats_por_tipo = {
                "aumento": len(mudancas_por_tipo["aumento"]),
                "queda": len(mudancas_por_tipo["queda"]),
                "remocao": len(mudancas_por_tipo["remocao"]),
                "novo": len(mudancas_por_tipo["novo"])
            }
            stats["mudancas_por_tipo"] = stats_por_tipo
            
            return {
                "comparison_table": comparison_table,
                "comparison_by_type": comparison_by_type,  # Agrupamento por tipo para renderização em seções
                "chart_data": None,  # Sem gráfico
                "visualization_type": "gtmin_changes_table",
                "stats": stats,
                "llm_context": {
                    "total_mudancas": len(comparison_table),
                    "deck_1_name": "Dezembro 2025",
                    "deck_2_name": "Janeiro 2026",
                    "description": result_to_use.get("description", f"Análise de {len(comparison_table)} mudanças de GTMIN entre Dezembro 2025 e Janeiro 2026, ordenadas por magnitude.")
                }
            }
    
    def _aggregate_transitions(
        self,
        transitions: List[Dict],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Agrega resultados de múltiplas transições entre decks consecutivos.
        Coleta todas as mudanças de GTMIN de todas as transições.
        Deduplica mudanças idênticas que podem aparecer em múltiplas transições.
        """
        all_comparison_tables = []
        seen_keys = set()  # Para deduplicação
        all_comparison_by_type = {}
        all_stats = {
            "total_mudancas": 0,
            "mudancas_por_tipo": {
                "aumento": 0,
                "queda": 0,
                "remocao": 0,
                "novo": 0
            }
        }
        
        for transition in transitions:
            result = transition["result"]
            comparison_table = result.get("comparison_table", [])
            comparison_by_type = result.get("comparison_by_type", {})
            stats = result.get("stats", {})
            
            # Adicionar informações da transição a cada registro e deduplicar
            for row in comparison_table:
                # Criar chave única para deduplicação
                # Baseada em: usina, período, valores e tipo de mudança
                # Verificar múltiplos nomes de campos possíveis
                codigo_usina = row.get("codigo_usina") or row.get("usina_codigo")
                nome_usina = row.get("nome_usina") or row.get("usina") or row.get("field") or "N/A"
                periodo_inicio = row.get("periodo_inicio") or row.get("periodo") or "N/A"
                periodo_fim = row.get("periodo_fim") or periodo_inicio
                gtmin_dez = row.get("gtmin_dezembro") or row.get("gtmin_anterior") or row.get("deck_1") or row.get("deck_1_value")
                gtmin_jan = row.get("gtmin_janeiro") or row.get("gtmin_atual") or row.get("deck_2") or row.get("deck_2_value")
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                
                # Chave única: combinação de identificadores
                # Usar nome_usina como identificador principal (mais confiável que código)
                dedup_key = (
                    str(nome_usina).strip().upper(),  # Normalizar nome
                    str(periodo_inicio).strip(),
                    str(periodo_fim).strip(),
                    gtmin_dez,
                    gtmin_jan,
                    tipo_mudanca
                )
                
                # Se já vimos esta mudança, pular (deduplicação)
                if dedup_key in seen_keys:
                    continue
                
                seen_keys.add(dedup_key)
                
                # Adicionar informações da transição
                row["transition"] = f"{transition['from_deck']} → {transition['to_deck']}"
                row["from_deck"] = transition["from_deck"]
                row["to_deck"] = transition["to_deck"]
                
                all_comparison_tables.append(row)
            
            # Agregar comparison_by_type (também deduplicar aqui)
            for tipo, tipo_data in comparison_by_type.items():
                if tipo not in all_comparison_by_type:
                    all_comparison_by_type[tipo] = {
                        "tipo": tipo,
                        "label": tipo_data.get("label", tipo),
                        "rows": []
                    }
                
                # Deduplicar rows também
                for row in tipo_data.get("rows", []):
                    # Usar mesma lógica de deduplicação
                    nome_usina = row.get("nome_usina") or row.get("usina") or row.get("field") or "N/A"
                    periodo_inicio = row.get("periodo_inicio") or row.get("periodo") or "N/A"
                    periodo_fim = row.get("periodo_fim") or periodo_inicio
                    gtmin_dez = row.get("gtmin_dezembro") or row.get("gtmin_anterior") or row.get("deck_1") or row.get("deck_1_value")
                    gtmin_jan = row.get("gtmin_janeiro") or row.get("gtmin_atual") or row.get("deck_2") or row.get("deck_2_value")
                    
                    dedup_key = (
                        str(nome_usina).strip().upper(),  # Normalizar nome
                        str(periodo_inicio).strip(),
                        str(periodo_fim).strip(),
                        gtmin_dez,
                        gtmin_jan,
                        tipo
                    )
                    
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_comparison_by_type[tipo]["rows"].append(row)
            
            # Agregar estatísticas (usar contagem única, não somar)
            # As estatísticas serão recalculadas abaixo com base nos dados deduplicados
        
        # Recalcular estatísticas baseadas nos dados deduplicados
        all_stats["total_mudancas"] = len(all_comparison_tables)
        for row in all_comparison_tables:
            tipo = row.get("tipo_mudanca", "N/A")
            if tipo in all_stats["mudancas_por_tipo"]:
                all_stats["mudancas_por_tipo"][tipo] += 1
        
        # Reordenar tabela geral por tipo e magnitude
        ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
        all_comparison_tables.sort(key=lambda x: (
            ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
            -abs(x.get("magnitude", 0))  # Maior magnitude primeiro dentro do mesmo tipo
        ))
        
        # Reordenar rows em comparison_by_type também
        for tipo_data in all_comparison_by_type.values():
            tipo_data["rows"].sort(key=lambda x: -abs(x.get("magnitude", 0)))
        
        return {
            "comparison_table": all_comparison_tables,
            "comparison_by_type": all_comparison_by_type,
            "chart_data": None,
            "visualization_type": "gtmin_changes_table",
            "stats": all_stats,
            "llm_context": {
                "total_mudancas": len(all_comparison_tables),
                "total_transitions": len(transitions),
                "description": f"Análise histórica de {len(all_comparison_tables)} mudanças de GTMIN ao longo de {len(transitions)} transições entre decks, ordenadas por magnitude."
            }
        }
        
        # Fallback: se recebemos dois resultados separados (não deve acontecer)
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "gtmin_changes_table",
            "llm_context": {
                "note": "Dados não formatados corretamente. A MudancasGeracoesTermicasTool deve retornar dados comparativos diretamente."
            }
        }
    
    def _format_matrix_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação usando matriz para múltiplos decks.
        
        Args:
            decks_data: Lista de dados dos decks
            tool_name: Nome da tool
            query: Query do usuário
            
        Returns:
            Dicionário formatado com dados da matriz
        """
        # Extrair matrix_data do primeiro deck (todos devem ter a mesma estrutura)
        first_result = decks_data[0].result if decks_data else {}
        matrix_data = first_result.get("matrix_data", [])
        deck_names = first_result.get("deck_names", self.get_deck_names(decks_data))
        stats = first_result.get("stats", {})
        
        # Formatar dados da matriz para o frontend
        formatted_matrix = []
        
        for row in matrix_data:
            formatted_row = {
                "nome_usina": row.get("nome_usina", "N/A"),
                "codigo_usina": row.get("codigo_usina"),
                "periodo_inicio": row.get("periodo_inicio", "N/A"),
                "periodo_fim": row.get("periodo_fim", "N/A"),
                "gtmin_values": row.get("gtmin_values", {}),  # Dict[deck_name, value]
                "matrix": row.get("matrix", {})  # Dict[(deck_from, deck_to), difference]
            }
            formatted_matrix.append(formatted_row)
        
        return {
            "comparison_table": formatted_matrix,
            "matrix_data": formatted_matrix,  # Manter para compatibilidade
            "deck_names": deck_names,
            "visualization_type": "gtmin_matrix",
            "is_multi_deck": True,
            "stats": stats,
            "chart_config": {
                "type": "matrix",
                "title": f"Matriz de Comparação GTMIN - {len(deck_names)} Decks",
                "tool_name": tool_name
            },
            "llm_context": {
                "total_registros": len(formatted_matrix),
                "total_decks": len(deck_names),
                "description": f"Matriz de comparação de GTMIN entre {len(deck_names)} decks, com {len(formatted_matrix)} registros com variações."
            }
        }
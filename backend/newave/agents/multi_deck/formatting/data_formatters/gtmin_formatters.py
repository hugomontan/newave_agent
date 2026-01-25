"""
Formatador para MudancasGeracoesTermicasTool.
Visualização: Tabela de mudanças ordenadas por magnitude.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List
from backend.newave.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


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
        # Verificar também no resultado completo (pode estar em full_result)
        first_result = decks_data[0].result if decks_data else {}
        first_full_result = first_result.get("full_result", {}) if isinstance(first_result, dict) else {}
        
        # Verificar matrix_data em múltiplos lugares
        if "matrix_data" in first_result or "matrix_data" in first_full_result:
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
        
        # Para N decks (sem matrix_data), criar estrutura de matriz a partir das transições
        # Isso permite visualização multi-deck mesmo quando a tool não retorna matrix_data
        matrix_result = self._create_matrix_from_transitions(decks_data, tool_name, query)
        if matrix_result:
            return matrix_result
        
        # Fallback: se não conseguir criar matriz, usar método de agregação de transições
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
        print(f"[GTMIN_FORMATTER] [DEBUG] _format_comparison_internal chamado")
        print(f"[GTMIN_FORMATTER] [DEBUG]   result_dec.is_comparison: {result_dec.get('is_comparison') if isinstance(result_dec, dict) else 'N/A'}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   result_jan.is_comparison: {result_jan.get('is_comparison') if isinstance(result_jan, dict) else 'N/A'}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   result_dec keys: {list(result_dec.keys()) if isinstance(result_dec, dict) else 'N/A'}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   result_jan keys: {list(result_jan.keys()) if isinstance(result_jan, dict) else 'N/A'}")
        
        result_to_use = result_dec if result_dec.get("is_comparison") else result_jan
        
        if result_to_use.get("is_comparison") and "comparison_table" in result_to_use:
            raw_table = result_to_use.get("comparison_table", [])
            stats = result_to_use.get("stats", {})
            print(f"[GTMIN_FORMATTER] [DEBUG]   ✅ Encontrou comparison_table com {len(raw_table)} registros")
            if raw_table:
                print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro raw: {raw_table[0]}")
            
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
                    codigo_usina = row.get("codigo_usina")  # Preservar código da usina
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
                        "codigo_usina": codigo_usina,  # Preservar código da usina
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
        else:
            print(f"[GTMIN_FORMATTER] [DEBUG]   ⚠️ Não encontrou dados comparativos válidos")
            print(f"[GTMIN_FORMATTER] [DEBUG]   result_to_use.is_comparison: {result_to_use.get('is_comparison') if isinstance(result_to_use, dict) else 'N/A'}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   'comparison_table' in result_to_use: {'comparison_table' in result_to_use if isinstance(result_to_use, dict) else 'N/A'}")
        
        # Se não encontrou dados comparativos, retornar estrutura vazia
        return {
            "comparison_table": [],
            "comparison_by_type": {},
            "chart_data": None,
            "visualization_type": "gtmin_changes_table",
            "stats": {},
            "llm_context": {
                "total_mudancas": 0,
                "description": "Nenhuma mudança de GTMIN encontrada entre os decks."
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
    
    def _create_matrix_from_transitions(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Cria estrutura de matriz a partir de transições entre decks consecutivos.
        Usado quando há mais de 2 decks mas a tool não retornou matrix_data.
        
        Estrutura da matriz:
        - Linhas: Cada restrição de GTMIN (usina + período)
        - Colunas: Cada deck (mostrando valor de GTMIN para aquela restrição)
        
        Args:
            decks_data: Lista de dados dos decks
            tool_name: Nome da tool
            query: Query do usuário
            
        Returns:
            Dicionário formatado com dados da matriz ou None se não conseguir criar
        """
        if len(decks_data) < 3:
            return None  # Precisa de pelo menos 3 decks para matriz
        
        # Usar display_name para os decks (ex: "Fevereiro 2025")
        deck_names = self.get_deck_names(decks_data)  # Display names (ex: "Fevereiro 2025")
        
        print(f"[GTMIN_FORMATTER] [DEBUG] deck_names obtidos: {deck_names}")
        print(f"[GTMIN_FORMATTER] [DEBUG] deck_names count: {len(deck_names)}")
        print(f"[GTMIN_FORMATTER] [DEBUG] decks_data count: {len(decks_data)}")
        for i, deck in enumerate(decks_data):
            print(f"[GTMIN_FORMATTER] [DEBUG]   Deck {i}: name={deck.name}, display_name={deck.display_name}")
        
        # Coletar todos os registros únicos de todas as transições
        # Estrutura: {(nome_usina, codigo_usina, periodo_inicio, periodo_fim): {deck_name: value}}
        all_records = {}  # Dict[tuple, Dict[str, Any]]
        
        # Processar cada transição consecutiva para coletar valores de GTMIN
        for i in range(len(decks_data) - 1):
            deck_from = decks_data[i]
            deck_to = decks_data[i + 1]
            
            # Extrair comparison_table formatando comparação entre este par
            from_result = deck_from.result if isinstance(deck_from.result, dict) else {}
            to_result = deck_to.result if isinstance(deck_to.result, dict) else {}
            
            # Tentar extrair comparison_table diretamente dos resultados
            # Nota: Quando a tool é executada individualmente, cada resultado pode ter
            # comparison_table, mas pode estar vazia ou não ter os dados esperados
            comparison_table = []
            
            # Debug: verificar estrutura dos resultados
            print(f"[GTMIN_FORMATTER] [DEBUG] Processando transição {i}: {deck_from.display_name} -> {deck_to.display_name}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   from_result keys: {list(from_result.keys()) if isinstance(from_result, dict) else 'N/A'}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   to_result keys: {list(to_result.keys()) if isinstance(to_result, dict) else 'N/A'}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   from_result.is_comparison: {from_result.get('is_comparison') if isinstance(from_result, dict) else 'N/A'}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   to_result.is_comparison: {to_result.get('is_comparison') if isinstance(to_result, dict) else 'N/A'}")
            
            # Verificar se há comparison_table nos resultados
            from_table = from_result.get("comparison_table", []) if isinstance(from_result, dict) else []
            to_table = to_result.get("comparison_table", []) if isinstance(to_result, dict) else []
            print(f"[GTMIN_FORMATTER] [DEBUG]   from_result.comparison_table length: {len(from_table) if isinstance(from_table, list) else 'N/A'}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   to_result.comparison_table length: {len(to_table) if isinstance(to_table, list) else 'N/A'}")
            
            # Primeiro, tentar formatar comparação entre os dois decks
            # Isso deve criar uma comparison_table com dados comparativos
            transition_result = self._format_comparison_internal(
                from_result,
                to_result,
                tool_name,
                query
            )
            print(f"[GTMIN_FORMATTER] [DEBUG]   transition_result: {type(transition_result)}")
            if transition_result:
                comparison_table = transition_result.get("comparison_table", [])
                print(f"[GTMIN_FORMATTER] [DEBUG]   transition_result.comparison_table length: {len(comparison_table)}")
                if comparison_table:
                    print(f"[GTMIN_FORMATTER] [DEBUG]   First row sample: {comparison_table[0] if comparison_table else 'N/A'}")
            
            # Se ainda não temos dados, tentar extrair diretamente dos resultados
            # (pode acontecer se a tool foi executada em modo de comparação)
            if not comparison_table:
                if isinstance(from_table, list) and from_table:
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Usando from_result.comparison_table diretamente")
                    comparison_table = from_table
                elif isinstance(to_table, list) and to_table:
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Usando to_result.comparison_table diretamente")
                    comparison_table = to_table
            
            # Se ainda não temos dados, pular esta transição
            if not comparison_table:
                print(f"[GTMIN_FORMATTER] [DEBUG]   ⚠️ Nenhum dado encontrado para esta transição, pulando...")
                continue
            
            print(f"[GTMIN_FORMATTER] [DEBUG]   ✅ Processando {len(comparison_table)} registros desta transição")
            
            # Processar cada registro da transição
            # Usar display_name (ex: "Fevereiro 2025")
            deck_from_name = deck_from.display_name
            deck_to_name = deck_to.display_name
            
            for idx, row in enumerate(comparison_table):
                # Criar chave única para o registro (usina + período)
                nome_usina = row.get("nome_usina") or row.get("field") or "N/A"
                codigo_usina = row.get("codigo_usina")
                periodo_inicio = row.get("periodo_inicio") or "N/A"
                periodo_fim = row.get("periodo_fim") or periodo_inicio
                
                # Debug primeiro registro
                if idx == 0:
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro - campos disponíveis: {list(row.keys())}")
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro - nome_usina: {nome_usina}, codigo: {codigo_usina}")
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro - periodo_inicio: {periodo_inicio}, periodo_fim: {periodo_fim}")
                
                record_key = (
                    str(nome_usina).strip().upper(),
                    codigo_usina,
                    str(periodo_inicio).strip(),
                    str(periodo_fim).strip()
                )
                
                # Inicializar registro se não existir
                if record_key not in all_records:
                    all_records[record_key] = {
                        "nome_usina": nome_usina,
                        "codigo_usina": codigo_usina,
                        "periodo_inicio": periodo_inicio,
                        "periodo_fim": periodo_fim,
                        "gtmin_values": {},  # Dict[deck_name, value]
                        "matrix": {},  # Dict[(deck_from, deck_to), difference] - para compatibilidade
                        "magnitude": row.get("magnitude", 0)
                    }
                
                # Extrair valores de GTMIN desta transição
                # Tentar múltiplos campos possíveis
                gtmin_from = (
                    row.get("deck_1") or 
                    row.get("deck_1_value") or 
                    row.get("gtmin_dezembro") or
                    row.get("gtmin_anterior")
                )
                gtmin_to = (
                    row.get("deck_2") or 
                    row.get("deck_2_value") or 
                    row.get("gtmin_janeiro") or
                    row.get("gtmin_atual")
                )
                
                # Debug valores extraídos (primeiro registro)
                if idx == 0:
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro - gtmin_from: {gtmin_from} (deck_1={row.get('deck_1')}, deck_1_value={row.get('deck_1_value')}, gtmin_dezembro={row.get('gtmin_dezembro')})")
                    print(f"[GTMIN_FORMATTER] [DEBUG]   Primeiro registro - gtmin_to: {gtmin_to} (deck_2={row.get('deck_2')}, deck_2_value={row.get('deck_2_value')}, gtmin_janeiro={row.get('gtmin_janeiro')})")
                
                # Usar nomes YYYY-MM (já calculados acima)
                # Adicionar valores aos decks usando formato YYYY-MM
                if gtmin_from is not None and gtmin_from != 0:
                    all_records[record_key]["gtmin_values"][deck_from_name] = gtmin_from
                    if idx == 0:
                        print(f"[GTMIN_FORMATTER] [DEBUG]   ✅ Adicionado gtmin_from={gtmin_from} para {deck_from_name}")
                if gtmin_to is not None and gtmin_to != 0:
                    all_records[record_key]["gtmin_values"][deck_to_name] = gtmin_to
                    if idx == 0:
                        print(f"[GTMIN_FORMATTER] [DEBUG]   ✅ Adicionado gtmin_to={gtmin_to} para {deck_to_name}")
                
                # Calcular diferença para a matriz de diferenças (opcional)
                difference = row.get("diferenca") or row.get("difference")
                if difference is not None:
                    matrix_key = f"{deck_from_name},{deck_to_name}"
                    all_records[record_key]["matrix"][matrix_key] = difference
        
        # NÃO fazer inferência de valores - usar apenas valores coletados diretamente das transições
        # A inferência estava propagando valores incorretamente para todos os decks
        # Cada transição deve fornecer valores apenas para os dois decks envolvidos
        
        # Calcular diferenças faltantes na matriz de diferenças (para compatibilidade)
        for record_key, record in all_records.items():
            gtmin_values = record["gtmin_values"]
            matrix = record["matrix"]
            
            # Para cada par de decks, calcular diferença se não existe
            for i, deck_from in enumerate(deck_names):
                for j, deck_to in enumerate(deck_names):
                    if i == j:
                        continue
                    
                    matrix_key = f"{deck_from},{deck_to}"
                    if matrix_key not in matrix:
                        if deck_from in gtmin_values and deck_to in gtmin_values:
                            val_from = gtmin_values[deck_from]
                            val_to = gtmin_values[deck_to]
                            if val_from is not None and val_to is not None:
                                matrix[matrix_key] = val_to - val_from
        
        # Debug: verificar o que foi coletado
        print(f"[GTMIN_FORMATTER] [DEBUG] Total de registros únicos coletados: {len(all_records)}")
        if all_records:
            first_key = list(all_records.keys())[0]
            first_record = all_records[first_key]
            print(f"[GTMIN_FORMATTER] [DEBUG] Primeiro registro coletado:")
            print(f"[GTMIN_FORMATTER] [DEBUG]   nome_usina: {first_record['nome_usina']}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   periodo_inicio: {first_record['periodo_inicio']}, periodo_fim: {first_record['periodo_fim']}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   gtmin_values: {first_record['gtmin_values']}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   gtmin_values keys: {list(first_record['gtmin_values'].keys())}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   gtmin_values values: {list(first_record['gtmin_values'].values())}")
        
        # Se não coletamos nenhum registro, retornar None para usar fallback
        if not all_records:
            print(f"[GTMIN_FORMATTER] [DEBUG] ⚠️ Nenhum registro coletado, retornando None")
            return None
        
        # Função auxiliar para expandir período em meses individuais
        def expand_period(periodo_inicio: str, periodo_fim: str) -> List[str]:
            """
            Expande um período (ex: "2030-07 a 2030-10") em meses individuais.
            Retorna lista de strings no formato "YYYY-MM".
            """
            if periodo_inicio == "N/A" or not periodo_inicio:
                return []
            
            # Se período fim não especificado ou igual ao início, retornar apenas o início
            if not periodo_fim or periodo_fim == "N/A" or periodo_fim == periodo_inicio:
                return [periodo_inicio]
            
            # Parsear início e fim
            try:
                inicio_parts = periodo_inicio.split("-")
                fim_parts = periodo_fim.split("-")
                
                if len(inicio_parts) != 2 or len(fim_parts) != 2:
                    return [periodo_inicio]  # Fallback: retornar apenas início
                
                ano_inicio = int(inicio_parts[0])
                mes_inicio = int(inicio_parts[1])
                ano_fim = int(fim_parts[0])
                mes_fim = int(fim_parts[1])
                
                # Gerar lista de meses
                meses = []
                ano_atual = ano_inicio
                mes_atual = mes_inicio
                
                # Incluir todos os meses do período (inclusive o último)
                while True:
                    meses.append(f"{ano_atual}-{mes_atual:02d}")
                    
                    # Verificar se chegamos ao último mês
                    if ano_atual == ano_fim and mes_atual == mes_fim:
                        break
                    
                    # Avançar para próximo mês
                    mes_atual += 1
                    if mes_atual > 12:
                        mes_atual = 1
                        ano_atual += 1
                    
                    # Verificar se passamos do fim (segurança)
                    if ano_atual > ano_fim or (ano_atual == ano_fim and mes_atual > mes_fim):
                        break
                
                return meses
            except (ValueError, IndexError):
                # Em caso de erro, retornar apenas o início
                return [periodo_inicio]
        
        # Converter para formato esperado pelo frontend
        # Formato: cada linha é um mês individual, cada coluna é um deck
        formatted_matrix = []
        records_with_values = 0
        records_skipped = 0
        
        for record_key, record in all_records.items():
            gtmin_values = record["gtmin_values"]
            
            # Verificar se há valores (não todos None)
            valores_nao_nulos = [v for v in gtmin_values.values() if v is not None]
            if not valores_nao_nulos:
                records_skipped += 1
                continue  # Pular se não há valores
            
            records_with_values += 1
            
            # Expandir período em meses individuais
            periodo_inicio = record["periodo_inicio"]
            periodo_fim = record["periodo_fim"] or periodo_inicio
            meses = expand_period(periodo_inicio, periodo_fim)
            
            # Debug primeiro registro com valores
            if records_with_values == 1:
                print(f"[GTMIN_FORMATTER] [DEBUG] Primeiro registro com valores:")
                print(f"[GTMIN_FORMATTER] [DEBUG]   periodo_inicio: {periodo_inicio}, periodo_fim: {periodo_fim}")
                print(f"[GTMIN_FORMATTER] [DEBUG]   meses expandidos: {meses}")
                print(f"[GTMIN_FORMATTER] [DEBUG]   gtmin_values: {gtmin_values}")
            
            # Criar uma linha para cada mês
            for mes in meses:
                # Criar grupo de valores iguais para coloração (por mês)
                # IMPORTANTE: usar string como chave para compatibilidade JSON
                value_groups = {}
                for deck_name, value in gtmin_values.items():
                    if value is not None:
                        rounded_value = round(float(value), 2)
                        # Usar string como chave para garantir compatibilidade JSON
                        value_key = str(rounded_value)
                        if value_key not in value_groups:
                            value_groups[value_key] = []
                        value_groups[value_key].append(deck_name)
                
                formatted_row = {
                    "nome_usina": record["nome_usina"],
                    "codigo_usina": record.get("codigo_usina"),  # Pode ser None
                    "periodo": mes,  # Mês individual (ex: "2030-07")
                    "periodo_inicio": periodo_inicio,  # Manter período original para referência
                    "periodo_fim": periodo_fim,  # Manter período original para referência
                    "gtmin_values": gtmin_values,  # Dict[deck_name, value] - valores por deck
                    "matrix": record.get("matrix", {}),  # Matriz de diferenças (para compatibilidade)
                    "value_groups": value_groups,  # Grupos de valores iguais para coloração
                    "_magnitude": record.get("magnitude", 0),  # Manter magnitude para ordenação
                    "_sort_key": (record["nome_usina"], mes)  # Chave para ordenação
                }
                formatted_matrix.append(formatted_row)
        
        # Ordenar por nome da usina e depois por mês
        formatted_matrix.sort(key=lambda x: x.get("_sort_key", ("", "")))
        
        # Remover campos auxiliares antes de retornar
        for row in formatted_matrix:
            row.pop("_magnitude", None)
            row.pop("_sort_key", None)
        
        # Debug final
        print(f"[GTMIN_FORMATTER] [DEBUG] Resumo final:")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Registros coletados: {len(all_records)}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Registros com valores: {records_with_values}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Registros pulados (sem valores): {records_skipped}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Linhas na matriz final: {len(formatted_matrix)}")
        if formatted_matrix:
            first_row = formatted_matrix[0]
            print(f"[GTMIN_FORMATTER] [DEBUG]   Primeira linha da matriz:")
            print(f"[GTMIN_FORMATTER] [DEBUG]     periodo: {first_row.get('periodo')}")
            print(f"[GTMIN_FORMATTER] [DEBUG]     nome_usina: {first_row.get('nome_usina')}")
            print(f"[GTMIN_FORMATTER] [DEBUG]     gtmin_values: {first_row.get('gtmin_values')}")
            print(f"[GTMIN_FORMATTER] [DEBUG]     gtmin_values keys: {list(first_row.get('gtmin_values', {}).keys())}")
            print(f"[GTMIN_FORMATTER] [DEBUG]     gtmin_values values: {list(first_row.get('gtmin_values', {}).values())}")
        
        # Calcular estatísticas
        stats = {
            "total_mudancas": len(formatted_matrix),
            "mudancas_por_tipo": {
                "aumento": 0,
                "queda": 0,
                "remocao": 0,
                "novo": 0
            }
        }
        
        for record_key, record in all_records.items():
            tipo = record.get("tipo_mudanca", "N/A")
            if tipo in stats["mudancas_por_tipo"]:
                stats["mudancas_por_tipo"][tipo] += 1
        
        # Garantir que todos os deck_names estão presentes em gtmin_values de cada linha
        # Preencher com None se não existir valor para aquele deck
        for row in formatted_matrix:
            gtmin_values = row.get("gtmin_values", {})
            # Garantir que todas as chaves de deck_names existem em gtmin_values
            for deck_name in deck_names:
                if deck_name not in gtmin_values:
                    gtmin_values[deck_name] = None
        
        # Debug: verificar consistência
        print(f"[GTMIN_FORMATTER] [DEBUG] Verificando consistência de deck_names:")
        print(f"[GTMIN_FORMATTER] [DEBUG]   deck_names: {deck_names}")
        if formatted_matrix:
            first_row = formatted_matrix[0]
            first_gtmin_values = first_row.get("gtmin_values", {})
            print(f"[GTMIN_FORMATTER] [DEBUG]   Primeira linha gtmin_values keys: {list(first_gtmin_values.keys())}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   Todas as chaves estão em deck_names? {all(k in deck_names for k in first_gtmin_values.keys())}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   Todos os deck_names estão em gtmin_values? {all(dn in first_gtmin_values for dn in deck_names)}")
        
        # Transpor matriz: linhas = (deck, usina), colunas = meses
        # Coletar TODOS os meses únicos de TODOS os períodos e garantir que sejam consecutivos
        from collections import defaultdict
        
        # Estrutura: {(nome_usina, periodo): {deck_name: value}}
        usina_mes_values = defaultdict(dict)
        meses_unicos = set()
        usinas_unicas = set()
        
        # Primeiro, coletar TODOS os meses de TODOS os períodos
        for record_key, record in all_records.items():
            periodo_inicio = record["periodo_inicio"]
            periodo_fim = record["periodo_fim"] or periodo_inicio
            meses_expandidos = expand_period(periodo_inicio, periodo_fim)
            meses_unicos.update(meses_expandidos)
            usinas_unicas.add(record["nome_usina"])
        
        # Agora coletar valores por (usina, mês) usando deck_names (display_name)
        for matrix_row in formatted_matrix:
            nome_usina = matrix_row.get("nome_usina", "N/A")
            periodo = matrix_row.get("periodo", "N/A")  # Mês no formato YYYY-MM (ex: "2026-07")
            gtmin_values = matrix_row.get("gtmin_values", {})
            
            if periodo != "N/A":
                # Armazenar valores por deck usando display_name
                for deck_name, value in gtmin_values.items():
                    if value is not None:
                        usina_mes_values[(nome_usina, periodo)][deck_name] = value
        
        # Garantir que todos os meses sejam consecutivos (preencher gaps)
        # Encontrar o primeiro e último mês
        if meses_unicos:
            meses_lista = sorted(meses_unicos)
            primeiro_mes = meses_lista[0]
            ultimo_mes = meses_lista[-1]
            
            # Parsear primeiro e último mês
            def parse_month(month_str: str) -> tuple:
                """Retorna (ano, mes) de uma string YYYY-MM"""
                try:
                    parts = month_str.split("-")
                    if len(parts) == 2:
                        return (int(parts[0]), int(parts[1]))
                except:
                    pass
                return (None, None)
            
            def generate_all_months(start: str, end: str) -> List[str]:
                """Gera todos os meses consecutivos entre start e end (inclusive)"""
                start_year, start_month = parse_month(start)
                end_year, end_month = parse_month(end)
                
                if start_year is None or start_month is None or end_year is None or end_month is None:
                    return sorted(meses_unicos)
                
                meses_completos = []
                ano_atual = start_year
                mes_atual = start_month
                
                while True:
                    meses_completos.append(f"{ano_atual}-{mes_atual:02d}")
                    
                    if ano_atual == end_year and mes_atual == end_month:
                        break
                    
                    mes_atual += 1
                    if mes_atual > 12:
                        mes_atual = 1
                        ano_atual += 1
                    
                    # Segurança: evitar loop infinito
                    if ano_atual > end_year + 10:
                        break
                
                return meses_completos
            
            # Gerar todos os meses consecutivos
            meses_ordenados = generate_all_months(primeiro_mes, ultimo_mes)
            print(f"[GTMIN_FORMATTER] [DEBUG] Meses coletados: {len(meses_unicos)} únicos")
            print(f"[GTMIN_FORMATTER] [DEBUG] Primeiro mês: {primeiro_mes}, Último mês: {ultimo_mes}")
            print(f"[GTMIN_FORMATTER] [DEBUG] Meses consecutivos gerados: {len(meses_ordenados)} meses")
            print(f"[GTMIN_FORMATTER] [DEBUG] Primeiros 5 meses: {meses_ordenados[:5]}")
            print(f"[GTMIN_FORMATTER] [DEBUG] Últimos 5 meses: {meses_ordenados[-5:]}")
        else:
            meses_ordenados = sorted(meses_unicos)
        
        usinas_ordenadas = sorted(usinas_unicas)
        
        # Criar comparison_table transposta: cada linha = (deck, usina), cada coluna = mês
        comparison_table = []
        TOLERANCE = 0.01  # Tolerância para comparação de float
        
        for deck_idx, deck_name in enumerate(deck_names):
            for nome_usina in usinas_ordenadas:
                # Verificar se há valores para esta combinação (deck, usina)
                tem_valores = False
                valores_por_mes = {}
                
                # Coletar valores para TODOS os meses consecutivos (mesmo que None)
                for periodo in meses_ordenados:
                    key = (nome_usina, periodo)
                    value = usina_mes_values.get(key, {}).get(deck_name)
                    valores_por_mes[periodo] = value
                    if value is not None:
                        tem_valores = True
                
                # Só criar linha se houver pelo menos um valor
                if tem_valores:
                    table_row = {
                        "field": nome_usina,  # Nome da usina
                        "nome_usina": nome_usina,
                        "deck_name": deck_name,  # Nome do deck (display_name, ex: "Fevereiro 2025")
                        "period": deck_name,  # Deck será usado como identificador da linha
                        "classe": "GTMIN",
                    }
                    
                    # Adicionar valores por mês como colunas dinâmicas para TODOS os meses consecutivos
                    # Usar formato month_YYYY-MM para as chaves
                    # E também adicionar change_type_YYYY-MM para indicar o tipo de mudança
                    for periodo in meses_ordenados:
                        month_key = f"month_{periodo}"
                        current_value = valores_por_mes.get(periodo)
                        table_row[month_key] = current_value  # Pode ser None
                        
                        # Determinar tipo de mudança comparando com deck anterior
                        change_type = "stable"  # Padrão: estável
                        
                        if current_value is not None:
                            # Procurar o último deck anterior que tem valor para este (usina, mês)
                            previous_value = None
                            
                            # Procurar do deck anterior até o primeiro deck
                            for prev_deck_idx in range(deck_idx - 1, -1, -1):
                                prev_deck_name = deck_names[prev_deck_idx]
                                key = (nome_usina, periodo)
                                prev_val = usina_mes_values.get(key, {}).get(prev_deck_name)
                                if prev_val is not None:
                                    previous_value = prev_val
                                    break
                            
                            if previous_value is None:
                                # Nenhum deck anterior tem valor: é implementação
                                change_type = "implemented"
                            else:
                                # Comparar com o valor do deck anterior
                                diff = current_value - previous_value
                                if abs(diff) < TOLERANCE:
                                    # Valores iguais: estável
                                    change_type = "stable"
                                elif diff > 0:
                                    # Valor aumentou: verde
                                    change_type = "increased"
                                else:
                                    # Valor diminuiu: vermelho
                                    change_type = "decreased"
                        
                        # Adicionar campo de tipo de mudança
                        change_type_key = f"change_type_{periodo}"
                        table_row[change_type_key] = change_type
                    
                    comparison_table.append(table_row)
        
        # Armazenar meses ordenados para o frontend (formato YYYY-MM, todos consecutivos)
        meses_metadata = list(meses_ordenados)
        
        print(f"[GTMIN_FORMATTER] [DEBUG] Convertido {len(formatted_matrix)} linhas de matriz para {len(comparison_table)} linhas de tabela comparativa transposta")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Meses únicos: {meses_ordenados}")
        print(f"[GTMIN_FORMATTER] [DEBUG]   Usinas únicas: {usinas_ordenadas}")
        if comparison_table:
            first_table_row = comparison_table[0]
            print(f"[GTMIN_FORMATTER] [DEBUG] Primeira linha da tabela comparativa:")
            print(f"[GTMIN_FORMATTER] [DEBUG]   field: {first_table_row.get('field')}")
            print(f"[GTMIN_FORMATTER] [DEBUG]   deck_name: {first_table_row.get('deck_name')}")
            month_keys = [k for k in first_table_row.keys() if k.startswith('month_')]
            print(f"[GTMIN_FORMATTER] [DEBUG]   month_keys: {month_keys}")
        
        return {
            "comparison_table": comparison_table,
            "matrix_data": formatted_matrix,  # Manter para compatibilidade (será removido depois)
            "deck_names": deck_names,  # Usar display_name (ex: "Fevereiro 2025")
            "deck_displays": deck_names,  # Mesmo que deck_names
            "deck_count": len(deck_names),
            "meses_ordenados": meses_metadata,  # Lista de meses no formato YYYY-MM (todos consecutivos, sem gaps)
            "visualization_type": "gtmin_changes_table",
            "is_multi_deck": True,
            "stats": stats,
            "chart_config": {
                "type": "table",
                "title": f"Comparação de GTMIN - {len(deck_names)} Decks",
                "tool_name": tool_name
            },
            "llm_context": {
                "total_registros": len(comparison_table),
                "total_decks": len(deck_names),
                "total_meses": len(meses_metadata),
                "description": f"Comparação de GTMIN entre {len(deck_names)} decks, com {len(comparison_table)} registros com variações."
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
        first_full_result = first_result.get("full_result", {}) if isinstance(first_result, dict) else {}
        
        # Verificar matrix_data em múltiplos lugares
        matrix_data = (
            first_result.get("matrix_data", []) or 
            first_full_result.get("matrix_data", [])
        )
        deck_names = (
            first_result.get("deck_names") or 
            first_full_result.get("deck_names") or 
            self.get_deck_names(decks_data)
        )
        stats = (
            first_result.get("stats", {}) or 
            first_full_result.get("stats", {})
        )
        
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
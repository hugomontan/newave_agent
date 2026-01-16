"""
Formatador para MudancasVazaoMinimaTool.
Visualização: Tabela de mudanças ordenadas por magnitude.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List
from newave_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData
from newave_agent.app.agents.multi_deck.formatting.data_formatters.gtmin_formatters import (
    format_date_br,
    format_periodo_coluna
)


class MudancasVazaoMinimaFormatter(ComparisonFormatter):
    """
    Formatador para MudancasVazaoMinimaTool.
    Visualização: Tabela de mudanças ordenadas por magnitude, destacando variações de VAZMIN/VAZMINT.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "MudancasVazaoMinimaTool" and (
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
        """Formata comparação de mudanças de vazão mínima para N decks."""
        if len(decks_data) < 2:
            return {"comparison_table": [], "visualization_type": "vazao_minima_table"}
        
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
            result["visualization_type"] = "vazao_minima_changes_table"
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
        aggregated["visualization_type"] = "vazao_minima_changes_table"
        return aggregated
    
    def _format_periodo_mm_yyyy(self, periodo_inicio: str) -> str:
        """
        Formata período de YYYY-MM para MM-YYYY.
        
        Args:
            periodo_inicio: Data no formato "YYYY-MM" ou "N/A"
            
        Returns:
            Período formatado como "MM-YYYY" (ex: "12-2025") ou string vazia se inválido
        """
        if not periodo_inicio or periodo_inicio == "N/A":
            return ""
        
        try:
            if "-" in periodo_inicio:
                parts = periodo_inicio.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = parts[1]
                    return f"{mes}-{ano}"
            return ""
        except:
            return ""
    
    def _format_comparison_internal(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de mudanças de vazão mínima.
        Similar ao formatador de GTMIN.
        """
        result_to_use = result_dec if result_dec.get("is_comparison") else result_jan
        
        if result_to_use.get("is_comparison") and "comparison_table" in result_to_use:
            raw_table = result_to_use.get("comparison_table", [])
            stats = result_to_use.get("stats", {})
            
            # Agrupar por tipo_vazao E tipo_mudanca (chave composta)
            # Estrutura: {tipo_vazao: {tipo_mudanca: [rows]}}
            mudancas_por_tipo_vazao = {
                "VAZMIN": {
                    "aumento": [],
                    "queda": [],
                    "remocao": [],
                    "novo": [],
                    "sem_mudanca": []
                },
                "VAZMINT": {
                    "aumento": [],
                    "queda": [],
                    "remocao": [],
                    "novo": [],
                    "sem_mudanca": []
                }
            }
            
            for row in raw_table:
                tipo_mudanca = row.get("tipo_mudanca", "N/A")
                tipo_vazao = row.get("tipo_vazao", "VAZMIN")
                
                # Garantir que tipo_vazao seja VAZMIN ou VAZMINT
                if tipo_vazao not in ["VAZMIN", "VAZMINT"]:
                    tipo_vazao = "VAZMIN"  # Fallback
                
                if tipo_mudanca in mudancas_por_tipo_vazao[tipo_vazao]:
                    mudancas_por_tipo_vazao[tipo_vazao][tipo_mudanca].append(row)
            
            # Converter para formato do frontend
            comparison_table = []
            comparison_by_type = {}
            
            tipo_labels = {
                "aumento": "Aumentos",
                "queda": "Reduções",
                "remocao": "Exclusões",
                "novo": "Inclusões",
                "sem_mudanca": "Sem Mudança"
            }
            
            tipo_vazao_labels = {
                "VAZMIN": "VAZMIN",
                "VAZMINT": "VAZMINT"
            }
            
            # Processar cada combinação de tipo_vazao e tipo_mudanca
            for tipo_vazao in ["VAZMIN", "VAZMINT"]:
                for tipo_mudanca, mudancas_tipo in mudancas_por_tipo_vazao[tipo_vazao].items():
                    if not mudancas_tipo:
                        continue
                    
                    tipo_table = []
                    for row in mudancas_tipo:
                        nome_usina = row.get("nome_usina", "N/A")
                        periodo_inicio = row.get("periodo_inicio", "N/A")
                        tipo_vazao_row = row.get("tipo_vazao", "VAZMIN")
                        
                        # Formatar período
                        # Para VAZMINT, período é OBRIGATÓRIO e deve ser sempre exibido
                        if tipo_vazao_row == "VAZMINT":
                            periodo_inicio_formatado = format_date_br(periodo_inicio)
                            # Se ainda for "N/A", usar o período original como fallback
                            if periodo_inicio_formatado == "N/A" and periodo_inicio != "N/A":
                                periodo_str = str(periodo_inicio)
                            else:
                                periodo_str = periodo_inicio_formatado if periodo_inicio_formatado != "N/A" else str(periodo_inicio)
                        else:
                            # Para VAZMIN, não há período
                            periodo_inicio_formatado = ""
                            periodo_str = ""
                        
                        # Formatar período para coluna no formato MM-YYYY
                        # Para VAZMINT, SEMPRE deve ter período_coluna no formato MM-YYYY
                        if tipo_vazao_row == "VAZMINT":
                            # Converter período de YYYY-MM para MM-YYYY
                            periodo_mm_yyyy = self._format_periodo_mm_yyyy(periodo_inicio)
                            periodo_coluna = periodo_mm_yyyy if periodo_mm_yyyy else ""
                        else:
                            periodo_coluna = ""  # VAZMIN não tem período
                        
                        vazao_dez = row.get("vazao_dezembro")
                        vazao_jan = row.get("vazao_janeiro")
                        diferenca = row.get("diferenca")
                        
                        # Para inclusões/exclusões, não calcular diferença percentual
                        is_inclusao_ou_exclusao = tipo_mudanca in ["novo", "remocao"]
                        
                        difference_percent = 0.0
                        if not is_inclusao_ou_exclusao:
                            if vazao_dez is not None and vazao_dez != 0:
                                if diferenca is not None:
                                    difference_percent = (diferenca / abs(vazao_dez)) * 100
                            elif vazao_jan is not None and vazao_jan != 0:
                                if diferenca is not None:
                                    difference_percent = (diferenca / abs(vazao_jan)) * 100
                        
                        row_formatted = {
                            "field": nome_usina,
                            "classe": tipo_vazao_row,  # Usar tipo_vazao como classe
                            "data": periodo_str,
                            "periodo_coluna": periodo_coluna,
                            "period": nome_usina,
                            "periodo_inicio": periodo_inicio,
                            "tipo_vazao": tipo_vazao_row,  # "VAZMIN" ou "VAZMINT"
                            "tipo_mudanca": tipo_mudanca,
                            # Chave composta: tipo_vazao-tipo_mudanca (ex: "VAZMIN-aumento", "VAZMINT-queda")
                            "tipo_mudanca_key": f"{tipo_vazao}-{tipo_mudanca}",
                            # Label composto: "Aumentos de VAZMIN" ou "Aumentos de VAZMINT"
                            "tipo_mudanca_label": f"{tipo_labels.get(tipo_mudanca, tipo_mudanca)} de {tipo_vazao_labels.get(tipo_vazao, tipo_vazao)}",
                            "is_inclusao_ou_exclusao": is_inclusao_ou_exclusao,
                            "deck_1": vazao_dez if vazao_dez is not None else 0,
                            "deck_1_value": vazao_dez if vazao_dez is not None else 0,
                            "deck_2": vazao_jan if vazao_jan is not None else 0,
                            "deck_2_value": vazao_jan if vazao_jan is not None else 0,
                            "diferenca": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "difference": diferenca if (diferenca is not None and not is_inclusao_ou_exclusao) else None,
                            "diferenca_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                            "difference_percent": round(difference_percent, 2) if not is_inclusao_ou_exclusao else None,
                            "magnitude": row.get("magnitude", 0),
                            "nome_usina": nome_usina,
                            "vazao_dezembro": vazao_dez,
                            "vazao_janeiro": vazao_jan,
                        }
                        
                        tipo_table.append(row_formatted)
                        comparison_table.append(row_formatted)
                
                    # Ordenar por magnitude
                    tipo_table.sort(key=lambda x: -abs(x.get("magnitude", 0)))
                    
                    # Criar chave composta para o agrupamento
                    chave_composta = f"{tipo_vazao}-{tipo_mudanca}"
                    comparison_by_type[chave_composta] = {
                        "tipo": tipo_mudanca,
                        "tipo_vazao": tipo_vazao,
                        "label": f"{tipo_labels.get(tipo_mudanca, tipo_mudanca)} de {tipo_vazao_labels.get(tipo_vazao, tipo_vazao)}",
                        "rows": tipo_table
                    }
            
            # Ordenar tabela geral
            # Ordem: primeiro por tipo_vazao (VAZMIN antes de VAZMINT), depois por tipo_mudanca, depois por magnitude
            ordem_tipo_vazao = {"VAZMIN": 0, "VAZMINT": 1}
            ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3}
            comparison_table.sort(key=lambda x: (
                ordem_tipo_vazao.get(x.get("tipo_vazao", "VAZMIN"), 99),
                ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
                -abs(x.get("magnitude", 0))
            ))
            
            # Adicionar estatísticas por tipo (agregadas)
            stats_por_tipo = {
                "aumento": sum(len(mudancas_por_tipo_vazao[tv]["aumento"]) for tv in ["VAZMIN", "VAZMINT"]),
                "queda": sum(len(mudancas_por_tipo_vazao[tv]["queda"]) for tv in ["VAZMIN", "VAZMINT"]),
                "remocao": sum(len(mudancas_por_tipo_vazao[tv]["remocao"]) for tv in ["VAZMIN", "VAZMINT"]),
                "novo": sum(len(mudancas_por_tipo_vazao[tv]["novo"]) for tv in ["VAZMIN", "VAZMINT"])
            }
            stats["mudancas_por_tipo"] = stats_por_tipo
            
            # Adicionar estatísticas por tipo_vazao
            stats_por_tipo_vazao = {
                "VAZMIN": sum(len(mudancas_por_tipo_vazao["VAZMIN"][tm]) for tm in ["aumento", "queda", "remocao", "novo"]),
                "VAZMINT": sum(len(mudancas_por_tipo_vazao["VAZMINT"][tm]) for tm in ["aumento", "queda", "remocao", "novo"])
            }
            stats["mudancas_por_tipo_vazao"] = stats_por_tipo_vazao
            
            return {
                "comparison_table": comparison_table,
                "comparison_by_type": comparison_by_type,
                "chart_data": None,
                "visualization_type": "vazao_minima_changes_table",
                "stats": stats,
                "llm_context": {
                    "total_mudancas": len(comparison_table),
                    "deck_1_name": "Dezembro 2025",
                    "deck_2_name": "Janeiro 2026",
                    "description": result_to_use.get("description", f"Análise de {len(comparison_table)} mudanças de vazão mínima entre Dezembro 2025 e Janeiro 2026, ordenadas por magnitude."),
                    "tipos_vazao": {
                        "VAZMIN": stats_por_tipo_vazao.get("VAZMIN", 0),
                        "VAZMINT": stats_por_tipo_vazao.get("VAZMINT", 0)
                    },
                    "note": "Os resultados incluem mudanças de ambos os tipos: VAZMIN (vazão mínima sem período) e VAZMINT (vazão mínima com período). Os dados estão claramente separados por seções no frontend."
                }
            }
        
        return {
            "comparison_table": [],
            "chart_data": None,
            "visualization_type": "vazao_minima_changes_table",
            "llm_context": {
                "note": "Dados não formatados corretamente."
            }
        }
    
    def _apply_forward_fill(self, valores_por_mes: Dict[str, any], meses_ordenados: List[str]) -> Dict[str, any]:
        """
        Aplica forward fill nos valores por mês.
        
        Conceito:
        - Percorrer os meses em ordem cronológica.
        - Quando encontrar um valor, guardá-lo como "último valor conhecido".
        - Para meses sem valor, usar o "último valor conhecido".
        - Se não houver valor inicial, os meses anteriores permanecem vazios.
        
        Exemplo:
        - Registros originais: 2025-12=4600, 2026-01=3900, 2026-11=4600
        - Resultado: 2025-12=4600, 2026-01=3900, 2026-02=3900, ..., 2026-10=3900, 2026-11=4600
        
        Args:
            valores_por_mes: Dicionário {mes: valor} (pode ter valores None)
            meses_ordenados: Lista de meses em ordem cronológica
            
        Returns:
            Dicionário com valores preenchidos via forward fill
        """
        resultado = {}
        ultimo_valor_conhecido = None
        
        for mes in meses_ordenados:
            valor_atual = valores_por_mes.get(mes)
            
            if valor_atual is not None:
                # Mês tem valor - guardar como último conhecido
                ultimo_valor_conhecido = valor_atual
                resultado[mes] = valor_atual
            elif ultimo_valor_conhecido is not None:
                # Mês sem valor - usar forward fill
                resultado[mes] = ultimo_valor_conhecido
            else:
                # Nenhum valor conhecido ainda - manter None
                resultado[mes] = None
        
        return resultado
    
    def _expand_period_vazmint(self, periodo_inicio: str, periodo_fim: str) -> List[str]:
        """
        Expande um período (ex: "2030-07 a 2030-10") em meses individuais.
        Retorna lista de strings no formato "YYYY-MM".
        Usado apenas para VAZMINT (VAZMIN não tem período).
        
        Args:
            periodo_inicio: Data início no formato "YYYY-MM" ou "N/A"
            periodo_fim: Data fim no formato "YYYY-MM" ou "N/A"
            
        Returns:
            Lista de meses no formato "YYYY-MM"
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
        - Linhas: Cada restrição de vazão mínima (usina + tipo_vazao + período)
        - Colunas: Cada deck (mostrando valor de vazão para aquela restrição)
        
        IMPORTANTE: Separa VAZMIN (sem período) de VAZMINT (com período).
        
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
        
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] _create_matrix_from_transitions chamado")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] deck_names obtidos: {deck_names}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] deck_names count: {len(deck_names)}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] decks_data count: {len(decks_data)}")
        
        # Coletar todos os registros únicos de todas as transições
        # Estrutura: {(nome_usina, codigo_usina, tipo_vazao, periodo_inicio, periodo_fim): {deck_name: value}}
        # IMPORTANTE: Incluir tipo_vazao na chave para separar VAZMIN de VAZMINT
        all_records = {}  # Dict[tuple, Dict[str, Any]]
        
        # Processar cada transição consecutiva para coletar valores de vazão mínima
        for i in range(len(decks_data) - 1):
            deck_from = decks_data[i]
            deck_to = decks_data[i + 1]
            
            # Extrair comparison_table formatando comparação entre este par
            from_result = deck_from.result if isinstance(deck_from.result, dict) else {}
            to_result = deck_to.result if isinstance(deck_to.result, dict) else {}
            
            # Tentar extrair comparison_table diretamente dos resultados
            comparison_table = []
            
            # Primeiro, tentar formatar comparação entre os dois decks
            transition_result = self._format_comparison_internal(
                from_result,
                to_result,
                tool_name,
                query
            )
            
            if transition_result:
                comparison_table = transition_result.get("comparison_table", [])
            
            # Se ainda não temos dados, tentar extrair diretamente dos resultados
            if not comparison_table:
                from_table = from_result.get("comparison_table", []) if isinstance(from_result, dict) else []
                to_table = to_result.get("comparison_table", []) if isinstance(to_result, dict) else []
                
                if isinstance(from_table, list) and from_table:
                    comparison_table = from_table
                elif isinstance(to_table, list) and to_table:
                    comparison_table = to_table
            
            # Se ainda não temos dados, pular esta transição
            if not comparison_table:
                print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] ⚠️ Nenhum dado encontrado para transição {i}, pulando...")
                continue
            
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] ✅ Processando {len(comparison_table)} registros da transição {i}")
            
            # Processar cada registro da transição
            deck_from_name = deck_from.display_name
            deck_to_name = deck_to.display_name
            
            for idx, row in enumerate(comparison_table):
                # Criar chave única para o registro (usina + tipo_vazao + período)
                nome_usina = row.get("nome_usina") or row.get("field") or "N/A"
                codigo_usina = row.get("codigo_usina")
                tipo_vazao = row.get("tipo_vazao", "VAZMIN")  # IMPORTANTE: incluir tipo_vazao
                periodo_inicio = row.get("periodo_inicio") or "N/A"
                periodo_fim = row.get("periodo_fim") or periodo_inicio
                
                # Garantir que tipo_vazao seja VAZMIN ou VAZMINT
                if tipo_vazao not in ["VAZMIN", "VAZMINT"]:
                    tipo_vazao = "VAZMIN"  # Fallback
                
                # Debug primeiro registro
                if idx == 0:
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Primeiro registro - campos disponíveis: {list(row.keys())}")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Primeiro registro - nome_usina: {nome_usina}, codigo: {codigo_usina}, tipo_vazao: {tipo_vazao}")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Primeiro registro - periodo_inicio: {periodo_inicio}, periodo_fim: {periodo_fim}")
                
                # Chave inclui tipo_vazao para separar VAZMIN de VAZMINT
                record_key = (
                    str(nome_usina).strip().upper(),
                    codigo_usina,
                    tipo_vazao,  # IMPORTANTE: incluir tipo_vazao na chave
                    str(periodo_inicio).strip(),
                    str(periodo_fim).strip()
                )
                
                # Inicializar registro se não existir
                if record_key not in all_records:
                    all_records[record_key] = {
                        "nome_usina": nome_usina,
                        "codigo_usina": codigo_usina,
                        "tipo_vazao": tipo_vazao,  # IMPORTANTE: preservar tipo_vazao
                        "periodo_inicio": periodo_inicio,
                        "periodo_fim": periodo_fim,
                        "vazao_values": {},  # Dict[deck_name, value] - similar a gtmin_values
                        "matrix": {},  # Dict[(deck_from, deck_to), difference] - para compatibilidade
                        "magnitude": row.get("magnitude", 0)
                    }
                
                # Extrair valores de vazão desta transição
                # Tentar múltiplos campos possíveis
                vazao_from = (
                    row.get("deck_1") or 
                    row.get("deck_1_value") or 
                    row.get("vazao_dezembro") or
                    row.get("vazao_anterior")
                )
                vazao_to = (
                    row.get("deck_2") or 
                    row.get("deck_2_value") or 
                    row.get("vazao_janeiro") or
                    row.get("vazao_atual")
                )
                
                # Debug valores extraídos (primeiro registro)
                if idx == 0:
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Primeiro registro - vazao_from: {vazao_from}")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Primeiro registro - vazao_to: {vazao_to}")
                
                # Adicionar valores aos decks usando display_name
                if vazao_from is not None and vazao_from != 0:
                    all_records[record_key]["vazao_values"][deck_from_name] = vazao_from
                    if idx == 0:
                        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   ✅ Adicionado vazao_from={vazao_from} para {deck_from_name}")
                if vazao_to is not None and vazao_to != 0:
                    all_records[record_key]["vazao_values"][deck_to_name] = vazao_to
                    if idx == 0:
                        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   ✅ Adicionado vazao_to={vazao_to} para {deck_to_name}")
                
                # Calcular diferença para a matriz de diferenças (opcional)
                difference = row.get("diferenca") or row.get("difference")
                if difference is not None:
                    matrix_key = f"{deck_from_name},{deck_to_name}"
                    all_records[record_key]["matrix"][matrix_key] = difference
        
        # Calcular diferenças faltantes na matriz de diferenças (para compatibilidade)
        for record_key, record in all_records.items():
            vazao_values = record["vazao_values"]
            matrix = record["matrix"]
            
            # Para cada par de decks, calcular diferença se não existe
            for i, deck_from in enumerate(deck_names):
                for j, deck_to in enumerate(deck_names):
                    if i == j:
                        continue
                    
                    matrix_key = f"{deck_from},{deck_to}"
                    if matrix_key not in matrix:
                        if deck_from in vazao_values and deck_to in vazao_values:
                            val_from = vazao_values[deck_from]
                            val_to = vazao_values[deck_to]
                            if val_from is not None and val_to is not None:
                                matrix[matrix_key] = val_to - val_from
        
        # Debug: verificar o que foi coletado
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] Total de registros únicos coletados: {len(all_records)}")
        if all_records:
            first_key = list(all_records.keys())[0]
            first_record = all_records[first_key]
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] Primeiro registro coletado:")
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   nome_usina: {first_record['nome_usina']}")
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   tipo_vazao: {first_record['tipo_vazao']}")
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   periodo_inicio: {first_record['periodo_inicio']}, periodo_fim: {first_record['periodo_fim']}")
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   vazao_values: {first_record['vazao_values']}")
        
        # Se não coletamos nenhum registro, retornar None para usar fallback
        if not all_records:
            print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] ⚠️ Nenhum registro coletado, retornando None")
            return None
        
        # Converter para formato esperado pelo frontend
        # Formato: cada linha é um mês individual (para VAZMINT) ou registro único (para VAZMIN), cada coluna é um deck
        formatted_matrix = []
        records_with_values = 0
        records_skipped = 0
        
        for record_key, record in all_records.items():
            vazao_values = record["vazao_values"]
            tipo_vazao = record["tipo_vazao"]
            
            # Verificar se há valores (não todos None)
            valores_nao_nulos = [v for v in vazao_values.values() if v is not None]
            if not valores_nao_nulos:
                records_skipped += 1
                continue  # Pular se não há valores
            
            records_with_values += 1
            
            # IMPORTANTE: VAZMINT expande período em meses, VAZMIN não expande
            if tipo_vazao == "VAZMINT":
                # VAZMINT: expandir período em meses individuais
                periodo_inicio = record["periodo_inicio"]
                periodo_fim = record["periodo_fim"] or periodo_inicio
                meses = self._expand_period_vazmint(periodo_inicio, periodo_fim)
                
                # Debug primeiro registro com valores
                if records_with_values == 1:
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] Primeiro registro VAZMINT com valores:")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   periodo_inicio: {periodo_inicio}, periodo_fim: {periodo_fim}")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   meses expandidos: {meses}")
                    print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   vazao_values: {vazao_values}")
                
                # Criar uma linha para cada mês
                for mes in meses:
                    # Criar grupo de valores iguais para coloração (por mês)
                    value_groups = {}
                    for deck_name, value in vazao_values.items():
                        if value is not None:
                            rounded_value = round(float(value), 2)
                            value_key = str(rounded_value)
                            if value_key not in value_groups:
                                value_groups[value_key] = []
                            value_groups[value_key].append(deck_name)
                    
                    formatted_row = {
                        "nome_usina": record["nome_usina"],
                        "codigo_usina": record.get("codigo_usina"),
                        "tipo_vazao": tipo_vazao,  # IMPORTANTE: preservar tipo_vazao
                        "periodo": mes,  # Mês individual (ex: "2030-07")
                        "periodo_inicio": periodo_inicio,  # Manter período original para referência
                        "periodo_fim": periodo_fim,  # Manter período original para referência
                        "vazao_values": vazao_values,  # Dict[deck_name, value] - valores por deck
                        "matrix": record.get("matrix", {}),  # Matriz de diferenças (para compatibilidade)
                        "value_groups": value_groups,  # Grupos de valores iguais para coloração
                        "_magnitude": record.get("magnitude", 0),  # Manter magnitude para ordenação
                        "_sort_key": (record["nome_usina"], tipo_vazao, mes)  # Chave para ordenação
                    }
                    formatted_matrix.append(formatted_row)
            else:
                # VAZMIN: não expande período (valor fixo, sem período)
                # Criar apenas uma linha por registro
                value_groups = {}
                for deck_name, value in vazao_values.items():
                    if value is not None:
                        rounded_value = round(float(value), 2)
                        value_key = str(rounded_value)
                        if value_key not in value_groups:
                            value_groups[value_key] = []
                        value_groups[value_key].append(deck_name)
                
                formatted_row = {
                    "nome_usina": record["nome_usina"],
                    "codigo_usina": record.get("codigo_usina"),
                    "tipo_vazao": tipo_vazao,  # IMPORTANTE: preservar tipo_vazao
                    "periodo": "N/A",  # VAZMIN não tem período
                    "periodo_inicio": "N/A",
                    "periodo_fim": "N/A",
                    "vazao_values": vazao_values,  # Dict[deck_name, value] - valores por deck
                    "matrix": record.get("matrix", {}),  # Matriz de diferenças (para compatibilidade)
                    "value_groups": value_groups,  # Grupos de valores iguais para coloração
                    "_magnitude": record.get("magnitude", 0),  # Manter magnitude para ordenação
                    "_sort_key": (record["nome_usina"], tipo_vazao, "N/A")  # Chave para ordenação
                }
                formatted_matrix.append(formatted_row)
        
        # Ordenar por nome da usina, tipo_vazao (VAZMIN antes de VAZMINT), e depois por período
        ordem_tipo_vazao = {"VAZMIN": 0, "VAZMINT": 1}
        formatted_matrix.sort(key=lambda x: (
            x.get("nome_usina", ""),
            ordem_tipo_vazao.get(x.get("tipo_vazao", "VAZMIN"), 99),
            x.get("periodo", "N/A")
        ))
        
        # Remover campos auxiliares antes de retornar
        for row in formatted_matrix:
            row.pop("_magnitude", None)
            row.pop("_sort_key", None)
        
        # Debug final
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] Resumo final:")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Registros coletados: {len(all_records)}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Registros com valores: {records_with_values}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Registros pulados (sem valores): {records_skipped}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Linhas na matriz final: {len(formatted_matrix)}")
        
        # Garantir que todos os deck_names estão presentes em vazao_values de cada linha
        for row in formatted_matrix:
            vazao_values = row.get("vazao_values", {})
            for deck_name in deck_names:
                if deck_name not in vazao_values:
                    vazao_values[deck_name] = None
        
        # Separar VAZMIN e VAZMINT para processamento diferente
        # VAZMINT: precisa transpor para meses como colunas
        # VAZMIN: pode usar formato tradicional (decks como colunas)
        
        # Coletar meses únicos apenas de VAZMINT
        meses_unicos = set()
        usinas_unicas = set()
        
        for record_key, record in all_records.items():
            tipo_vazao = record["tipo_vazao"]
            if tipo_vazao == "VAZMINT":
                periodo_inicio = record["periodo_inicio"]
                periodo_fim = record["periodo_fim"] or periodo_inicio
                meses_expandidos = self._expand_period_vazmint(periodo_inicio, periodo_fim)
                meses_unicos.update(meses_expandidos)
            usinas_unicas.add(record["nome_usina"])
        
        # Gerar meses consecutivos se necessário
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
        else:
            meses_ordenados = []
        
        # Transpor matriz: linhas = (deck, usina), colunas = meses (apenas para VAZMINT)
        # Para VAZMIN, manter formato tradicional (decks como colunas)
        from collections import defaultdict
        
        # Estrutura para VAZMINT: {(nome_usina, periodo): {deck_name: value}}
        usina_mes_values = defaultdict(dict)
        
        # Coletar valores por (usina, mês) usando deck_names (display_name) - apenas VAZMINT
        for matrix_row in formatted_matrix:
            nome_usina = matrix_row.get("nome_usina", "N/A")
            tipo_vazao = matrix_row.get("tipo_vazao", "VAZMIN")
            periodo = matrix_row.get("periodo", "N/A")
            vazao_values = matrix_row.get("vazao_values", {})
            
            # Apenas VAZMINT precisa transpor (tem meses)
            if tipo_vazao == "VAZMINT" and periodo != "N/A":
                for deck_name, value in vazao_values.items():
                    if value is not None:
                        usina_mes_values[(nome_usina, periodo)][deck_name] = value
        
        usinas_ordenadas = sorted(usinas_unicas)
        
        # Criar comparison_table transposta: cada linha = (deck, usina), cada coluna = mês (apenas VAZMINT)
        # Para VAZMIN, manter formato tradicional
        comparison_table = []
        TOLERANCE = 0.01  # Tolerância para comparação de float
        
        # Processar VAZMINT (matriz transposta)
        if meses_ordenados:
            for deck_idx, deck_name in enumerate(deck_names):
                for nome_usina in usinas_ordenadas:
                    # Verificar se há valores para esta combinação (deck, usina) em VAZMINT
                    tem_valores = False
                    valores_por_mes_raw = {}
                    
                    # Coletar valores para TODOS os meses consecutivos (mesmo que None)
                    for periodo in meses_ordenados:
                        key = (nome_usina, periodo)
                        value = usina_mes_values.get(key, {}).get(deck_name)
                        valores_por_mes_raw[periodo] = value
                        if value is not None:
                            tem_valores = True
                    
                    # Aplicar forward fill para preencher meses sem valor
                    valores_por_mes = self._apply_forward_fill(valores_por_mes_raw, meses_ordenados)
                    
                    # Só criar linha se houver pelo menos um valor
                    if tem_valores:
                        table_row = {
                            "field": nome_usina,
                            "nome_usina": nome_usina,
                            "deck_name": deck_name,
                            "period": deck_name,
                            "classe": "VAZMINT",  # Tipo de vazão
                            "tipo_vazao": "VAZMINT",  # IMPORTANTE: preservar tipo_vazao
                        }
                        
                        # Adicionar valores por mês como colunas dinâmicas
                        for periodo in meses_ordenados:
                            month_key = f"month_{periodo}"
                            current_value = valores_por_mes.get(periodo)
                            table_row[month_key] = current_value  # Pode ser None
                            
                            # Determinar tipo de mudança comparando com deck anterior
                            change_type = "stable"
                            
                            if current_value is not None:
                                # Procurar o último deck anterior que tem valor para este (usina, mês)
                                previous_value = None
                                
                                for prev_deck_idx in range(deck_idx - 1, -1, -1):
                                    prev_deck_name = deck_names[prev_deck_idx]
                                    key = (nome_usina, periodo)
                                    prev_val = usina_mes_values.get(key, {}).get(prev_deck_name)
                                    if prev_val is not None:
                                        previous_value = prev_val
                                        break
                                
                                if previous_value is None:
                                    change_type = "implemented"
                                else:
                                    diff = current_value - previous_value
                                    if abs(diff) < TOLERANCE:
                                        change_type = "stable"
                                    elif diff > 0:
                                        change_type = "increased"
                                    else:
                                        change_type = "decreased"
                            
                            # Adicionar campo de tipo de mudança
                            change_type_key = f"change_type_{periodo}"
                            table_row[change_type_key] = change_type
                        
                        comparison_table.append(table_row)
        
        # Processar VAZMIN (formato tradicional - decks como colunas)
        # Coletar registros VAZMIN
        vazmin_records = [r for r in formatted_matrix if r.get("tipo_vazao") == "VAZMIN"]
        
        for vazmin_row in vazmin_records:
            nome_usina = vazmin_row.get("nome_usina", "N/A")
            vazao_values = vazmin_row.get("vazao_values", {})
            
            # Criar linha tradicional para VAZMIN
            table_row = {
                "field": nome_usina,
                "nome_usina": nome_usina,
                "codigo_usina": vazmin_row.get("codigo_usina"),
                "period": nome_usina,
                "classe": "VAZMIN",
                "tipo_vazao": "VAZMIN",  # IMPORTANTE: preservar tipo_vazao
                "periodo": "N/A",
                "periodo_inicio": "N/A",
                "periodo_fim": "N/A",
            }
            
            # Adicionar valores por deck
            for deck_idx, deck_name in enumerate(deck_names):
                deck_key = f"deck_{deck_idx + 1}"
                deck_value_key = f"deck_{deck_idx + 1}_value"
                value = vazao_values.get(deck_name)
                table_row[deck_key] = value if value is not None else None
                table_row[deck_value_key] = value if value is not None else None
            
            comparison_table.append(table_row)
        
        # Armazenar meses ordenados para o frontend (formato YYYY-MM, todos consecutivos)
        meses_metadata = list(meses_ordenados)
        
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG] Convertido {len(formatted_matrix)} linhas de matriz para {len(comparison_table)} linhas de tabela comparativa")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Meses únicos (VAZMINT): {meses_ordenados}")
        print(f"[VAZAO_MINIMA_FORMATTER] [DEBUG]   Usinas únicas: {usinas_ordenadas}")
        
        # Calcular estatísticas
        stats = {
            "total_mudancas": len(comparison_table),
            "mudancas_por_tipo": {
                "aumento": 0,
                "queda": 0,
                "remocao": 0,
                "novo": 0
            },
            "mudancas_por_tipo_vazao": {
                "VAZMIN": len([r for r in formatted_matrix if r.get("tipo_vazao") == "VAZMIN"]),
                "VAZMINT": len([r for r in formatted_matrix if r.get("tipo_vazao") == "VAZMINT"])
            }
        }
        
        return {
            "comparison_table": comparison_table,
            "matrix_data": formatted_matrix,  # Manter para compatibilidade
            "deck_names": deck_names,
            "deck_displays": deck_names,
            "deck_count": len(deck_names),
            "meses_ordenados": meses_metadata,  # Lista de meses no formato YYYY-MM (apenas VAZMINT)
            "visualization_type": "vazao_minima_changes_table",
            "is_multi_deck": True,
            "stats": stats,
            "chart_config": {
                "type": "table",
                "title": f"Comparação de Vazão Mínima - {len(deck_names)} Decks",
                "tool_name": tool_name
            },
            "llm_context": {
                "total_registros": len(comparison_table),
                "total_decks": len(deck_names),
                "total_meses": len(meses_metadata),
                "description": f"Comparação de vazão mínima entre {len(deck_names)} decks, com {len(comparison_table)} registros com variações. Separado por VAZMIN (sem período) e VAZMINT (com período)."
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
        Formato TRANSPOSTO igual ao GTMIN: linhas = (deck, usina), colunas = meses (para VAZMINT).
        
        Args:
            decks_data: Lista de dados dos decks
            tool_name: Nome da tool
            query: Query do usuário
            
        Returns:
            Dicionário formatado com dados da matriz transposta
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
        
        if not matrix_data:
            return {
                "comparison_table": [],
                "matrix_data": [],
                "deck_names": deck_names,
                "visualization_type": "vazao_minima_changes_table",
                "is_multi_deck": True,
                "stats": stats or {},
            }
        
        # Separar VAZMIN e VAZMINT
        vazmint_rows = [r for r in matrix_data if r.get("tipo_vazao") == "VAZMINT"]
        vazmin_rows = [r for r in matrix_data if r.get("tipo_vazao") == "VAZMIN"]
        
        # Processar VAZMINT: formato transposto (linhas = deck, colunas = meses)
        comparison_table = []
        meses_ordenados = []
        
        if vazmint_rows:
            # Coletar todos os meses únicos de todos os períodos VAZMINT
            meses_unicos = set()
            usinas_unicas = set()
            usina_mes_values = {}  # {(nome_usina, mes): {deck_name: value}}
            
            for row in vazmint_rows:
                nome_usina = row.get("nome_usina", "N/A")
                periodo_inicio = row.get("periodo_inicio", "N/A")
                periodo_fim = row.get("periodo_fim") or periodo_inicio
                vazao_values = row.get("vazao_values", {})
                
                if periodo_inicio != "N/A":
                    # Expandir período em meses
                    meses = self._expand_period_vazmint(periodo_inicio, periodo_fim)
                    meses_unicos.update(meses)
                    usinas_unicas.add(nome_usina)
                    
                    # Armazenar valores por (usina, mês, deck)
                    for mes in meses:
                        key = (nome_usina, mes)
                        if key not in usina_mes_values:
                            usina_mes_values[key] = {}
                        # Todos os meses do período têm o mesmo valor
                        for deck_name, value in vazao_values.items():
                            if value is not None:
                                usina_mes_values[key][deck_name] = value
            
            # Garantir que todos os meses sejam consecutivos (preencher gaps)
            if meses_unicos:
                meses_lista = sorted(meses_unicos)
                primeiro_mes = meses_lista[0]
                ultimo_mes = meses_lista[-1]
                
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
                
                meses_ordenados = generate_all_months(primeiro_mes, ultimo_mes)
            else:
                meses_ordenados = sorted(meses_unicos)
            
            usinas_ordenadas = sorted(usinas_unicas)
            TOLERANCE = 0.01
            
            # Criar linhas transpostas: cada linha = (deck, usina)
            for deck_idx, deck_name in enumerate(deck_names):
                for nome_usina in usinas_ordenadas:
                    # Verificar se há valores para esta combinação (deck, usina)
                    tem_valores = False
                    valores_por_mes_raw = {}
                    
                    # Coletar valores para TODOS os meses consecutivos
                    for mes in meses_ordenados:
                        key = (nome_usina, mes)
                        value = usina_mes_values.get(key, {}).get(deck_name)
                        valores_por_mes_raw[mes] = value
                        if value is not None:
                            tem_valores = True
                    
                    # Aplicar forward fill para preencher meses sem valor
                    valores_por_mes = self._apply_forward_fill(valores_por_mes_raw, meses_ordenados)
                    
                    # Só criar linha se houver pelo menos um valor
                    if tem_valores:
                        table_row = {
                            "field": nome_usina,
                            "nome_usina": nome_usina,
                            "deck_name": deck_name,
                            "period": deck_name,
                            "classe": "VAZMINT",
                            "tipo_vazao": "VAZMINT",
                        }
                        
                        # Adicionar valores por mês como colunas dinâmicas
                        for mes in meses_ordenados:
                            month_key = f"month_{mes}"
                            current_value = valores_por_mes.get(mes)
                            table_row[month_key] = current_value
                            
                            # Determinar tipo de mudança comparando com deck anterior
                            change_type = "stable"
                            
                            if current_value is not None:
                                # Procurar o último deck anterior que tem valor
                                previous_value = None
                                for prev_deck_idx in range(deck_idx - 1, -1, -1):
                                    prev_deck_name = deck_names[prev_deck_idx]
                                    key = (nome_usina, mes)
                                    prev_val = usina_mes_values.get(key, {}).get(prev_deck_name)
                                    if prev_val is not None:
                                        previous_value = prev_val
                                        break
                                
                                if previous_value is None:
                                    change_type = "implemented"
                                else:
                                    diff = current_value - previous_value
                                    if abs(diff) < TOLERANCE:
                                        change_type = "stable"
                                    elif diff > 0:
                                        change_type = "increased"
                                    else:
                                        change_type = "decreased"
                            
                            change_type_key = f"change_type_{mes}"
                            table_row[change_type_key] = change_type
                        
                        comparison_table.append(table_row)
        
        # Processar VAZMIN: formato tradicional (linhas = usina, colunas = decks)
        # VAZMIN não tem período, então não precisa de matriz transposta
        for row in vazmin_rows:
            nome_usina = row.get("nome_usina", "N/A")
            vazao_values = row.get("vazao_values", {})
            
            table_row = {
                "field": nome_usina,
                "nome_usina": nome_usina,
                "classe": "VAZMIN",
                "tipo_vazao": "VAZMIN",
            }
            
            # Adicionar valores por deck
            for deck_idx, deck_name in enumerate(deck_names):
                value = vazao_values.get(deck_name)
                table_row[f"deck_{deck_idx + 1}"] = deck_name
                table_row[f"deck_{deck_idx + 1}_value"] = value
            
            comparison_table.append(table_row)
        
        return {
            "comparison_table": comparison_table,
            "matrix_data": comparison_table,  # Manter para compatibilidade
            "deck_names": deck_names,
            "meses_ordenados": meses_ordenados,  # Lista de meses para VAZMINT
            "visualization_type": "vazao_minima_changes_table",
            "is_multi_deck": True,
            "stats": stats,
            "chart_config": {
                "type": "matrix",
                "title": f"Matriz de Comparação Vazão Mínima - {len(deck_names)} Decks",
                "tool_name": tool_name
            },
            "llm_context": {
                "total_registros": len(comparison_table),
                "total_decks": len(deck_names),
                "description": f"Matriz de comparação de vazão mínima entre {len(deck_names)} decks, com {len(comparison_table)} registros com variações. Separado por VAZMIN (sem período) e VAZMINT (com período)."
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
        Coleta todas as mudanças de vazão mínima de todas as transições.
        """
        all_comparison_tables = []
        all_comparison_by_type = {}
        all_stats = {
            "total_mudancas": 0,
            "mudancas_por_tipo": {
                "aumento": 0,
                "queda": 0,
                "remocao": 0,
                "novo": 0,
                "sem_mudanca": 0
            },
            "mudancas_por_tipo_vazao": {
                "VAZMIN": 0,
                "VAZMINT": 0
            }
        }
        
        for transition in transitions:
            result = transition["result"]
            comparison_table = result.get("comparison_table", [])
            comparison_by_type = result.get("comparison_by_type", {})
            stats = result.get("stats", {})
            
            # Adicionar informações da transição a cada registro
            for row in comparison_table:
                row["transition"] = f"{transition['from_deck']} → {transition['to_deck']}"
                row["from_deck"] = transition["from_deck"]
                row["to_deck"] = transition["to_deck"]
            
            all_comparison_tables.extend(comparison_table)
            
            # Agregar comparison_by_type
            for tipo, tipo_data in comparison_by_type.items():
                if tipo not in all_comparison_by_type:
                    all_comparison_by_type[tipo] = {
                        "tipo": tipo,
                        "label": tipo_data.get("label", tipo),
                        "rows": []
                    }
                all_comparison_by_type[tipo]["rows"].extend(tipo_data.get("rows", []))
            
            # Agregar estatísticas
            if stats:
                all_stats["total_mudancas"] += stats.get("total_mudancas", len(comparison_table))
                mudancas_por_tipo = stats.get("mudancas_por_tipo", {})
                for tipo, count in mudancas_por_tipo.items():
                    if tipo in all_stats["mudancas_por_tipo"]:
                        all_stats["mudancas_por_tipo"][tipo] += count
                
                mudancas_por_tipo_vazao = stats.get("mudancas_por_tipo_vazao", {})
                for tipo_vazao, count in mudancas_por_tipo_vazao.items():
                    if tipo_vazao in all_stats["mudancas_por_tipo_vazao"]:
                        all_stats["mudancas_por_tipo_vazao"][tipo_vazao] += count
        
        # Reordenar tabela geral por tipo_vazao, tipo_mudanca e magnitude
        ordem_tipo_vazao = {"VAZMIN": 0, "VAZMINT": 1}
        ordem_tipo = {"aumento": 0, "queda": 1, "remocao": 2, "novo": 3, "sem_mudanca": 4}
        all_comparison_tables.sort(key=lambda x: (
            ordem_tipo_vazao.get(x.get("tipo_vazao", "VAZMIN"), 99),
            ordem_tipo.get(x.get("tipo_mudanca", "N/A"), 99),
            -abs(x.get("magnitude", 0)) if x.get("magnitude") else 0  # Maior magnitude primeiro dentro do mesmo tipo
        ))
        
        return {
            "comparison_table": all_comparison_tables,
            "comparison_by_type": all_comparison_by_type,
            "chart_data": None,
            "visualization_type": "vazao_minima_changes_table",
            "stats": all_stats,
            "llm_context": {
                "total_mudancas": len(all_comparison_tables),
                "total_transitions": len(transitions),
                "description": f"Análise histórica de {len(all_comparison_tables)} mudanças de vazão mínima ao longo de {len(transitions)} transições entre decks, ordenadas por magnitude.",
                "tipos_vazao": all_stats["mudancas_por_tipo_vazao"],
                "note": "Os resultados incluem mudanças de ambos os tipos: VAZMIN (vazão mínima sem período) e VAZMINT (vazão mínima com período). Os dados estão claramente separados por seções no frontend."
            }
        }
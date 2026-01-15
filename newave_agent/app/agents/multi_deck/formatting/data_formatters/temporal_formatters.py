"""
Formatadores temporais para comparação multi-deck.
Para tools que retornam séries históricas (dados por período).
Suporta N decks para comparação dinâmica.
"""
import math
import re
from typing import Dict, Any, List, Optional, Tuple
from newave_agent.app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class ClastComparisonFormatter(ComparisonFormatter):
    """
    Formatador para ClastValoresTool - custos de classes térmicas.
    Visualização: Tabela comparativa + Gráfico de linha temporal
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "ClastValoresTool" and (
            "dados_estruturais" in result_structure or 
            "dados_conjunturais" in result_structure
        )
    
    def get_priority(self) -> int:
        return 100  # Alta prioridade - muito específico
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de custos de classes térmicas para N decks.
        Suporta análise histórica com múltiplos decks.
        """
        if len(decks_data) < 1:
            return {"comparison_table": [], "chart_data": None, "visualization_type": "table"}
        
        if len(decks_data) == 1:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table",
                "deck_names": self.get_deck_names(decks_data),
                "is_multi_deck": False,
                "error": "Apenas um deck disponível para comparação"
            }
        
        # Verificar se é query de CVU
        is_cvu = self._is_cvu_query(query)
        
        # Se for CVU, usar formato simplificado que suporta N decks
        if is_cvu:
            return self._format_cvu_simplified_multi(decks_data, tool_name, query)
        
        # Para outras queries, usar formato interno (compatibilidade com 2 decks)
        if len(decks_data) >= 2:
            result_dec = decks_data[0].result
            result_jan = decks_data[-1].result
            result = self._format_comparison_internal(result_dec, result_jan, tool_name, query, decks_data)
            result["deck_names"] = self.get_deck_names(decks_data)
            result["is_multi_deck"] = len(decks_data) > 2
            return result
        
        return {"comparison_table": [], "chart_data": None, "visualization_type": "table"}
    
    def _format_comparison_internal(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        decks_data: Optional[List[DeckData]] = None
    ) -> Dict[str, Any]:
        """
        Formata comparação de custos de classes térmicas.
        Foca em dados estruturais (custos por ano/classe).
        Para CVU, usa formato simplificado (tabela simples + gráfico com uma linha por deck).
        """
        # Verificar se é query de CVU
        is_cvu = self._is_cvu_query(query)
        
        dados_estruturais_dec = result_dec.get("dados_estruturais", [])
        dados_estruturais_jan = result_jan.get("dados_estruturais", [])
        
        if not dados_estruturais_dec and not dados_estruturais_jan:
            # Fallback para conjunturais se não há estruturais
            if decks_data and len(decks_data) > 2:
                return self._format_conjunturais_multi(decks_data, tool_name, query)
            return self._format_conjunturais(result_dec, result_jan, tool_name, query)
        
        # Se for CVU, usar formato simplificado
        if is_cvu:
            # Se temos decks_data (N decks), usar método multi-deck
            if decks_data and len(decks_data) > 2:
                return self._format_cvu_simplified_multi(decks_data, tool_name, query)
            # Caso contrário, usar método legado (2 decks)
            return self._format_cvu_simplified(
                dados_estruturais_dec,
                dados_estruturais_jan,
                result_dec,
                result_jan
            )
        
        # Para queries não-CVU, verificar se temos N decks
        if decks_data and len(decks_data) > 2:
            return self._format_estruturais_multi(decks_data, tool_name, query)
        
        # Método legado para 2 decks
        # Indexar por (classe, ano)
        dec_indexed = self._index_estruturais(dados_estruturais_dec)
        jan_indexed = self._index_estruturais(dados_estruturais_jan)
        
        # Construir tabela comparativa
        comparison_table = []
        chart_labels = []
        chart_series = {}  # {classe_nome: {dec: [...], jan: [...]}}
        
        all_keys = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        for key in all_keys:
            dec_record = dec_indexed.get(key, {})
            jan_record = jan_indexed.get(key, {})
            
            classe = dec_record.get("codigo_usina") or jan_record.get("codigo_usina")
            nome_classe = dec_record.get("nome_usina") or jan_record.get("nome_usina", f"Classe {classe}")
            ano = dec_record.get("indice_ano_estudo") or jan_record.get("indice_ano_estudo")
            
            val_dec = self._sanitize_number(dec_record.get("valor"))
            val_jan = self._sanitize_number(jan_record.get("valor"))
            
            if val_dec is not None and val_jan is not None:
                diff = val_jan - val_dec
                diff_percent = ((val_jan - val_dec) / val_dec * 100) if val_dec != 0 else 0
                
                comparison_table.append({
                    "classe": nome_classe,
                    "codigo_classe": classe,
                    "ano": ano,
                    "deck_1_value": round(val_dec, 2),
                    "deck_2_value": round(val_jan, 2),
                    "difference": round(diff, 2),
                    "difference_percent": round(diff_percent, 4)
                })
                
                # Dados para gráfico
                periodo_label = f"Ano {ano}"
                if nome_classe not in chart_series:
                    chart_series[nome_classe] = {"dec": [], "jan": []}
                
                chart_series[nome_classe]["dec"].append({
                    "period": periodo_label,
                    "value": round(val_dec, 2)
                })
                chart_series[nome_classe]["jan"].append({
                    "period": periodo_label,
                    "value": round(val_jan, 2)
                })
                
                if periodo_label not in chart_labels:
                    chart_labels.append(periodo_label)
        
        # Construir chart_data (uma série por classe)
        chart_datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff"]
        
        for idx, (nome_classe, series) in enumerate(chart_series.items()):
            color = colors[idx % len(colors)]
            
            # Alinhar valores por período
            dec_values = [None] * len(chart_labels)
            jan_values = [None] * len(chart_labels)
            
            for item in series["dec"]:
                if item["period"] in chart_labels:
                    idx_period = chart_labels.index(item["period"])
                    dec_values[idx_period] = item["value"]
            
            for item in series["jan"]:
                if item["period"] in chart_labels:
                    idx_period = chart_labels.index(item["period"])
                    jan_values[idx_period] = item["value"]
            
            chart_datasets.append({
                "label": f"{nome_classe} - Dezembro",
                "data": dec_values
            })
            chart_datasets.append({
                "label": f"{nome_classe} - Janeiro",
                "data": jan_values
            })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Evolução dos Custos por Classe Térmica",
                "x_axis": "Ano",
                "y_axis": "Custo (R$/MWh)"
            }
        }
    
    def _index_estruturais(self, dados: List[Dict]) -> Dict[str, Dict]:
        """Indexa dados estruturais por (classe, ano)."""
        index = {}
        for record in dados:
            classe = record.get("codigo_usina")
            ano = record.get("indice_ano_estudo")
            if classe is not None and ano is not None:
                key = f"{classe}-{ano}"
                index[key] = record
        return index
    
    def _format_conjunturais(self, result_dec, result_jan, tool_name, query):
        """Formata dados conjunturais (modificações sazonais)."""
        dados_conj_dec = result_dec.get("dados_conjunturais", [])
        dados_conj_jan = result_jan.get("dados_conjunturais", [])
        
        # Para conjunturais, apenas tabela (sem gráfico temporal)
        comparison_table = []
        
        dec_indexed = {(r.get("codigo_usina"), r.get("data_inicio")): r for r in dados_conj_dec}
        jan_indexed = {(r.get("codigo_usina"), r.get("data_inicio")): r for r in dados_conj_jan}
        
        all_keys = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        for key in all_keys:
            dec_record = dec_indexed.get(key)
            jan_record = jan_indexed.get(key)
            
            val_dec = self._sanitize_number(dec_record.get("custo")) if dec_record else None
            val_jan = self._sanitize_number(jan_record.get("custo")) if jan_record else None
            
            if val_dec is not None and val_jan is not None:
                diff = val_jan - val_dec
                comparison_table.append({
                    "classe": dec_record.get("nome_usina") or jan_record.get("nome_usina"),
                    "data_inicio": dec_record.get("data_inicio") or jan_record.get("data_inicio"),
                    "deck_1_value": round(val_dec, 2),
                    "deck_2_value": round(val_jan, 2),
                    "difference": round(diff, 2)
                })
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "table_only"
        }
    
    def _format_estruturais_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata dados estruturais (custos por ano/classe) para N decks."""
        # Extrair dados de todos os decks
        all_keys = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados_estruturais = result.get("dados_estruturais", [])
            
            # Indexar por (classe, ano)
            deck_indexed = self._index_estruturais(dados_estruturais)
            all_keys.update(deck_indexed.keys())
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": deck_indexed
            })
        
        # Construir tabela comparativa com N colunas
        comparison_table = []
        chart_labels = []
        chart_series = {}  # {classe_nome: {deck_idx: [...]}}
        
        for key in sorted(all_keys):
            # Extrair classe e ano do key
            parts = key.split("-")
            if len(parts) >= 2:
                classe = int(parts[0]) if parts[0].isdigit() else None
                ano = int(parts[1]) if parts[1].isdigit() else None
                
                if classe is None or ano is None:
                    continue
                
                # Obter nome da classe do primeiro deck que tiver
                nome_classe = None
                for deck_info in decks_info:
                    record = deck_info["indexed"].get(key, {})
                    if record.get("nome_usina"):
                        nome_classe = record.get("nome_usina")
                        break
                if not nome_classe:
                    nome_classe = f"Classe {classe}"
                
                # Criar linha na tabela
                table_row = {
                    "classe": nome_classe,
                    "codigo_classe": classe,
                    "ano": ano
                }
                
                # Adicionar valores de cada deck
                periodo_label = f"Ano {ano}"
                if periodo_label not in chart_labels:
                    chart_labels.append(periodo_label)
                
                if nome_classe not in chart_series:
                    chart_series[nome_classe] = {deck_idx: [] for deck_idx in range(len(decks_info))}
                
                for deck_idx, deck_info in enumerate(decks_info):
                    record = deck_info["indexed"].get(key, {})
                    val = self._sanitize_number(record.get("valor"))
                    table_row[f"deck_{deck_idx + 1}"] = round(val, 2) if val is not None else None
                    
                    # Adicionar ao gráfico
                    chart_series[nome_classe][deck_idx].append({
                        "period": periodo_label,
                        "value": round(val, 2) if val is not None else None
                    })
                
                comparison_table.append(table_row)
        
        # Construir chart_data (uma série por classe, com N datasets por classe)
        chart_datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff", "#0088fe", "#00c49f", "#ffbb28", "#ff8042"]
        
        for idx, (nome_classe, series) in enumerate(chart_series.items()):
            color = colors[idx % len(colors)]
            
            # Criar dataset para cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                # Alinhar valores por período
                values = [None] * len(chart_labels)
                for item in series[deck_idx]:
                    if item["period"] in chart_labels:
                        idx_period = chart_labels.index(item["period"])
                        values[idx_period] = item["value"]
                
                chart_datasets.append({
                    "label": f"{nome_classe} - {deck_info['display_name']}",
                    "data": values
                })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Evolução dos Custos por Classe Térmica",
                "x_axis": "Ano",
                "y_axis": "Custo (R$/MWh)"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_conjunturais_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata dados conjunturais (modificações sazonais) para N decks."""
        # Extrair dados de todos os decks
        all_keys = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados_conjunturais = result.get("dados_conjunturais", [])
            
            # Indexar por (classe, data_inicio)
            deck_indexed = {}
            for record in dados_conjunturais:
                key = (record.get("codigo_usina"), record.get("data_inicio"))
                if key[0] is not None and key[1] is not None:
                    deck_indexed[key] = record
                    all_keys.add(key)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": deck_indexed
            })
        
        # Construir tabela comparativa com N colunas
        comparison_table = []
        
        for key in sorted(all_keys):
            classe, data_inicio = key
            
            # Obter nome da classe do primeiro deck que tiver
            nome_classe = None
            for deck_info in decks_info:
                record = deck_info["indexed"].get(key, {})
                if record.get("nome_usina"):
                    nome_classe = record.get("nome_usina")
                    break
            if not nome_classe:
                nome_classe = f"Classe {classe}"
            
            # Criar linha na tabela
            table_row = {
                "classe": nome_classe,
                "data_inicio": data_inicio
            }
            
            # Adicionar valores de cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                record = deck_info["indexed"].get(key, {})
                val = self._sanitize_number(record.get("custo"))
                table_row[f"deck_{deck_idx + 1}"] = round(val, 2) if val is not None else None
            
            comparison_table.append(table_row)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "table_only",
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _is_cvu_query(self, query: str) -> bool:
        """Verifica se a query é sobre CVU (Custo Variável Unitário)."""
        query_lower = query.lower()
        cvu_keywords = [
            "cvu",
            "custo variável unitário",
            "custo variavel unitario",
            "custo variável unitario",
            "custo variavel unitário",
        ]
        return any(kw in query_lower for kw in cvu_keywords)
    
    def _get_base_year_from_deck(self, result: Dict[str, Any]) -> Optional[int]:
        """
        Tenta extrair o ano base do deck a partir do caminho ou nome do deck.
        O ano base é o ano do deck, e o primeiro ano do estudo (indice_ano_estudo=1) 
        corresponde ao ano seguinte (ano_base + 1).
        
        Exemplo: Se o deck é "NW202512" (dezembro de 2025), o ano base é 2025,
        e o primeiro ano do estudo (indice_ano_estudo=1) é 2026.
        """
        import re
        import os
        
        # Tentar extrair do caminho do deck se disponível
        deck_path = result.get("deck_path") or result.get("deck")
        if deck_path:
            # Converter Path para string se necessário
            deck_path_str = str(deck_path)
            
            # Tentar extrair ano do nome do deck (ex: "NW202512" -> 2025)
            # Padrão: NW + 4 dígitos (ano) + 2 dígitos (mês)
            ano_match = re.search(r'NW(\d{4})\d{2}', deck_path_str)
            if ano_match:
                ano_base = int(ano_match.group(1))
                return ano_base
            
            # Tentar padrão genérico de 4 dígitos que possa ser um ano (2000-2100)
            ano_match = re.search(r'(20[0-5]\d)', deck_path_str)
            if ano_match:
                ano_base = int(ano_match.group(1))
                return ano_base
            
            # Tentar ler do DGER.DAT se o caminho for um diretório válido
            if os.path.isdir(deck_path_str):
                dger_path = os.path.join(deck_path_str, "DGER.DAT")
                if not os.path.exists(dger_path):
                    dger_path = os.path.join(deck_path_str, "dger.dat")
                
                if os.path.exists(dger_path):
                    try:
                        with open(dger_path, 'r', encoding='latin-1') as f:
                            lines = f.readlines()
                            if len(lines) > 20:
                                reg21 = lines[20].strip()
                                # Procurar por padrão de 4 dígitos que possa ser um ano (2000-2100)
                                anos_match = re.findall(r'\b(20[0-5]\d)\b', reg21)
                                if anos_match:
                                    # Pegar o primeiro ano encontrado (geralmente é o ano do estudo)
                                    ano_encontrado = int(anos_match[0])
                                    # O ano base geralmente é um ano antes do primeiro ano do histórico
                                    # Mas para CVU, precisamos do ano do deck, não do histórico
                                    # Vamos assumir que o ano do deck está próximo do ano encontrado
                                    return ano_encontrado
                    except Exception:
                        pass
        
        # Se não encontrou, tentar usar o ano atual como fallback mais inteligente
        import datetime
        ano_atual = datetime.datetime.now().year
        # Se estamos em 2026 ou depois, usar o ano atual como fallback mais razoável
        if ano_atual >= 2026:
            return ano_atual
        # Caso contrário, usar 2025 como último recurso
        return 2025
    
    def _get_year_and_month_from_deck(self, result: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        Extrai ano e mês do deck a partir do caminho ou nome do deck.
        
        Args:
            result: Resultado da tool que contém informações do deck
            
        Returns:
            Tuple (ano, mês) ou None se não conseguir extrair
        """
        import os
        
        deck_path = result.get("deck_path") or result.get("deck")
        if deck_path:
            deck_path_str = str(deck_path)
            
            # Tentar extrair ano e mês do nome do deck (ex: "NW202512" -> (2025, 12))
            # Padrão: NW + 4 dígitos (ano) + 2 dígitos (mês)
            match = re.search(r'NW(\d{4})(\d{2})', deck_path_str)
            if match:
                ano = int(match.group(1))
                mes = int(match.group(2))
                return (ano, mes)
        
        return None
    
    def _calculate_real_year(self, indice_ano_estudo: int, ano_deck: int, mes_deck: int) -> int:
        """
        Calcula o ano real baseado no índice do ano do estudo, ano e mês do deck.
        
        Para CVU:
        - Deck de dezembro: indice_ano_estudo=1 corresponde ao ano do deck (dezembro do ano)
        - Deck de janeiro: indice_ano_estudo=1 corresponde ao ano do deck (janeiro do ano)
        
        Args:
            indice_ano_estudo: Índice do ano do estudo (1, 2, 3, ...)
            ano_deck: Ano do deck (ex: 2025 para NW202512)
            mes_deck: Mês do deck (ex: 12 para NW202512)
            
        Returns:
            Ano real correspondente
        """
        # Para CVU, o indice_ano_estudo=1 corresponde ao ano do deck
        # Então: ano_real = ano_deck + (indice_ano_estudo - 1)
        return ano_deck + (indice_ano_estudo - 1)
    
    def _format_cvu_simplified_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de CVU de forma simplificada para N decks:
        - Tabela: Ano (dinâmico baseado no deck), Deck 1, Deck 2, ..., Deck N
        - Gráfico: uma linha por deck, eixo Y = CVU, eixo X = Anos
        
        Suporta análise histórica com múltiplos decks (ex: evolução de 12 meses).
        
        Nota: Para CVU, geralmente há uma única classe térmica. Se houver múltiplas,
        usa a primeira classe encontrada (priorizando a mais frequente nos dados).
        
        IMPORTANTE: Cada deck tem sua própria base de ano:
        - Deck de fevereiro (NW202502): indice_ano_estudo=1 corresponde a 2025
        - Deck de março (NW202503): indice_ano_estudo=1 corresponde a 2025
        - etc.
        """
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados estruturais de todos os decks
        decks_info = []
        all_dados_estruturais = []
        
        for deck in decks_data:
            result = deck.result
            deck_info = self._get_year_and_month_from_deck(result)
            
            if deck_info is None:
                # Fallback: tentar extrair do nome do deck
                import re
                deck_name = deck.name
                match = re.search(r'NW(\d{4})(\d{2})', deck_name)
                if match:
                    ano = int(match.group(1))
                    mes = int(match.group(2))
                    deck_info = (ano, mes)
                else:
                    # Último fallback
                    import datetime
                    ano_atual = datetime.datetime.now().year
                    deck_info = (ano_atual, 1)
            
            dados_estruturais = result.get("dados_estruturais", [])
            all_dados_estruturais.extend(dados_estruturais)
            
            decks_info.append({
                "deck": deck,
                "ano": deck_info[0],
                "mes": deck_info[1],
                "dados_estruturais": dados_estruturais,
                "display_name": deck.display_name
            })
        
        # Identificar a classe principal (mais frequente nos dados de todos os decks)
        classes_count = {}
        classe_nome_map = {}
        for record in all_dados_estruturais:
            classe = record.get("codigo_usina")
            nome_usina = record.get("nome_usina", "")
            if classe is not None:
                classes_count[classe] = classes_count.get(classe, 0) + 1
                if classe not in classe_nome_map and nome_usina:
                    classe_nome_map[classe] = nome_usina
        
        classe_principal = None
        nome_classe_principal = None
        if classes_count:
            classe_principal = max(classes_count.items(), key=lambda x: x[1])[0]
            nome_classe_principal = classe_nome_map.get(classe_principal, f"Classe {classe_principal}")
        
        # Agrupar dados por deck e indice_ano_estudo
        decks_by_indice = {}  # {deck_index: {indice_ano_estudo: valor}}
        
        for deck_idx, deck_info in enumerate(decks_info):
            deck_by_indice = {}
            for record in deck_info["dados_estruturais"]:
                classe = record.get("codigo_usina")
                if classe_principal is not None and classe != classe_principal:
                    continue
                
                indice = record.get("indice_ano_estudo")
                valor = self._sanitize_number(record.get("valor"))
                if indice is not None and valor is not None:
                    if indice not in deck_by_indice:
                        deck_by_indice[indice] = valor
            
            decks_by_indice[deck_idx] = {
                "by_indice": deck_by_indice,
                "ano": deck_info["ano"],
                "mes": deck_info["mes"],
                "display_name": deck_info["display_name"]
            }
        
        # Criar dicionário mapeando ano real -> valores de cada deck
        # Para cada deck, calcular o ano real baseado no indice_ano_estudo
        comparison_by_year = {}  # {ano_real: {deck_0: valor, deck_1: valor, ...}}
        
        for deck_idx, deck_data in decks_by_indice.items():
            ano_deck = deck_data["ano"]
            mes_deck = deck_data["mes"]
            by_indice = deck_data["by_indice"]
            
            for indice, valor in by_indice.items():
                ano_real = self._calculate_real_year(indice, ano_deck, mes_deck)
                if ano_real not in comparison_by_year:
                    comparison_by_year[ano_real] = {}
                comparison_by_year[ano_real][deck_idx] = valor
        
        # Ordenar anos
        sorted_years = sorted(comparison_by_year.keys())
        
        # Função auxiliar para arredondar
        def safe_round(value):
            if value is None:
                return None
            try:
                rounded = round(value, 2)
                if math.isnan(rounded) or math.isinf(rounded):
                    return None
                return rounded
            except (ValueError, TypeError):
                return None
        
        # Construir tabela comparativa com N colunas (uma por deck)
        comparison_table = []
        chart_labels = []
        chart_datasets = []
        
        # Inicializar datasets para o gráfico (um por deck)
        for deck_idx, deck_data in decks_by_indice.items():
            chart_datasets.append({
                "label": deck_data["display_name"],
                "data": []
            })
        
        # Processar cada ano
        for ano_real in sorted_years:
            values_by_deck = comparison_by_year[ano_real]
            
            # Construir linha da tabela
            classe_info = f"{classe_principal} - {nome_classe_principal}" if classe_principal is not None and nome_classe_principal else "N/A"
            table_row = {
                "classe_info": classe_info,
                "data": ano_real,
                "ano": ano_real,
            }
            
            # Adicionar valores de cada deck (deck_1, deck_2, ..., deck_N)
            for deck_idx in range(len(decks_info)):
                value = safe_round(values_by_deck.get(deck_idx))
                table_row[f"deck_{deck_idx + 1}"] = value
                # Adicionar ao dataset do gráfico
                chart_datasets[deck_idx]["data"].append(value)
            
            comparison_table.append(table_row)
            chart_labels.append(f"Ano {ano_real}")
        
        # Construir chart_data (N datasets, um por deck)
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": "CVU - Custo Variável Unitário",
                "x_axis": "Ano",
                "y_axis": "CVU (R$/MWh)"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_cvu_simplified(
        self,
        dados_estruturais_dec: List[Dict],
        dados_estruturais_jan: List[Dict],
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use _format_cvu_simplified_multi instead.
        Mantido para compatibilidade com código legado.
        """
        # Converter para formato novo usando DeckData
        from newave_agent.app.agents.multi_deck.formatting.base import DeckData
        
        decks_data = [
            DeckData(
                name="deck_1",
                display_name="Deck 1",
                result=result_dec,
                success=True
            ),
            DeckData(
                name="deck_2",
                display_name="Deck 2",
                result=result_jan,
                success=True
            )
        ]
        
        return self._format_cvu_simplified_multi(decks_data, "ClastValoresTool", "")
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None


class CargaComparisonFormatter(ComparisonFormatter):
    """
    Formatador para CargaMensalTool e CadicTool.
    Visualização: Gráfico multi-série (uma linha por submercado/categoria)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name in ["CargaMensalTool", "CadicTool"] and (
            "data" in result_structure or "dados_por_submercado" in result_structure
        )
    
    def get_priority(self) -> int:
        return 90
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de carga para N decks.
        """
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table",
                "deck_names": self.get_deck_names(decks_data),
                "is_multi_deck": False,
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Para CargaMensalTool e CadicTool, usar formato simplificado multi-deck
        if tool_name in ["CargaMensalTool", "CadicTool"]:
            return self._format_carga_simplified_multi(decks_data, tool_name, query)
        
        # Para outros casos, verificar se há dados_por_submercado
        if any(deck.result.get("dados_por_submercado") for deck in decks_data):
            return self._format_por_submercado_multi(decks_data, tool_name, query)
        
        # Caso padrão: formatar por período
        return self._format_por_periodo_multi(decks_data, tool_name, query)
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de carga mensal ou carga adicional.
        Para CargaMensalTool e CadicTool, usa formato simplificado (tabela + gráfico) baseado no formato de CVU.
        """
        # Para CargaMensalTool e CadicTool, usar formato simplificado (baseado no formato de CVU)
        if tool_name in ["CargaMensalTool", "CadicTool"]:
            return self._format_carga_simplified(result_dec, result_jan, tool_name, query)
        
        # Extrair dados
        data_dec = result_dec.get("data", [])
        data_jan = result_jan.get("data", [])
        
        # Se dados_por_submercado existe, usar (CargaMensalTool)
        if result_dec.get("dados_por_submercado") or result_jan.get("dados_por_submercado"):
            return self._format_por_submercado(result_dec, result_jan, tool_name, query)
        
        # Caso contrário, indexar por período e categoria
        return self._format_por_periodo(data_dec, data_jan, result_dec, result_jan, tool_name, query)
    
    def _format_por_submercado(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata quando dados estão organizados por submercado."""
        dados_por_sub_dec = result_dec.get("dados_por_submercado", {})
        dados_por_sub_jan = result_jan.get("dados_por_submercado", {})
        
        # Se não há dados_por_submercado, extrair do campo data
        if not dados_por_sub_dec and not dados_por_sub_jan:
            data_dec = result_dec.get("data", [])
            data_jan = result_jan.get("data", [])
            dados_por_sub_dec = self._group_by_submercado(data_dec)
            dados_por_sub_jan = self._group_by_submercado(data_jan)
        
        # Obter todos os submercados
        all_subs = set(dados_por_sub_dec.keys()) | set(dados_por_sub_jan.keys())
        
        # Indexar por período (ano-mês)
        chart_labels = []
        chart_datasets = []
        
        # Indexar dados de cada deck por submercado e período
        dec_indexed = {}
        jan_indexed = {}
        
        for sub in all_subs:
            sub_data_dec = dados_por_sub_dec.get(sub, {}).get("dados", [])
            sub_data_jan = dados_por_sub_jan.get(sub, {}).get("dados", [])
            
            nome_sub = dados_por_sub_dec.get(sub, {}).get("nome") or dados_por_sub_jan.get(sub, {}).get("nome", f"Subsistema {sub}")
            
            for record in sub_data_dec:
                periodo_key = self._get_period_key(record)
                if periodo_key:
                    if sub not in dec_indexed:
                        dec_indexed[sub] = {}
                    dec_indexed[sub][periodo_key] = record
                    if periodo_key not in chart_labels:
                        chart_labels.append(periodo_key)
            
            for record in sub_data_jan:
                periodo_key = self._get_period_key(record)
                if periodo_key:
                    if sub not in jan_indexed:
                        jan_indexed[sub] = {}
                    jan_indexed[sub][periodo_key] = record
                    if periodo_key not in chart_labels:
                        chart_labels.append(periodo_key)
        
        chart_labels = sorted(chart_labels)
        
        # Criar uma série por submercado para cada deck
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff"]
        sub_idx = 0
        
        for sub in sorted(all_subs):
            nome_sub = dados_por_sub_dec.get(sub, {}).get("nome") or dados_por_sub_jan.get(sub, {}).get("nome", f"Subsistema {sub}")
            color = colors[sub_idx % len(colors)]
            
            dec_values = []
            jan_values = []
            
            for periodo in chart_labels:
                dec_record = dec_indexed.get(sub, {}).get(periodo, {})
                jan_record = jan_indexed.get(sub, {}).get(periodo, {})
                
                val_dec = self._sanitize_number(dec_record.get("valor"))
                val_jan = self._sanitize_number(jan_record.get("valor"))
                
                dec_values.append(round(val_dec, 2) if val_dec is not None else None)
                jan_values.append(round(val_jan, 2) if val_jan is not None else None)
            
            chart_datasets.append({
                "label": f"{nome_sub} - Dezembro",
                "data": dec_values
            })
            chart_datasets.append({
                "label": f"{nome_sub} - Janeiro",
                "data": jan_values
            })
            
            sub_idx += 1
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Tabela resumida (média por submercado)
        summary_table = []
        for sub in sorted(all_subs):
            nome_sub = dados_por_sub_dec.get(sub, {}).get("nome") or dados_por_sub_jan.get(sub, {}).get("nome", f"Subsistema {sub}")
            
            sub_dec_data = dados_por_sub_dec.get(sub, {}).get("dados", [])
            sub_jan_data = dados_por_sub_jan.get(sub, {}).get("dados", [])
            
            valores_dec = [self._sanitize_number(r.get("valor")) for r in sub_dec_data]
            valores_jan = [self._sanitize_number(r.get("valor")) for r in sub_jan_data]
            
            valores_dec = [v for v in valores_dec if v is not None]
            valores_jan = [v for v in valores_jan if v is not None]
            
            media_dec = sum(valores_dec) / len(valores_dec) if valores_dec else None
            media_jan = sum(valores_jan) / len(valores_jan) if valores_jan else None
            
            if media_dec is not None and media_jan is not None:
                diff = media_jan - media_dec
                summary_table.append({
                    "submercado": nome_sub,
                    "deck_1_value": round(media_dec, 2),
                    "deck_2_value": round(media_jan, 2),
                    "difference": round(diff, 2),
                    "difference_percent": round((diff / media_dec * 100) if media_dec != 0 else 0, 4)
                })
        
        return {
            "comparison_table": summary_table,
            "chart_data": chart_data,
            "visualization_type": "multi_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Carga Mensal por Submercado" if tool_name == "CargaMensalTool" else "Carga Adicional por Submercado",
                "x_axis": "Período",
                "y_axis": "Carga (MWméd)"
            }
        }
    
    def _format_por_periodo(self, data_dec, data_jan, result_dec, result_jan, tool_name, query):
        """Formata quando dados não estão organizados por submercado."""
        # Indexar por período
        dec_indexed = {self._get_period_key(r): r for r in data_dec if self._get_period_key(r)}
        jan_indexed = {self._get_period_key(r): r for r in data_jan if self._get_period_key(r)}
        
        chart_labels = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        dec_values = []
        jan_values = []
        
        for periodo in chart_labels:
            dec_record = dec_indexed.get(periodo, {})
            jan_record = jan_indexed.get(periodo, {})
            
            val_dec = self._sanitize_number(dec_record.get("valor"))
            val_jan = self._sanitize_number(jan_record.get("valor"))
            
            dec_values.append(round(val_dec, 2) if val_dec is not None else None)
            jan_values.append(round(val_jan, 2) if val_jan is not None else None)
        
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {"label": "Dezembro", "data": dec_values},
                {"label": "Janeiro", "data": jan_values}
            ]
        } if chart_labels else None
        
        return {
            "comparison_table": [],
            "chart_data": chart_data,
            "visualization_type": "multi_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Comparação Temporal",
                "x_axis": "Período",
                "y_axis": "Valor"
            }
        }
    
    def _format_carga_simplified_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de carga mensal de forma simplificada para N decks:
        - Tabela: Data (ano-mês), Deck 1, Deck 2, ..., Deck N
        - Gráfico: uma linha por deck, eixo Y = Carga, eixo X = Períodos
        
        Suporta análise histórica com múltiplos decks (ex: evolução de 12 meses).
        """
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        decks_info = []
        all_periods = set()
        
        for deck in decks_data:
            result = deck.result
            data = result.get("data", [])
            
            # Se há dados_por_submercado, usar apenas o primeiro submercado (ou o filtrado)
            if result.get("dados_por_submercado"):
                dados_por_sub = result.get("dados_por_submercado", {})
                if len(dados_por_sub) == 1:
                    sub_data = next(iter(dados_por_sub.values()))
                    if isinstance(sub_data, dict) and "dados" in sub_data:
                        data = sub_data["dados"]
                elif dados_por_sub:
                    first_sub = next(iter(dados_por_sub.values()))
                    if isinstance(first_sub, dict) and "dados" in first_sub:
                        data = first_sub["dados"]
            
            # Indexar por período (ano-mês)
            deck_by_period = {}  # {periodo_key: valor}
            
            for record in data:
                periodo_key = self._get_period_key(record)
                if periodo_key:
                    valor = self._sanitize_number(record.get("valor"))
                    if valor is not None:
                        if periodo_key not in deck_by_period:
                            deck_by_period[periodo_key] = valor
                            all_periods.add(periodo_key)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "by_period": deck_by_period
            })
        
        # Ordenar períodos
        sorted_periods = sorted(all_periods)
        
        # Função auxiliar para arredondar
        def safe_round(value):
            if value is None:
                return None
            try:
                rounded = round(value, 2)
                if math.isnan(rounded) or math.isinf(rounded):
                    return None
                if rounded == int(rounded):
                    return int(rounded)
                return rounded
            except (ValueError, TypeError):
                return None
        
        # Construir tabela comparativa com N colunas (uma por deck)
        comparison_table = []
        chart_labels = []
        chart_datasets = []
        
        # Inicializar datasets para o gráfico (um por deck)
        for deck_info in decks_info:
            chart_datasets.append({
                "label": deck_info["display_name"],
                "data": []
            })
        
        # Processar cada período
        for periodo_key in sorted_periods:
            # Formatar label do período (ex: "2025-12" -> "Dez/2025")
            periodo_label = self._format_period_label(periodo_key)
            
            # Extrair ano e mês do periodo_key
            ano = None
            mes = None
            if periodo_key and "-" in periodo_key:
                try:
                    parts = periodo_key.split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, TypeError):
                    pass
            
            # Construir linha da tabela
            table_row = {
                "data": periodo_label,
                "ano": ano,
                "mes": mes,
            }
            
            # Adicionar valores de cada deck (deck_1, deck_2, ..., deck_N)
            for deck_idx, deck_info in enumerate(decks_info):
                value = safe_round(deck_info["by_period"].get(periodo_key))
                deck_key = f"deck_{deck_idx + 1}"
                table_row[deck_key] = value
                # Adicionar ao dataset do gráfico
                chart_datasets[deck_idx]["data"].append(value)
            
            # Debug: verificar se valores foram adicionados
            from newave_agent.app.config import safe_print
            safe_print(f"[CargaComparisonFormatter] Linha tabela para {periodo_key}: {list(table_row.keys())}")
            safe_print(f"[CargaComparisonFormatter] Valores: {[table_row.get(f'deck_{i+1}') for i in range(len(decks_info))]}")
            
            comparison_table.append(table_row)
            chart_labels.append(periodo_label)
        
        # Construir chart_data (N datasets, um por deck)
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Determinar título e eixo Y baseado na tool
        if tool_name == "CadicTool":
            title = "Carga Adicional"
            y_axis = "Carga Adicional (MWméd)"
        else:
            title = "Carga Mensal"
            y_axis = "Carga (MWméd)"
        
        # Debug: verificar estrutura final da tabela
        from newave_agent.app.config import safe_print
        if comparison_table:
            first_row = comparison_table[0]
            safe_print(f"[CargaComparisonFormatter] ✅ Tabela gerada - Total de linhas: {len(comparison_table)}")
            safe_print(f"[CargaComparisonFormatter] ✅ Primeira linha - Chaves: {list(first_row.keys())}")
            deck_keys = [k for k in first_row.keys() if k.startswith('deck_')]
            safe_print(f"[CargaComparisonFormatter] ✅ Colunas de deck encontradas: {deck_keys}")
            safe_print(f"[CargaComparisonFormatter] ✅ Número de decks esperado: {len(decks_data)}")
            if len(deck_keys) != len(decks_data):
                safe_print(f"[CargaComparisonFormatter] ⚠️ AVISO: Número de colunas de deck ({len(deck_keys)}) não corresponde ao número de decks ({len(decks_data)})")
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": title,
                "x_axis": "Período",
                "y_axis": y_axis
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_por_submercado_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata quando dados estão organizados por submercado para N decks."""
        # Extrair dados de todos os decks
        all_subs = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados_por_sub = result.get("dados_por_submercado", {})
            
            # Se não há dados_por_submercado, extrair do campo data
            if not dados_por_sub:
                data = result.get("data", [])
                dados_por_sub = self._group_by_submercado(data)
            
            all_subs.update(dados_por_sub.keys())
            
            # Indexar dados por submercado e período
            deck_indexed = {}  # {sub: {periodo_key: record}}
            
            for sub, sub_data in dados_por_sub.items():
                sub_records = sub_data.get("dados", []) if isinstance(sub_data, dict) else []
                if sub not in deck_indexed:
                    deck_indexed[sub] = {}
                for record in sub_records:
                    periodo_key = self._get_period_key(record)
                    if periodo_key:
                        deck_indexed[sub][periodo_key] = record
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "dados_por_sub": dados_por_sub,
                "indexed": deck_indexed
            })
        
        # Obter todos os períodos únicos
        all_periods = set()
        for deck_info in decks_info:
            for sub in all_subs:
                all_periods.update(deck_info["indexed"].get(sub, {}).keys())
        
        chart_labels = sorted(all_periods)
        
        # Criar uma série por submercado para cada deck
        chart_datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff", "#0088fe", "#00c49f", "#ffbb28", "#ff8042"]
        sub_idx = 0
        
        for sub in sorted(all_subs):
            nome_sub = None
            for deck_info in decks_info:
                sub_data = deck_info["dados_por_sub"].get(sub, {})
                if isinstance(sub_data, dict) and sub_data.get("nome"):
                    nome_sub = sub_data.get("nome")
                    break
            if not nome_sub:
                nome_sub = f"Subsistema {sub}"
            
            # Criar dataset para cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                values = []
                for periodo in chart_labels:
                    record = deck_info["indexed"].get(sub, {}).get(periodo, {})
                    val = self._sanitize_number(record.get("valor"))
                    values.append(round(val, 2) if val is not None else None)
                
                chart_datasets.append({
                    "label": f"{nome_sub} - {deck_info['display_name']}",
                    "data": values
                })
            
            sub_idx += 1
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Tabela resumida (média por submercado) com N colunas
        summary_table = []
        for sub in sorted(all_subs):
            nome_sub = None
            for deck_info in decks_info:
                sub_data = deck_info["dados_por_sub"].get(sub, {})
                if isinstance(sub_data, dict) and sub_data.get("nome"):
                    nome_sub = sub_data.get("nome")
                    break
            if not nome_sub:
                nome_sub = f"Subsistema {sub}"
            
            table_row = {"submercado": nome_sub}
            
            # Calcular média para cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                sub_data = deck_info["dados_por_sub"].get(sub, {})
                sub_records = sub_data.get("dados", []) if isinstance(sub_data, dict) else []
                valores = [self._sanitize_number(r.get("valor")) for r in sub_records]
                valores = [v for v in valores if v is not None]
                media = sum(valores) / len(valores) if valores else None
                deck_key = f"deck_{deck_idx + 1}"
                table_row[deck_key] = round(media, 2) if media is not None else None
            
            # Debug: verificar se valores foram adicionados
            from newave_agent.app.config import safe_print
            safe_print(f"[CargaComparisonFormatter] Linha tabela por submercado {nome_sub}: {list(table_row.keys())}")
            safe_print(f"[CargaComparisonFormatter] Valores: {[table_row.get(f'deck_{i+1}') for i in range(len(decks_info))]}")
            
            summary_table.append(table_row)
        
        return {
            "comparison_table": summary_table,
            "chart_data": chart_data,
            "visualization_type": "multi_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Carga Mensal por Submercado" if tool_name == "CargaMensalTool" else "Carga Adicional por Submercado",
                "x_axis": "Período",
                "y_axis": "Carga (MWméd)"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_por_periodo_multi(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata quando dados não estão organizados por submercado para N decks."""
        # Extrair dados de todos os decks
        all_periods = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            data = result.get("data", [])
            
            # Indexar por período
            deck_indexed = {}
            for record in data:
                periodo_key = self._get_period_key(record)
                if periodo_key:
                    deck_indexed[periodo_key] = record
                    all_periods.add(periodo_key)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": deck_indexed
            })
        
        chart_labels = sorted(all_periods)
        
        # Criar datasets (um por deck)
        chart_datasets = []
        for deck_info in decks_info:
            values = []
            for periodo in chart_labels:
                record = deck_info["indexed"].get(periodo, {})
                val = self._sanitize_number(record.get("valor"))
                values.append(round(val, 2) if val is not None else None)
            
            chart_datasets.append({
                "label": deck_info["display_name"],
                "data": values
            })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        return {
            "comparison_table": [],
            "chart_data": chart_data,
            "visualization_type": "multi_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Comparação Temporal",
                "x_axis": "Período",
                "y_axis": "Valor"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_carga_simplified(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de carga mensal de forma simplificada (baseado no formato de CVU):
        - Tabela: Data (ano-mês), Deck 1, Deck 2, Diferença (nominal + %)
        - Gráfico: uma linha por deck, eixo Y = Carga, eixo X = Períodos
        
        Trata corretamente meses que podem não existir em ambos os decks.
        """
        # Extrair dados - pode estar em "data" ou "dados_por_submercado"
        data_dec = result_dec.get("data", [])
        data_jan = result_jan.get("data", [])
        
        # Debug: verificar dados recebidos
        import sys
        print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - dados_dec: {len(data_dec)}, dados_jan: {len(data_jan)}", file=sys.stderr)
        if data_dec:
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - exemplo record_dec: {data_dec[0]}", file=sys.stderr)
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - keys record_dec: {list(data_dec[0].keys()) if data_dec else []}", file=sys.stderr)
        if data_jan:
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - exemplo record_jan: {data_jan[0]}", file=sys.stderr)
        
        # Se há dados_por_submercado, usar apenas o primeiro submercado (ou o filtrado)
        # (a tool já filtra por submercado quando solicitado)
        if result_dec.get("dados_por_submercado") or result_jan.get("dados_por_submercado"):
            dados_por_sub_dec = result_dec.get("dados_por_submercado", {})
            dados_por_sub_jan = result_jan.get("dados_por_submercado", {})
            
            # Se há apenas um submercado (caso comum quando filtrado), usar seus dados
            if len(dados_por_sub_dec) == 1 and len(dados_por_sub_jan) == 1:
                sub_data_dec = next(iter(dados_por_sub_dec.values()))
                sub_data_jan = next(iter(dados_por_sub_jan.values()))
                if isinstance(sub_data_dec, dict) and "dados" in sub_data_dec:
                    data_dec = sub_data_dec["dados"]
                if isinstance(sub_data_jan, dict) and "dados" in sub_data_jan:
                    data_jan = sub_data_jan["dados"]
            elif dados_por_sub_dec or dados_por_sub_jan:
                # Múltiplos submercados: usar o primeiro (ou consolidar se necessário)
                if dados_por_sub_dec:
                    first_sub_dec = next(iter(dados_por_sub_dec.values()))
                    if isinstance(first_sub_dec, dict) and "dados" in first_sub_dec:
                        data_dec = first_sub_dec["dados"]
                if dados_por_sub_jan:
                    first_sub_jan = next(iter(dados_por_sub_jan.values()))
                    if isinstance(first_sub_jan, dict) and "dados" in first_sub_jan:
                        data_jan = first_sub_jan["dados"]
        
        # Indexar por período (ano-mês)
        dec_by_period = {}  # {ano_mes: valor}
        jan_by_period = {}  # {ano_mes: valor}
        
        # Processar dados de dezembro
        import sys
        records_sem_periodo = 0
        for idx, record in enumerate(data_dec):
            periodo_key = self._get_period_key(record)
            if not periodo_key:
                records_sem_periodo += 1
                # Debug: verificar por que não encontrou período (apenas primeiros 3)
                if records_sem_periodo <= 3:
                    print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - record[{idx}] sem período: keys={list(record.keys())}, ano={record.get('ano')}, mes={record.get('mes')}, data={record.get('data')}, tipo_data={type(record.get('data'))}", file=sys.stderr)
            if periodo_key:
                valor = self._sanitize_number(record.get("valor"))
                if valor is not None:
                    # Se já existe valor para este período, manter o primeiro
                    if periodo_key not in dec_by_period:
                        dec_by_period[periodo_key] = valor
        if records_sem_periodo > 0:
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - total records sem período em dezembro: {records_sem_periodo}/{len(data_dec)}", file=sys.stderr)
        
        # Processar dados de janeiro
        for record in data_jan:
            periodo_key = self._get_period_key(record)
            if periodo_key:
                valor = self._sanitize_number(record.get("valor"))
                if valor is not None:
                    if periodo_key not in jan_by_period:
                        jan_by_period[periodo_key] = valor
        
        # Debug: verificar períodos encontrados
        import sys
        print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - períodos_dec: {len(dec_by_period)}, períodos_jan: {len(jan_by_period)}", file=sys.stderr)
        if len(dec_by_period) > 0:
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - exemplo período_dec: {list(dec_by_period.keys())[:3]}", file=sys.stderr)
        if len(jan_by_period) > 0:
            print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - exemplo período_jan: {list(jan_by_period.keys())[:3]}", file=sys.stderr)
        
        # Obter todos os períodos únicos e ordenar
        all_periods = sorted(set(list(dec_by_period.keys()) + list(jan_by_period.keys())))
        print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - total períodos únicos: {len(all_periods)}", file=sys.stderr)
        
        # Construir tabela comparativa simplificada
        comparison_table = []
        chart_labels = []
        dec_values = []
        jan_values = []
        
        for periodo_key in all_periods:
            val_dec = dec_by_period.get(periodo_key)
            val_jan = jan_by_period.get(periodo_key)
            
            # Calcular diferença
            diff = None
            diff_percent = None
            
            if val_dec is not None and val_jan is not None:
                diff = val_jan - val_dec
                diff_percent = ((val_jan - val_dec) / val_dec * 100) if val_dec != 0 else 0
            elif val_jan is not None:
                # Apenas em janeiro (adicionado)
                diff = val_jan
                diff_percent = None
            elif val_dec is not None:
                # Apenas em dezembro (removido)
                diff = -val_dec
                diff_percent = None
            
            # Formatar label do período (ex: "2025-12" -> "Dez/2025")
            periodo_label = self._format_period_label(periodo_key)
            
            # Extrair ano e mês do periodo_key (formato "2025-12")
            ano = None
            mes = None
            if periodo_key and "-" in periodo_key:
                try:
                    parts = periodo_key.split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, TypeError):
                    pass
            
            # Função auxiliar para arredondar e garantir que NaN vire None, sem decimais quando inteiro
            def safe_round(value):
                if value is None:
                    return None
                try:
                    rounded = round(value, 2)
                    # Verificar se o resultado é NaN ou Inf
                    if math.isnan(rounded) or math.isinf(rounded):
                        return None
                    # Se for número inteiro, retornar sem decimais
                    if rounded == int(rounded):
                        return int(rounded)
                    return rounded
                except (ValueError, TypeError):
                    return None
            
            # Adicionar à tabela (sem diferença/variação conforme solicitado para SISTEMA.DAT)
            table_row = {
                "data": periodo_label,  # Coluna "Data" com mês-ano formatado (ex: "Dez/2025")
                "ano": ano,  # Ano extraído do periodo_key (para detecção no frontend)
                "mes": mes,  # Mês extraído do periodo_key (para detecção no frontend)
                "deck_1": safe_round(val_dec),
                "deck_2": safe_round(val_jan),
            }
            
            # REMOVIDO: Colunas diferença e variação conforme solicitado para SISTEMA.DAT
            
            comparison_table.append(table_row)
            
            # Dados para gráfico
            chart_labels.append(periodo_label)
            dec_values.append(safe_round(val_dec))
            jan_values.append(safe_round(val_jan))
        
        # Debug: verificar chart_labels antes de criar chart_data
        import sys
        print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - chart_labels: {len(chart_labels)}, dec_values: {len(dec_values)}, jan_values: {len(jan_values)}", file=sys.stderr)
        
        # Construir chart_data (uma linha por deck - mesmo formato do CVU)
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "Dezembro 2025",
                    "data": dec_values
                },
                {
                    "label": "Janeiro 2026",
                    "data": jan_values
                }
            ]
        } if chart_labels else None
        
        print(f"[FORMATTER] [CARGA_SIMPLIFIED] {tool_name} - chart_data gerado: {chart_data is not None}", file=sys.stderr)
        
        # Determinar título e eixo Y baseado na tool
        if tool_name == "CadicTool":
            title = "Carga Adicional"
            y_axis = "Carga Adicional (MWméd)"
        else:
            title = "Carga Mensal"
            y_axis = "Carga (MWméd)"
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": title,
                "x_axis": "Período",
                "y_axis": y_axis
            }
        }
    
    def _format_period_label(self, periodo_key: str) -> str:
        """
        Formata chave de período (ex: "2025-12") para label legível (ex: "Dez/2025").
        """
        try:
            if "-" in periodo_key:
                parts = periodo_key.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = int(parts[1])
                    meses_nomes = {
                        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
                        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
                        9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
                    }
                    mes_nome = meses_nomes.get(mes, f"M{mes}")
                    return f"{mes_nome}/{ano}"
            return periodo_key
        except (ValueError, IndexError):
            return periodo_key
    
    def _group_by_submercado(self, data: List[Dict]) -> Dict[str, Dict]:
        """Agrupa dados por submercado."""
        grouped = {}
        for record in data:
            sub = record.get("codigo_submercado")
            if sub:
                if sub not in grouped:
                    grouped[sub] = {"codigo": sub, "nome": f"Subsistema {sub}", "dados": []}
                grouped[sub]["dados"].append(record)
        return grouped
    
    def _get_period_key(self, record: Dict) -> Optional[str]:
        """Obtém chave de período (ano-mês)."""
        # Tentar ano e mes primeiro
        ano = record.get("ano")
        mes = record.get("mes")
        
        # Verificar se são válidos (não None, não NaN)
        if ano is not None and mes is not None:
            try:
                # Converter para int, tratando casos onde podem ser float ou string
                ano_int = int(float(ano)) if isinstance(ano, (int, float, str)) else None
                mes_int = int(float(mes)) if isinstance(mes, (int, float, str)) else None
                if ano_int is not None and mes_int is not None:
                    return f"{ano_int:04d}-{mes_int:02d}"
            except (ValueError, TypeError):
                pass
        
        # Tentar campo data
        data = record.get("data")
        if data:
            # Se data é string ISO, extrair ano-mês
            if isinstance(data, str):
                # Formato ISO: "2025-12-01T00:00:00" ou "2025-12-01"
                if len(data) >= 7 and "-" in data:
                    return data[:7]  # YYYY-MM
            # Se data é datetime object, converter
            elif hasattr(data, 'year') and hasattr(data, 'month'):
                try:
                    return f"{data.year:04d}-{data.month:02d}"
                except (AttributeError, ValueError):
                    pass
        
        return None
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None


class VazoesComparisonFormatter(ComparisonFormatter):
    """
    Formatador para VazoesTool e DsvaguaTool.
    Visualização: Gráfico de linha temporal (séries históricas)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name in ["VazoesTool", "DsvaguaTool"]
    
    def get_priority(self) -> int:
        return 80
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de vazões para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "line_chart",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        all_periods = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            # DsvaguaTool retorna "dados", VazoesTool retorna "data"
            data = result.get("data", result.get("dados", []))
            
            # Indexar por período
            deck_indexed = {}
            for record in data:
                periodo_key = self._get_period_key(record)
                if periodo_key:
                    deck_indexed[periodo_key] = record
                    all_periods.add(periodo_key)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": deck_indexed
            })
        
        chart_labels = sorted(all_periods)
        
        # Criar datasets (um por deck)
        chart_datasets = []
        for deck_info in decks_info:
            values = []
            for periodo in chart_labels:
                record = deck_info["indexed"].get(periodo, {})
                val = self._extract_value(record)
                values.append(round(val, 2) if val is not None else None)
            
            chart_datasets.append({
                "label": deck_info["display_name"],
                "data": values
            })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Tabela comparativa resumida com N colunas
        comparison_table = []
        for periodo in chart_labels[:20]:  # Limitar a 20 períodos na tabela
            # Obter o primeiro registro disponível para extrair ano e mês
            first_record = None
            for deck_info in decks_info:
                record = deck_info["indexed"].get(periodo, {})
                if record:
                    first_record = record
                    break
            
            # Extrair ano e mês do registro ou da chave de período
            ano = None
            mes = None
            if first_record:
                ano = first_record.get("ano")
                mes = first_record.get("mes")
            
            # Se não encontrou no registro, tentar extrair da chave de período (formato "YYYY-MM")
            if ano is None and periodo and "-" in str(periodo):
                try:
                    parts = str(periodo).split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, IndexError):
                    pass
            
            # Formatar ano no formato YYYY-MM quando ambos estiverem disponíveis
            ano_formatado = None
            if ano is not None and mes is not None:
                ano_formatado = f"{int(ano):04d}-{int(mes):02d}"
            elif ano is not None:
                ano_formatado = str(int(ano))
            elif periodo and "-" in str(periodo):
                # Usar o período diretamente se já estiver no formato correto
                ano_formatado = str(periodo)
            
            table_row = {
                "periodo": periodo,
                "ano": ano_formatado if ano_formatado else ano,
                "mes": mes
            }
            
            # Adicionar valores de cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                record = deck_info["indexed"].get(periodo, {})
                val = self._extract_value(record)
                table_row[f"deck_{deck_idx + 1}"] = round(val, 2) if val is not None else None
            
            # Calcular diferença entre primeiro e último deck (se ambos tiverem valores)
            if len(decks_info) >= 2:
                val_first = self._extract_value(decks_info[0]["indexed"].get(periodo, {}))
                val_last = self._extract_value(decks_info[-1]["indexed"].get(periodo, {}))
                if val_first is not None and val_last is not None:
                    diff = val_last - val_first
                    table_row["difference"] = round(diff, 2)
                    table_row["difference_percent"] = round((diff / val_first * 100) if val_first != 0 else 0, 4)
            
            comparison_table.append(table_row)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "line_chart",
            "chart_config": {
                "type": "line",
                "title": "Vazões Históricas" if tool_name == "VazoesTool" else "Desvios de Água",
                "x_axis": "Período",
                "y_axis": "Vazão (m³/s)" if tool_name == "VazoesTool" else "Desvio (m³/s)"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de vazões ou desvios de água.
        Gráfico de linha temporal mostrando séries históricas lado a lado.
        """
        # DsvaguaTool retorna "dados", VazoesTool retorna "data"
        data_dec = result_dec.get("data", result_dec.get("dados", []))
        data_jan = result_jan.get("data", result_jan.get("dados", []))
        
        # Indexar por período
        dec_indexed = {self._get_period_key(r): r for r in data_dec if self._get_period_key(r)}
        jan_indexed = {self._get_period_key(r): r for r in data_jan if self._get_period_key(r)}
        
        chart_labels = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        dec_values = []
        jan_values = []
        
        for periodo in chart_labels:
            dec_record = dec_indexed.get(periodo, {})
            jan_record = jan_indexed.get(periodo, {})
            
            # Para VazoesTool, valor pode estar em diferentes campos
            val_dec = self._extract_value(dec_record)
            val_jan = self._extract_value(jan_record)
            
            dec_values.append(round(val_dec, 2) if val_dec is not None else None)
            jan_values.append(round(val_jan, 2) if val_jan is not None else None)
        
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {"label": "Dezembro", "data": dec_values},
                {"label": "Janeiro", "data": jan_values}
            ]
        } if chart_labels else None
        
        # Tabela comparativa resumida
        comparison_table = []
        for periodo in chart_labels[:20]:  # Limitar a 20 períodos na tabela
            dec_record = dec_indexed.get(periodo, {})
            jan_record = jan_indexed.get(periodo, {})
            
            # Extrair ano e mês do primeiro registro disponível
            first_record = dec_record if dec_record else jan_record
            ano = None
            mes = None
            if first_record:
                ano = first_record.get("ano")
                mes = first_record.get("mes")
            
            # Se não encontrou no registro, tentar extrair da chave de período (formato "YYYY-MM")
            if ano is None and periodo and "-" in str(periodo):
                try:
                    parts = str(periodo).split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, IndexError):
                    pass
            
            # Formatar ano no formato YYYY-MM quando ambos estiverem disponíveis
            ano_formatado = None
            if ano is not None and mes is not None:
                ano_formatado = f"{int(ano):04d}-{int(mes):02d}"
            elif ano is not None:
                ano_formatado = str(int(ano))
            elif periodo and "-" in str(periodo):
                # Usar o período diretamente se já estiver no formato correto
                ano_formatado = str(periodo)
            
            val_dec = self._extract_value(dec_record)
            val_jan = self._extract_value(jan_record)
            
            if val_dec is not None and val_jan is not None:
                diff = val_jan - val_dec
                comparison_table.append({
                    "periodo": periodo,
                    "ano": ano_formatado if ano_formatado else ano,
                    "mes": mes,
                    "deck_1_value": round(val_dec, 2),
                    "deck_2_value": round(val_jan, 2),
                    "difference": round(diff, 2),
                    "difference_percent": round((diff / val_dec * 100) if val_dec != 0 else 0, 4)
                })
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "line_chart",
            "chart_config": {
                "type": "line",
                "title": "Vazões Históricas" if tool_name == "VazoesTool" else "Desvios de Água",
                "x_axis": "Período",
                "y_axis": "Vazão (m³/s)" if tool_name == "VazoesTool" else "Desvio (m³/s)"
            }
        }
    
    def _get_period_key(self, record: Dict) -> Optional[str]:
        """Obtém chave de período."""
        # Tentar diferentes formatos
        ano = record.get("ano")
        mes = record.get("mes")
        if ano is not None and mes is not None:
            return f"{int(ano):04d}-{int(mes):02d}"
        
        data = record.get("data")
        if data:
            if isinstance(data, str) and len(data) >= 7:
                return data[:7]
        
        indice = record.get("indice")
        if indice is not None:
            return f"Índice {indice}"
        
        return None
    
    def _extract_value(self, record: Dict) -> Optional[float]:
        """Extrai valor numérico do registro."""
        for key in ["valor", "vazao", "desvio"]:
            if key in record:
                return self._sanitize_number(record[key])
        return None
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None


class UsinasNaoSimuladasFormatter(ComparisonFormatter):
    """
    Formatador para UsinasNaoSimuladasTool.
    Visualização: Gráfico contextual baseado em filtros da query.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        # UsinasNaoSimuladasTool retorna "dados", não "data"
        return tool_name == "UsinasNaoSimuladasTool" and ("data" in result_structure or "dados" in result_structure)
    
    def get_priority(self) -> int:
        return 85  # Prioridade maior que VazoesComparisonFormatter (80) para garantir seleção correta
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de usinas não simuladas para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [], 
                "chart_data": None, 
                "visualization_type": "line_chart",
                "chart_config": {
                    "type": "line",
                    "title": "Geração de Usinas Não Simuladas",
                    "x_axis": "Período",
                    "y_axis": "Geração (MWméd)",
                    "tool_name": "UsinasNaoSimuladasTool"  # Incluir tool_name no chart_config também
                },
                "tool_name": "UsinasNaoSimuladasTool"
            }
        
        # Analisar query para identificar filtros
        query_lower = query.lower()
        filtros = {
            "fonte": None,
            "submercado": None
        }
        
        # Identificar fonte (PCH, PCT, EOL, UFV, etc)
        fontes = ["pch", "pct", "eol", "ufv", "mmgd"]
        for fonte in fontes:
            if fonte in query_lower:
                filtros["fonte"] = fonte.upper()
                break
        
        # Identificar submercado (sudeste, sul, norte, nordeste)
        submercados_map = {
            "sudeste": 1, "sul": 2, "norte": 3, "nordeste": 4
        }
        for nome, codigo in submercados_map.items():
            if nome in query_lower:
                filtros["submercado"] = codigo
                break
        
        # Agrupar por categoria (fonte ou submercado) se não há filtro específico
        if not filtros["fonte"] and not filtros["submercado"]:
            # Agrupar por fonte
            return self._format_by_fonte_multi(decks_data, query)
        else:
            # Uma série única
            return self._format_single_series_multi(decks_data, filtros, query)
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de usinas não simuladas.
        Gera gráfico contextual baseado em filtros da query (tipo, região).
        """
        # UsinasNaoSimuladasTool retorna "dados", não "data"
        data_dec = result_dec.get("data", result_dec.get("dados", []))
        data_jan = result_jan.get("data", result_jan.get("dados", []))
        
        # Analisar query para identificar filtros
        query_lower = query.lower()
        filtros = {
            "fonte": None,
            "submercado": None
        }
        
        # Identificar fonte (PCH, PCT, EOL, UFV, etc)
        fontes = ["pch", "pct", "eol", "ufv", "mmgd"]
        for fonte in fontes:
            if fonte in query_lower:
                filtros["fonte"] = fonte.upper()
                break
        
        # Identificar submercado (sudeste, sul, norte, nordeste)
        submercados_map = {
            "sudeste": 1, "sul": 2, "norte": 3, "nordeste": 4
        }
        for nome, codigo in submercados_map.items():
            if nome in query_lower:
                filtros["submercado"] = codigo
                break
        
        # Filtrar dados conforme query
        if filtros["fonte"]:
            data_dec = [r for r in data_dec if r.get("fonte", "").upper() == filtros["fonte"]]
            data_jan = [r for r in data_jan if r.get("fonte", "").upper() == filtros["fonte"]]
        
        if filtros["submercado"]:
            data_dec = [r for r in data_dec if r.get("codigo_submercado") == filtros["submercado"]]
            data_jan = [r for r in data_jan if r.get("codigo_submercado") == filtros["submercado"]]
        
        # Agrupar por categoria (fonte ou submercado) se não há filtro específico
        if not filtros["fonte"] and not filtros["submercado"]:
            # Agrupar por fonte
            return self._format_by_fonte(data_dec, data_jan, query)
        else:
            # Uma série única
            return self._format_single_series(data_dec, data_jan, filtros, query)
    
    def _format_by_fonte(self, data_dec, data_jan, query):
        """Formata agrupando por fonte."""
        # Agrupar por fonte
        dec_by_fonte = {}
        jan_by_fonte = {}
        
        for record in data_dec:
            fonte = record.get("fonte", "Outros")
            if fonte not in dec_by_fonte:
                dec_by_fonte[fonte] = []
            dec_by_fonte[fonte].append(record)
        
        for record in data_jan:
            fonte = record.get("fonte", "Outros")
            if fonte not in jan_by_fonte:
                jan_by_fonte[fonte] = []
            jan_by_fonte[fonte].append(record)
        
        # Indexar por período
        all_fontes = set(dec_by_fonte.keys()) | set(jan_by_fonte.keys())
        chart_labels = []
        
        for fonte in all_fontes:
            for record in dec_by_fonte.get(fonte, []):
                periodo = self._get_period_key(record)
                if periodo and periodo not in chart_labels:
                    chart_labels.append(periodo)
            for record in jan_by_fonte.get(fonte, []):
                periodo = self._get_period_key(record)
                if periodo and periodo not in chart_labels:
                    chart_labels.append(periodo)
        
        chart_labels = sorted(chart_labels)
        
        # Criar série por fonte
        chart_datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00"]
        
        for idx, fonte in enumerate(sorted(all_fontes)):
            color = colors[idx % len(colors)]
            
            dec_indexed = {self._get_period_key(r): r for r in dec_by_fonte.get(fonte, []) if self._get_period_key(r)}
            jan_indexed = {self._get_period_key(r): r for r in jan_by_fonte.get(fonte, []) if self._get_period_key(r)}
            
            dec_values = []
            jan_values = []
            
            for periodo in chart_labels:
                dec_record = dec_indexed.get(periodo, {})
                jan_record = jan_indexed.get(periodo, {})
                
                val_dec = self._sanitize_number(dec_record.get("valor"))
                val_jan = self._sanitize_number(jan_record.get("valor"))
                
                dec_values.append(round(val_dec, 2) if val_dec is not None else None)
                jan_values.append(round(val_jan, 2) if val_jan is not None else None)
            
            chart_datasets.append({
                "label": f"{fonte} - Dezembro",
                "data": dec_values
            })
            chart_datasets.append({
                "label": f"{fonte} - Janeiro",
                "data": jan_values
            })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        return {
            "comparison_table": [],
            "chart_data": chart_data,
            "visualization_type": "line_chart",  # Usar line_chart padrão
            "chart_config": {
                "type": "line",
                "title": "Geração de Usinas Não Simuladas",  # Título explícito e correto
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)",
                "tool_name": "UsinasNaoSimuladasTool"  # Incluir tool_name no chart_config também
            },
            "tool_name": "UsinasNaoSimuladasTool"  # Garantir que tool_name está presente
        }
    
    def _format_single_series(self, data_dec, data_jan, filtros, query):
        """Formata uma única série (quando há filtro específico)."""
        dec_indexed = {self._get_period_key(r): r for r in data_dec if self._get_period_key(r)}
        jan_indexed = {self._get_period_key(r): r for r in data_jan if self._get_period_key(r)}
        
        chart_labels = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        dec_values = []
        jan_values = []
        
        for periodo in chart_labels:
            dec_record = dec_indexed.get(periodo, {})
            jan_record = jan_indexed.get(periodo, {})
            
            val_dec = self._sanitize_number(dec_record.get("valor"))
            val_jan = self._sanitize_number(jan_record.get("valor"))
            
            dec_values.append(round(val_dec, 2) if val_dec is not None else None)
            jan_values.append(round(val_jan, 2) if val_jan is not None else None)
        
        chart_data = {
            "labels": chart_labels,
            "datasets": [
                {"label": "Dezembro", "data": dec_values},
                {"label": "Janeiro", "data": jan_values}
            ]
        } if chart_labels else None
        
        # Criar título baseado nos filtros
        titulo_parts = []
        if filtros["fonte"]:
            titulo_parts.append(filtros["fonte"].upper())
        if filtros["submercado"]:
            sub_nomes = {1: "Sudeste", 2: "Sul", 3: "Norte", 4: "Nordeste"}
            titulo_parts.append(sub_nomes.get(filtros["submercado"], f"Subsistema {filtros['submercado']}"))
        titulo = " - ".join(titulo_parts) if titulo_parts else "Geração de Usinas Não Simuladas"
        
        return {
            "comparison_table": [],
            "chart_data": chart_data,
            "visualization_type": "line_chart",  # Usar line_chart padrão
            "chart_config": {
                "type": "line",
                "title": titulo if titulo else "Geração de Usinas Não Simuladas",  # Título explícito e correto
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)",
                "tool_name": "UsinasNaoSimuladasTool"  # Incluir tool_name no chart_config também
            },
            "tool_name": "UsinasNaoSimuladasTool"  # Garantir que tool_name está presente
        }
    
    def _format_by_fonte_multi(self, decks_data: List[DeckData], query: str):
        """Formata agrupando por fonte para N decks."""
        # Extrair dados de todos os decks
        all_fontes = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            # UsinasNaoSimuladasTool retorna "dados", não "data"
            data = result.get("data", result.get("dados", []))
            
            # Agrupar por fonte
            deck_by_fonte = {}
            for record in data:
                fonte = record.get("fonte", "Outros")
                if fonte not in deck_by_fonte:
                    deck_by_fonte[fonte] = []
                deck_by_fonte[fonte].append(record)
                all_fontes.add(fonte)
            
            # Indexar por período para cada fonte
            deck_indexed = {}  # {fonte: {periodo: record}}
            for fonte, records in deck_by_fonte.items():
                deck_indexed[fonte] = {}
                for record in records:
                    periodo = self._get_period_key(record)
                    if periodo:
                        deck_indexed[fonte][periodo] = record
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "by_fonte": deck_by_fonte,
                "indexed": deck_indexed
            })
        
        # Obter todos os períodos únicos
        all_periods = set()
        for deck_info in decks_info:
            for fonte in all_fontes:
                all_periods.update(deck_info["indexed"].get(fonte, {}).keys())
        
        chart_labels = sorted(all_periods)
        
        # Criar série por fonte para cada deck
        chart_datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff", "#0088fe", "#00c49f", "#ffbb28", "#ff8042"]
        
        for idx, fonte in enumerate(sorted(all_fontes)):
            color = colors[idx % len(colors)]
            
            # Criar dataset para cada deck
            for deck_info in decks_info:
                fonte_indexed = deck_info["indexed"].get(fonte, {})
                values = []
                for periodo in chart_labels:
                    record = fonte_indexed.get(periodo, {})
                    val = self._sanitize_number(record.get("valor"))
                    values.append(round(val, 2) if val is not None else None)
                
                chart_datasets.append({
                    "label": f"{fonte} - {deck_info['display_name']}",
                    "data": values
                })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Criar tabela de comparação (agrupada por fonte)
        comparison_table = []
        for periodo in chart_labels[:20]:  # Limitar a 20 períodos na tabela
            # Extrair ano e mês do período
            ano = None
            mes = None
            if periodo and "-" in str(periodo):
                try:
                    parts = str(periodo).split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, IndexError):
                    pass
            
            # Formatar ano no formato YYYY-MM
            ano_formatado = None
            if ano is not None and mes is not None:
                ano_formatado = f"{int(ano):04d}-{int(mes):02d}"
            elif periodo and "-" in str(periodo):
                ano_formatado = str(periodo)
            
            table_row = {
                "periodo": periodo,
                "ano": ano_formatado if ano_formatado else ano,
                "mes": mes
            }
            
            # Adicionar valores de cada fonte para cada deck
            for fonte in sorted(all_fontes):
                for deck_idx, deck_info in enumerate(decks_info):
                    fonte_indexed = deck_info["indexed"].get(fonte, {})
                    record = fonte_indexed.get(periodo, {})
                    val = self._sanitize_number(record.get("valor"))
                    # Criar coluna combinada: fonte_deck_idx
                    col_key = f"{fonte}_deck_{deck_idx + 1}"
                    table_row[col_key] = round(val, 2) if val is not None else None
            
            comparison_table.append(table_row)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "line_chart",  # Usar line_chart padrão para garantir que não use componente CVU
            "chart_config": {
                "type": "line",
                "title": "Geração de Usinas Não Simuladas",  # Título explícito e correto
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)",
                "tool_name": "UsinasNaoSimuladasTool"  # Incluir tool_name no chart_config também
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2,
            "tool_name": "UsinasNaoSimuladasTool"  # Garantir que tool_name está presente
        }
    
    def _format_single_series_multi(self, decks_data: List[DeckData], filtros: Dict, query: str):
        """Formata uma única série (quando há filtro específico) para N decks."""
        # Extrair dados de todos os decks
        all_periods = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            # UsinasNaoSimuladasTool retorna "dados", não "data"
            data = result.get("data", result.get("dados", []))
            
            # Filtrar dados conforme filtros
            filtered_data = data
            if filtros["fonte"]:
                filtered_data = [r for r in filtered_data if r.get("fonte", "").upper() == filtros["fonte"]]
            if filtros["submercado"]:
                filtered_data = [r for r in filtered_data if r.get("codigo_submercado") == filtros["submercado"]]
            
            # Indexar por período
            deck_indexed = {}
            for record in filtered_data:
                periodo = self._get_period_key(record)
                if periodo:
                    deck_indexed[periodo] = record
                    all_periods.add(periodo)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": deck_indexed
            })
        
        chart_labels = sorted(all_periods)
        
        # Criar datasets (um por deck)
        chart_datasets = []
        for deck_info in decks_info:
            values = []
            for periodo in chart_labels:
                record = deck_info["indexed"].get(periodo, {})
                val = self._sanitize_number(record.get("valor"))
                values.append(round(val, 2) if val is not None else None)
            
            chart_datasets.append({
                "label": deck_info["display_name"],
                "data": values
            })
        
        chart_data = {
            "labels": chart_labels,
            "datasets": chart_datasets
        } if chart_labels else None
        
        # Criar tabela de comparação
        comparison_table = []
        for periodo in chart_labels[:20]:  # Limitar a 20 períodos na tabela
            # Obter o primeiro registro disponível para extrair ano e mês
            first_record = None
            for deck_info in decks_info:
                record = deck_info["indexed"].get(periodo, {})
                if record:
                    first_record = record
                    break
            
            # Extrair ano e mês do registro ou da chave de período
            ano = None
            mes = None
            if first_record:
                ano = first_record.get("ano")
                mes = first_record.get("mes")
            
            # Se não encontrou no registro, tentar extrair da chave de período (formato "YYYY-MM")
            if ano is None and periodo and "-" in str(periodo):
                try:
                    parts = str(periodo).split("-")
                    if len(parts) >= 2:
                        ano = int(parts[0])
                        mes = int(parts[1])
                except (ValueError, IndexError):
                    pass
            
            # Formatar ano no formato YYYY-MM quando ambos estiverem disponíveis
            ano_formatado = None
            if ano is not None and mes is not None:
                ano_formatado = f"{int(ano):04d}-{int(mes):02d}"
            elif ano is not None:
                ano_formatado = str(int(ano))
            elif periodo and "-" in str(periodo):
                ano_formatado = str(periodo)
            
            table_row = {
                "periodo": periodo,
                "ano": ano_formatado if ano_formatado else ano,
                "mes": mes
            }
            
            # Adicionar valores de cada deck
            for deck_idx, deck_info in enumerate(decks_info):
                record = deck_info["indexed"].get(periodo, {})
                val = self._sanitize_number(record.get("valor"))
                table_row[f"deck_{deck_idx + 1}"] = round(val, 2) if val is not None else None
            
            # Calcular diferença entre primeiro e último deck (se ambos tiverem valores)
            if len(decks_info) >= 2:
                val_first = self._sanitize_number(decks_info[0]["indexed"].get(periodo, {}).get("valor"))
                val_last = self._sanitize_number(decks_info[-1]["indexed"].get(periodo, {}).get("valor"))
                if val_first is not None and val_last is not None:
                    diff = val_last - val_first
                    table_row["difference"] = round(diff, 2)
                    table_row["difference_percent"] = round((diff / val_first * 100) if val_first != 0 else 0, 4)
            
            comparison_table.append(table_row)
        
        # Criar título baseado nos filtros
        titulo_parts = []
        if filtros["fonte"]:
            titulo_parts.append(filtros["fonte"].upper())
        if filtros["submercado"]:
            sub_nomes = {1: "Sudeste", 2: "Sul", 3: "Norte", 4: "Nordeste"}
            titulo_parts.append(sub_nomes.get(filtros["submercado"], f"Subsistema {filtros['submercado']}"))
        titulo = " - ".join(titulo_parts) if titulo_parts else "Geração de Usinas Não Simuladas"
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "line_chart",  # Usar line_chart padrão para garantir que não use componente CVU
            "chart_config": {
                "type": "line",
                "title": titulo if titulo else "Geração de Usinas Não Simuladas",  # Título explícito e correto
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)",
                "tool_name": "UsinasNaoSimuladasTool"  # Incluir tool_name no chart_config também
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2,
            "tool_name": "UsinasNaoSimuladasTool"  # Garantir que tool_name está presente
        }
    
    def _get_period_key(self, record: Dict) -> Optional[str]:
        """Obtém chave de período."""
        ano = record.get("ano")
        mes = record.get("mes")
        if ano is not None and mes is not None:
            return f"{int(ano):04d}-{int(mes):02d}"
        data = record.get("data")
        if data and isinstance(data, str) and len(data) >= 7:
            return data[:7]
        return None
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None


class LimitesIntercambioComparisonFormatter(ComparisonFormatter):
    """
    Formatador para LimitesIntercambioTool.
    Visualização: Tabelas comparativas separadas por par de submercados.
    Todos os registros são incluídos, independente de serem iguais ou não.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "LimitesIntercambioTool" and (
            "data" in result_structure or "stats_por_par" in result_structure
        )
    
    def get_priority(self) -> int:
        return 85  # Prioridade alta - específico para limites de intercâmbio
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de limites de intercâmbio para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "chart_data": None,
                "charts_by_par": {},
                "visualization_type": "limites_intercambio",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        all_pares = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            data = result.get("data", [])
            
            # Indexar dados por (par, sentido, período)
            deck_indexed = self._index_by_par_sentido_periodo(data)
            all_pares.update(deck_indexed.keys())
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "result": result,
                "indexed": deck_indexed
            })
        
        # Detectar se a query especifica um par específico
        par_filtrado = None
        if decks_info:
            par_filtrado = self._extract_par_from_query(query, decks_info[0]["result"], decks_info[-1]["result"] if len(decks_info) > 1 else decks_info[0]["result"])
        
        # Filtrar pares se necessário
        if par_filtrado is not None:
            pares_filtrados = set()
            for par_key in all_pares:
                parts = par_key.split("-")
                if len(parts) >= 2:
                    sub_de_key = parts[0]
                    sub_para_key = parts[1]
                    sentido_key = parts[2] if len(parts) >= 3 else None
                    
                    if len(par_filtrado) == 2:
                        if str(par_filtrado[0]) == sub_de_key and str(par_filtrado[1]) == sub_para_key:
                            pares_filtrados.add(par_key)
                    elif len(par_filtrado) == 3:
                        if (str(par_filtrado[0]) == sub_de_key and 
                            str(par_filtrado[1]) == sub_para_key and
                            sentido_key is not None and str(par_filtrado[2]) == sentido_key):
                            pares_filtrados.add(par_key)
            
            if pares_filtrados:
                all_pares = pares_filtrados
        
        # Construir tabela comparativa e charts_by_par
        comparison_table = []
        charts_by_par = {}
        
        for par_key in sorted(all_pares):
            # Extrair informações do par_key
            parts = par_key.split("-")
            if len(parts) >= 3:
                sub_de = parts[0]
                sub_para = parts[1]
                sentido = int(parts[2])
                
                # Obter nomes dos submercados
                nome_de = self._get_submercado_nome(sub_de, decks_info[0]["result"], decks_info[-1]["result"] if len(decks_info) > 1 else decks_info[0]["result"])
                nome_para = self._get_submercado_nome(sub_para, decks_info[0]["result"], decks_info[-1]["result"] if len(decks_info) > 1 else decks_info[0]["result"])
                sentido_label = "Mínimo Obrigatório" if sentido == 1 else "Máximo"
                par_label = f"{nome_de} → {nome_para}"
                
                # Obter todos os períodos únicos para este par (de todos os decks)
                all_periodos = set()
                for deck_info in decks_info:
                    par_records = deck_info["indexed"].get(par_key, {})
                    all_periodos.update(par_records.keys())
                
                all_periodos = sorted(all_periodos)
                
                # Construir dados do gráfico para este par (N datasets, um por deck)
                par_datasets = []
                for deck_info in decks_info:
                    par_records = deck_info["indexed"].get(par_key, {})
                    par_values = []
                    for periodo in all_periodos:
                        record = par_records.get(periodo, {})
                        val = self._sanitize_number(record.get("valor"))
                        par_values.append(self._safe_round(val))
                    par_datasets.append({
                        "label": deck_info["display_name"],
                        "data": par_values
                    })
                
                # Labels formatados para o gráfico
                par_labels = [self._format_period_label(periodo) for periodo in all_periodos]
                
                # Criar chart_data para este par
                par_chart_data = {
                    "labels": par_labels,
                    "datasets": par_datasets
                } if all_periodos else None
                
                charts_by_par[par_key] = {
                    "par": par_label,
                    "sentido": sentido_label,
                    "chart_data": par_chart_data,
                    "chart_config": {
                        "type": "line",
                        "title": f"{par_label} - {sentido_label}",
                        "x_axis": "Período",
                        "y_axis": "Limite (MW)"
                    }
                }
                
                # Construir tabela (todos os períodos, com N colunas)
                for periodo in all_periodos:
                    periodo_formatted = self._format_period_label(periodo)
                    
                    table_row = {
                        "data": periodo_formatted,
                        "par_key": par_key,
                        "par": par_label,
                        "sentido": sentido_label,
                    }
                    
                    # Adicionar valores de cada deck
                    for deck_idx, deck_info in enumerate(decks_info):
                        par_records = deck_info["indexed"].get(par_key, {})
                        record = par_records.get(periodo, {})
                        val = self._sanitize_number(record.get("valor"))
                        deck_key = f"deck_{deck_idx + 1}"
                        table_row[deck_key] = self._safe_round(val)
                    
                    # Debug: verificar se valores foram adicionados
                    from newave_agent.app.config import safe_print
                    if len(comparison_table) < 3:  # Log apenas nas primeiras 3 linhas
                        safe_print(f"[LimitesIntercambioFormatter] Linha tabela para {par_key} - {periodo}: {list(table_row.keys())}")
                        safe_print(f"[LimitesIntercambioFormatter] Valores: {[table_row.get(f'deck_{i+1}') for i in range(len(decks_info))]}")
                    
                    comparison_table.append(table_row)
        
        # Resumo
        pares_afetados = len(set(row["par_key"] for row in comparison_table)) if comparison_table else 0
        
        # Debug: verificar estrutura final da tabela
        from newave_agent.app.config import safe_print
        if comparison_table:
            first_row = comparison_table[0]
            safe_print(f"[LimitesIntercambioFormatter] ✅ Tabela gerada - Total de linhas: {len(comparison_table)}")
            safe_print(f"[LimitesIntercambioFormatter] ✅ Primeira linha - Chaves: {list(first_row.keys())}")
            deck_keys = [k for k in first_row.keys() if k.startswith('deck_')]
            safe_print(f"[LimitesIntercambioFormatter] ✅ Colunas de deck encontradas: {deck_keys}")
            safe_print(f"[LimitesIntercambioFormatter] ✅ Número de decks esperado: {len(decks_data)}")
            if len(deck_keys) != len(decks_data):
                safe_print(f"[LimitesIntercambioFormatter] ⚠️ AVISO: Número de colunas de deck ({len(deck_keys)}) não corresponde ao número de decks ({len(decks_data)})")
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "charts_by_par": charts_by_par,
            "visualization_type": "limites_intercambio",
            "summary": {
                "total_registros": len(comparison_table),
                "pares_afetados": pares_afetados
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str,
        deck_1_name: Optional[str] = None,
        deck_2_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formata comparação de limites de intercâmbio.
        Agrupa por par de submercados e sentido, mostrando todos os registros.
        Se a query especificar um par específico, mostra apenas esse par.
        
        Args:
            result_dec: Resultado completo da tool para deck 1
            result_jan: Resultado completo da tool para deck 2
            tool_name: Nome da tool usada
            query: Query original do usuário
            deck_1_name: Nome do deck 1 (opcional, padrão: "Deck 1")
            deck_2_name: Nome do deck 2 (opcional, padrão: "Deck 2")
        """
        # Usar nomes fornecidos ou fallback genérico
        deck_1_label = deck_1_name or "Deck 1"
        deck_2_label = deck_2_name or "Deck 2"
        
        data_dec = result_dec.get("data", [])
        data_jan = result_jan.get("data", [])
        
        if not data_dec and not data_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "table_with_line_chart"
            }
        
        # Indexar dados por (par, sentido, período)
        dec_indexed = self._index_by_par_sentido_periodo(data_dec)
        jan_indexed = self._index_by_par_sentido_periodo(data_jan)
        
        # Obter todos os pares únicos
        all_pares = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        # ETAPA NOVA: Detectar se a query especifica um par específico
        from newave_agent.app.config import safe_print
        safe_print(f"[FORMATTER] [DEBUG] format_comparison - Query recebida: '{query}'")
        safe_print(f"[FORMATTER] [DEBUG] format_comparison - Total de pares encontrados antes do filtro: {len(all_pares)}")
        for par_key in sorted(all_pares):
            safe_print(f"[FORMATTER] [DEBUG]   Par encontrado: {par_key}")
        
        par_filtrado = self._extract_par_from_query(query, result_dec, result_jan)
        safe_print(f"[FORMATTER] [DEBUG] format_comparison - Par filtrado retornado: {par_filtrado}")
        
        # Se um par específico foi detectado, filtrar apenas esse par
        if par_filtrado is not None:
            # par_filtrado é uma tupla (sub_de, sub_para) ou (sub_de, sub_para, sentido)
            # Filtrar all_pares para incluir apenas os que correspondem ao par detectado
            safe_print(f"[FORMATTER] [DEBUG] format_comparison - Filtrando pares com: {par_filtrado}")
            pares_filtrados = set()
            for par_key in all_pares:
                parts = par_key.split("-")
                if len(parts) >= 2:
                    sub_de_key = parts[0]
                    sub_para_key = parts[1]
                    sentido_key = parts[2] if len(parts) >= 3 else None
                    
                    safe_print(f"[FORMATTER] [DEBUG]   Verificando par_key '{par_key}': sub_de={sub_de_key}, sub_para={sub_para_key}, sentido={sentido_key}")
                    
                    # Verificar se corresponde ao par filtrado
                    if len(par_filtrado) == 2:
                        # Apenas sub_de e sub_para foram especificados
                        if str(par_filtrado[0]) == sub_de_key and str(par_filtrado[1]) == sub_para_key:
                            safe_print(f"[FORMATTER] [DEBUG]     ✅ Par corresponde (sem sentido)")
                            pares_filtrados.add(par_key)
                        else:
                            safe_print(f"[FORMATTER] [DEBUG]     ❌ Par não corresponde")
                    elif len(par_filtrado) == 3:
                        # sub_de, sub_para e sentido foram especificados
                        if (str(par_filtrado[0]) == sub_de_key and 
                            str(par_filtrado[1]) == sub_para_key and
                            sentido_key is not None and str(par_filtrado[2]) == sentido_key):
                            safe_print(f"[FORMATTER] [DEBUG]     ✅ Par corresponde (com sentido)")
                            pares_filtrados.add(par_key)
                        else:
                            safe_print(f"[FORMATTER] [DEBUG]     ❌ Par não corresponde")
            
            safe_print(f"[FORMATTER] [DEBUG] format_comparison - Pares filtrados encontrados: {len(pares_filtrados)}")
            for par_key in sorted(pares_filtrados):
                safe_print(f"[FORMATTER] [DEBUG]   Par filtrado: {par_key}")
            
            if pares_filtrados:
                all_pares = pares_filtrados
                safe_print(f"[FORMATTER] [DEBUG] format_comparison - Usando {len(all_pares)} pares filtrados")
            else:
                safe_print(f"[FORMATTER] [DEBUG] format_comparison - ⚠️ Nenhum par correspondeu ao filtro, usando todos os pares")
        
        # Construir tabela comparativa (todos os registros) e charts_by_par
        comparison_table = []
        charts_by_par = {}
        
        for par_key in sorted(all_pares):
            dec_records = dec_indexed.get(par_key, {})
            jan_records = jan_indexed.get(par_key, {})
            
            # Extrair informações do par_key: "sub_de-sub_para-sentido"
            parts = par_key.split("-")
            if len(parts) >= 3:
                sub_de = parts[0]
                sub_para = parts[1]
                sentido = int(parts[2])
                
                # Obter nomes dos submercados
                nome_de = self._get_submercado_nome(sub_de, result_dec, result_jan)
                nome_para = self._get_submercado_nome(sub_para, result_dec, result_jan)
                sentido_label = "Mínimo Obrigatório" if sentido == 1 else "Máximo"
                par_label = f"{nome_de} → {nome_para}"
                
                # Obter todos os períodos únicos para este par
                all_periodos = sorted(set(dec_records.keys()) | set(jan_records.keys()))
                
                # Construir dados do gráfico e tabela para este par (incluir TODOS os períodos)
                par_dec_values = []
                par_jan_values = []
                par_labels = []  # Labels formatados para o gráfico
                
                for periodo in all_periodos:
                    dec_record = dec_records.get(periodo, {})
                    jan_record = jan_records.get(periodo, {})
                    
                    val_dec = self._sanitize_number(dec_record.get("valor"))
                    val_jan = self._sanitize_number(jan_record.get("valor"))
                    
                    # Dados para gráfico (todos os períodos)
                    par_dec_values.append(self._safe_round(val_dec))
                    par_jan_values.append(self._safe_round(val_jan))
                    
                    # Formatar período como mês-ano (ex: "Dez/2025") para labels do gráfico
                    periodo_formatted = self._format_period_label(periodo)
                    par_labels.append(periodo_formatted)
                    
                    # Incluir TODOS os registros na tabela, independente de serem iguais ou não
                    periodo_formatted_table = self._format_period_label(periodo)
                    
                    comparison_table.append({
                        "data": periodo_formatted_table,  # Formato mês-ano
                        "par_key": par_key,
                        "par": par_label,
                        "sentido": sentido_label,
                        "deck_1": self._safe_round(val_dec),
                        "deck_2": self._safe_round(val_jan),
                    })
                
                # Criar chart_data para este par (usar labels formatados)
                par_chart_data = {
                    "labels": par_labels,  # Usar labels formatados (mês/ano)
                    "datasets": [
                        {
                            "label": deck_1_label,
                            "data": par_dec_values
                        },
                        {
                            "label": deck_2_label,
                            "data": par_jan_values
                        }
                    ]
                } if all_periodos else None
                
                charts_by_par[par_key] = {
                    "par": par_label,
                    "sentido": sentido_label,
                    "chart_data": par_chart_data,
                    "chart_config": {
                        "type": "line",
                        "title": f"{par_label} - {sentido_label}",
                        "x_axis": "Período",
                        "y_axis": "Limite (MW)"
                    }
                }
        
        # Resumo
        pares_afetados = len(set(row["par_key"] for row in comparison_table)) if comparison_table else 0
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,  # Não usar chart_data único, usar charts_by_par
            "charts_by_par": charts_by_par,
            "visualization_type": "limites_intercambio",
            "summary": {
                "total_registros": len(comparison_table),
                "pares_afetados": pares_afetados
            }
        }
    
    def _index_by_par_sentido_periodo(self, data: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """
        Indexa dados por (submercado_de, submercado_para, sentido) e depois por período.
        Retorna: {par_key: {periodo: record}}
        """
        indexed = {}
        
        for record in data:
            sub_de = record.get("submercado_de")
            sub_para = record.get("submercado_para")
            sentido = record.get("sentido")
            
            if sub_de is not None and sub_para is not None and sentido is not None:
                par_key = f"{sub_de}-{sub_para}-{sentido}"
                
                periodo = self._get_period_key(record)
                if periodo:
                    if par_key not in indexed:
                        indexed[par_key] = {}
                    indexed[par_key][periodo] = record
        
        return indexed
    
    def _get_period_key(self, record: Dict) -> Optional[str]:
        """Obtém chave de período no formato YYYY-MM."""
        # Tentar ano e mes primeiro
        ano = record.get("ano")
        mes = record.get("mes")
        
        if ano is not None and mes is not None:
            try:
                ano_int = int(float(ano)) if isinstance(ano, (int, float, str)) else None
                mes_int = int(float(mes)) if isinstance(mes, (int, float, str)) else None
                if ano_int is not None and mes_int is not None:
                    return f"{ano_int:04d}-{mes_int:02d}"
            except (ValueError, TypeError):
                pass
        
        # Tentar campo data
        data = record.get("data")
        if data:
            if isinstance(data, str):
                # Formato ISO: "2025-01-01T00:00:00" ou "2025-01-01"
                if len(data) >= 7 and "-" in data:
                    return data[:7]  # YYYY-MM
            elif hasattr(data, 'year') and hasattr(data, 'month'):
                try:
                    return f"{data.year:04d}-{data.month:02d}"
                except (AttributeError, ValueError):
                    pass
        
        # Tentar ano_mes se existir
        ano_mes = record.get("ano_mes")
        if ano_mes:
            if isinstance(ano_mes, str) and len(ano_mes) >= 7:
                return ano_mes[:7]  # YYYY-MM
        
        return None
    
    def _get_submercado_nome(self, codigo: str, result_dec: Dict, result_jan: Dict) -> str:
        """Obtém nome do submercado a partir do código."""
        # Tentar obter dos dados
        for result in [result_dec, result_jan]:
            data = result.get("data", [])
            for record in data:
                if str(record.get("submercado_de")) == str(codigo):
                    nome = record.get("nome_submercado_de")
                    if nome:
                        return nome
                if str(record.get("submercado_para")) == str(codigo):
                    nome = record.get("nome_submercado_para")
                    if nome:
                        return nome
        
        # Fallback: usar código
        return f"Subsistema {codigo}"
    
    def _format_period_label(self, periodo_key: str) -> str:
        """
        Formata chave de período (ex: "2025-12") para label legível (ex: "12/2025").
        """
        try:
            if "-" in periodo_key:
                parts = periodo_key.split("-")
                if len(parts) == 2:
                    ano = parts[0]
                    mes = int(parts[1])
                    return f"{mes:02d}/{ano}"
            return periodo_key
        except (ValueError, IndexError):
            return periodo_key
    
    def _safe_round(self, value) -> Optional[float]:
        """Arredonda valor com tratamento de NaN/None, sem decimais quando inteiro."""
        if value is None:
            return None
        try:
            rounded = round(value, 2)
            # Verificar se o resultado é NaN ou Inf
            if math.isnan(rounded) or math.isinf(rounded):
                return None
            # Se for número inteiro, retornar sem decimais
            if rounded == int(rounded):
                return int(rounded)
            return rounded
        except (ValueError, TypeError):
            return None
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _extract_par_from_query(self, query: str, result_dec: Dict[str, Any], result_jan: Dict[str, Any]) -> Optional[Tuple]:
        """
        Extrai par de submercados (sub_de, sub_para) ou (sub_de, sub_para, sentido) da query.
        Retorna None se nenhum par específico for detectado.
        
        Args:
            query: Query do usuário
            result_dec: Resultado do deck 1 (para obter nomes de submercados)
            result_jan: Resultado do deck 2 (para obter nomes de submercados)
            
        Returns:
            Tupla (sub_de, sub_para) ou (sub_de, sub_para, sentido) ou None
        """
        from newave_agent.app.config import safe_print
        
        query_lower = query.lower()
        safe_print(f"[FORMATTER] [DEBUG] _extract_par_from_query - Query original: '{query}'")
        safe_print(f"[FORMATTER] [DEBUG] _extract_par_from_query - Query lower: '{query_lower}'")
        
        # Obter lista de submercados disponíveis dos resultados
        subsistemas_disponiveis = []
        for result in [result_dec, result_jan]:
            data = result.get("data", [])
            safe_print(f"[FORMATTER] [DEBUG] Processando {len(data)} registros de dados")
            for record in data:
                sub_de = record.get("submercado_de")
                nome_de = record.get("nome_submercado_de")
                if sub_de is not None and nome_de:
                    subsistemas_disponiveis.append({
                        'codigo': int(sub_de) if isinstance(sub_de, (int, float, str)) else None,
                        'nome': str(nome_de).strip()
                    })
                sub_para = record.get("submercado_para")
                nome_para = record.get("nome_submercado_para")
                if sub_para is not None and nome_para:
                    subsistemas_disponiveis.append({
                        'codigo': int(sub_para) if isinstance(sub_para, (int, float, str)) else None,
                        'nome': str(nome_para).strip()
                    })
        
        # Remover duplicatas
        seen = set()
        subsistemas_unicos = []
        for s in subsistemas_disponiveis:
            if s['codigo'] is not None:
                key = (s['codigo'], s['nome'])
                if key not in seen:
                    seen.add(key)
                    subsistemas_unicos.append(s)
        
        safe_print(f"[FORMATTER] [DEBUG] Subsistemas únicos encontrados: {len(subsistemas_unicos)}")
        for s in subsistemas_unicos:
            safe_print(f"[FORMATTER] [DEBUG]   - Código {s['codigo']}: '{s['nome']}'")
        
        if not subsistemas_unicos:
            safe_print(f"[FORMATTER] [DEBUG] Nenhum subsistema encontrado, retornando None")
            return None
        
        # ETAPA 1: Tentar extrair números explícitos
        patterns = [
            r'subsistema\s*(\d+)\s*(?:para|->|→)\s*subsistema\s*(\d+)',
            r'submercado\s*(\d+)\s*(?:para|->|→)\s*submercado\s*(\d+)',
            r'(\d+)\s*(?:para|->|→)\s*(\d+)',
            r'entre\s*subsistema\s*(\d+)\s*e\s*subsistema\s*(\d+)',
            r'entre\s*submercado\s*(\d+)\s*e\s*submercado\s*(\d+)',
        ]
        
        safe_print(f"[FORMATTER] [DEBUG] ETAPA 1: Tentando padrões numéricos...")
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, query_lower)
            if match:
                safe_print(f"[FORMATTER] [DEBUG]   Padrão {i+1} '{pattern}' encontrou match: {match.groups()}")
                try:
                    sub_de = int(match.group(1))
                    sub_para = int(match.group(2))
                    codigos_validos = [s['codigo'] for s in subsistemas_unicos if s['codigo'] is not None]
                    safe_print(f"[FORMATTER] [DEBUG]   Códigos extraídos: {sub_de} -> {sub_para}")
                    safe_print(f"[FORMATTER] [DEBUG]   Códigos válidos disponíveis: {codigos_validos}")
                    if sub_de in codigos_validos and sub_para in codigos_validos:
                        # Verificar se há filtro de sentido
                        sentido = None
                        if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                            sentido = 1
                        elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                            sentido = 0
                        
                        if sentido is not None:
                            safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par com sentido: ({sub_de}, {sub_para}, {sentido})")
                            return (sub_de, sub_para, sentido)
                        safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par sem sentido: ({sub_de}, {sub_para})")
                        return (sub_de, sub_para)
                    else:
                        safe_print(f"[FORMATTER] [DEBUG]   Códigos não estão na lista de válidos")
                except (ValueError, IndexError) as e:
                    safe_print(f"[FORMATTER] [DEBUG]   Erro ao processar match: {e}")
                    continue
            else:
                safe_print(f"[FORMATTER] [DEBUG]   Padrão {i+1} '{pattern}' não encontrou match")
        
        # ETAPA 2: Buscar por nomes de submercados
        # Ordenar por tamanho do nome (mais específico primeiro)
        subsistemas_ordenados = sorted(subsistemas_unicos, key=lambda x: len(x['nome']), reverse=True)
        safe_print(f"[FORMATTER] [DEBUG] ETAPA 2: Buscando por nomes de submercados...")
        safe_print(f"[FORMATTER] [DEBUG]   Subsistemas ordenados (por tamanho de nome):")
        for s in subsistemas_ordenados:
            safe_print(f"[FORMATTER] [DEBUG]     - '{s['nome']}' (código {s['codigo']})")
        
        sub_de = None
        sub_para = None
        
        # Padrão especial: "entre X e Y" (ex: "entre sudeste e norte")
        pattern_entre = re.search(r'entre\s+([^e]+?)\s+e\s+([^e]+?)(?:\s|$|,|\.)', query_lower)
        if pattern_entre:
            nome_1 = pattern_entre.group(1).strip()
            nome_2 = pattern_entre.group(2).strip()
            safe_print(f"[FORMATTER] [DEBUG]   Padrão 'entre X e Y' encontrado: '{nome_1}' e '{nome_2}'")
            
            # Buscar submercados que correspondem aos nomes
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_1:
                    sub_de = subsistema['codigo']
                    safe_print(f"[FORMATTER] [DEBUG]     ✅ Origem encontrada: '{subsistema['nome']}' (código {sub_de}) em '{nome_1}'")
                    break
            
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_2:
                    if subsistema['codigo'] != sub_de:
                        sub_para = subsistema['codigo']
                        safe_print(f"[FORMATTER] [DEBUG]     ✅ Destino encontrado: '{subsistema['nome']}' (código {sub_para}) em '{nome_2}'")
                        break
            
            if sub_de is not None and sub_para is not None:
                # Verificar se há filtro de sentido
                sentido = None
                if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                    sentido = 1
                elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                    sentido = 0
                
                if sentido is not None:
                    safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par 'entre X e Y' com sentido: ({sub_de}, {sub_para}, {sentido})")
                    return (sub_de, sub_para, sentido)
                safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par 'entre X e Y' sem sentido: ({sub_de}, {sub_para})")
                return (sub_de, sub_para)
            else:
                safe_print(f"[FORMATTER] [DEBUG]   Padrão 'entre X e Y' não encontrou par completo (sub_de={sub_de}, sub_para={sub_para})")
        
        # Padrão: "X para Y" ou "X → Y" - NOVA LÓGICA SIMPLIFICADA
        # Identificar todos os nomes de submercados na query e ordenar por posição cronológica
        safe_print(f"[FORMATTER] [DEBUG]   Padrão 'X para Y': Buscando todos os submercados na query...")
        
        submercados_encontrados = []
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                # Encontrar todas as ocorrências do nome na query
                pos = 0
                while True:
                    pos = query_lower.find(nome_sub_lower, pos)
                    if pos == -1:
                        break
                    submercados_encontrados.append({
                        'codigo': codigo_sub,
                        'nome': nome_sub,
                        'posicao': pos
                    })
                    safe_print(f"[FORMATTER] [DEBUG]     Encontrado '{nome_sub}' (código {codigo_sub}) na posição {pos}")
                    pos += 1
        
        # Ordenar por posição na query (ordem cronológica)
        submercados_encontrados.sort(key=lambda x: x['posicao'])
        safe_print(f"[FORMATTER] [DEBUG]   Submercados encontrados em ordem cronológica:")
        for i, sub in enumerate(submercados_encontrados):
            safe_print(f"[FORMATTER] [DEBUG]     {i+1}. '{sub['nome']}' (código {sub['codigo']}) na posição {sub['posicao']}")
        
        # Se encontrou pelo menos 2 submercados diferentes, usar os 2 primeiros
        if len(submercados_encontrados) >= 2:
            # Remover duplicatas mantendo a ordem
            submercados_unicos = []
            codigos_vistos = set()
            for sub in submercados_encontrados:
                if sub['codigo'] not in codigos_vistos:
                    codigos_vistos.add(sub['codigo'])
                    submercados_unicos.append(sub)
            
            if len(submercados_unicos) >= 2:
                sub_de = submercados_unicos[0]['codigo']
                sub_para = submercados_unicos[1]['codigo']
                safe_print(f"[FORMATTER] [DEBUG]   ✅ Par identificado por ordem cronológica:")
                safe_print(f"[FORMATTER] [DEBUG]     Origem: '{submercados_unicos[0]['nome']}' (código {sub_de})")
                safe_print(f"[FORMATTER] [DEBUG]     Destino: '{submercados_unicos[1]['nome']}' (código {sub_para})")
                
                # Verificar se há filtro de sentido
                sentido = None
                if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                    sentido = 1
                elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                    sentido = 0
                
                if sentido is not None:
                    safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par 'X para Y' com sentido: ({sub_de}, {sub_para}, {sentido})")
                    return (sub_de, sub_para, sentido)
                safe_print(f"[FORMATTER] [DEBUG] ✅ Retornando par 'X para Y' sem sentido: ({sub_de}, {sub_para})")
                return (sub_de, sub_para)
            else:
                safe_print(f"[FORMATTER] [DEBUG]   Apenas {len(submercados_unicos)} submercado(s) único(s) encontrado(s)")
        else:
            safe_print(f"[FORMATTER] [DEBUG]   Apenas {len(submercados_encontrados)} submercado(s) encontrado(s) na query")
        
        safe_print(f"[FORMATTER] [DEBUG] ❌ Nenhum par detectado, retornando None")
        return None


class RestricaoEletricaComparisonFormatter(ComparisonFormatter):
    """
    Formatador para RestricaoEletricaTool no modo multi-deck.
    Compara restrições elétricas entre múltiplos decks.
    Visualização: Tabela comparativa + Gráficos por restrição
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar RestricaoEletricaTool."""
        return tool_name == "RestricaoEletricaTool" and ("dados" in result_structure or "data" in result_structure)
    
    def get_priority(self) -> int:
        """Prioridade alta."""
        return 85
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de restrições elétricas para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "charts_by_restricao": {},
                "visualization_type": "restricao_eletrica",
                "chart_config": {
                    "type": "line",
                    "title": "Limites Superiores por Restrição e Patamar",
                    "x_axis": "Período",
                    "y_axis": "Limite Superior (MW)",
                    "tool_name": "RestricaoEletricaTool"
                },
                "tool_name": "RestricaoEletricaTool"
            }
        
        # Extrair dados de todos os decks
        all_restricoes = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados = result.get("dados", result.get("data", []))
            
            # Filtrar apenas limites (tipo 'limite')
            limites = [d for d in dados if d.get('tipo') == 'limite']
            
            # Indexar por (nome_restricao, patamar, período)
            indexed = self._index_by_restricao_patamar_periodo(limites)
            
            for nome_restricao in indexed.keys():
                all_restricoes.add(nome_restricao)
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "indexed": indexed
            })
        
        # Construir tabela de comparação e gráficos
        comparison_table = []
        charts_by_restricao = {}
        
        for nome_restricao in sorted(all_restricoes):
            # Coletar todos os patamares e períodos únicos para esta restrição
            all_patamares = set()
            all_periodos = set()
            
            for deck_info in decks_info:
                restricao_data = deck_info["indexed"].get(nome_restricao, {})
                for patamar_num in restricao_data.keys():
                    all_patamares.add(patamar_num)
                    patamar_data = restricao_data[patamar_num]
                    for periodo_key in patamar_data.get('periodos', {}).keys():
                        all_periodos.add(periodo_key)
            
            # Processar cada patamar
            for patamar_num in sorted(all_patamares):
                # Obter nome do patamar do primeiro deck que tiver
                nome_patamar = None
                for deck_info in decks_info:
                    restricao_data = deck_info["indexed"].get(nome_restricao, {})
                    patamar_data = restricao_data.get(patamar_num, {})
                    if patamar_data:
                        nome_patamar = patamar_data.get('nome_patamar', f'Patamar {patamar_num}')
                        break
                
                if not nome_patamar:
                    nome_patamar = f'Patamar {patamar_num}'
                
                # Processar cada período
                for periodo_key in sorted(all_periodos):
                    # Obter primeiro registro para extrair informações do período
                    first_record = None
                    for deck_info in decks_info:
                        restricao_data = deck_info["indexed"].get(nome_restricao, {})
                        patamar_data = restricao_data.get(patamar_num, {})
                        record = patamar_data.get('periodos', {}).get(periodo_key)
                        if record:
                            first_record = record
                            break
                    
                    if not first_record:
                        continue
                    
                    # Formatar período
                    periodo_formatted = self._format_period_label(
                        first_record.get('per_ini'),
                        first_record.get('per_fin')
                    )
                    
                    # Criar linha da tabela
                    table_row = {
                        "restricao": nome_restricao or f"Restrição {first_record.get('cod_rest', 'N/A')}",
                        "patamar": nome_patamar,
                        "patamar_num": patamar_num,
                        "periodo": periodo_formatted,
                        "cod_rest": first_record.get('cod_rest')
                    }
                    
                    # Adicionar valores de cada deck
                    for deck_idx, deck_info in enumerate(decks_info):
                        restricao_data = deck_info["indexed"].get(nome_restricao, {})
                        patamar_data = restricao_data.get(patamar_num, {})
                        record = patamar_data.get('periodos', {}).get(periodo_key, {})
                        lim_sup = self._safe_round(record.get('lim_sup'))
                        table_row[f"deck_{deck_idx + 1}"] = lim_sup
                    
                    comparison_table.append(table_row)
                
                # Preparar dados do gráfico para esta restrição e patamar
                if nome_restricao not in charts_by_restricao:
                    charts_by_restricao[nome_restricao] = {}
                
                # Coletar todos os períodos únicos para este patamar
                periodo_labels = []
                for periodo_key in sorted(all_periodos):
                    for deck_info in decks_info:
                        restricao_data = deck_info["indexed"].get(nome_restricao, {})
                        patamar_data = restricao_data.get(patamar_num, {})
                        record = patamar_data.get('periodos', {}).get(periodo_key)
                        if record:
                            periodo_labels.append(self._format_period_label(
                                record.get('per_ini'),
                                record.get('per_fin')
                            ))
                            break
                
                # Criar datasets para cada deck
                datasets = []
                for deck_idx, deck_info in enumerate(decks_info):
                    values = []
                    restricao_data = deck_info["indexed"].get(nome_restricao, {})
                    patamar_data = restricao_data.get(patamar_num, {})
                    
                    for periodo_key in sorted(all_periodos):
                        record = patamar_data.get('periodos', {}).get(periodo_key, {})
                        lim_sup = self._safe_round(record.get('lim_sup'))
                        values.append(lim_sup)
                    
                    datasets.append({
                        "label": deck_info["display_name"],
                        "data": values
                    })
                
                if periodo_labels and datasets:
                    charts_by_restricao[nome_restricao][nome_patamar] = {
                        "labels": periodo_labels,
                        "datasets": datasets,
                        "patamar_num": patamar_num
                    }
        
        return {
            "comparison_table": comparison_table,
            "charts_by_restricao": charts_by_restricao,
            "visualization_type": "restricao_eletrica",
            "chart_config": {
                "type": "line",
                "title": "Limites Superiores por Restrição e Patamar",
                "x_axis": "Período",
                "y_axis": "Limite Superior (MW)",
                "tool_name": "RestricaoEletricaTool"
            },
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2,
            "tool_name": "RestricaoEletricaTool"
        }
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de restrições elétricas (método legado para 2 decks)."""
        # Converter para formato de lista de decks
        decks_data = [
            DeckData(name="deck_1", display_name="Deck 1", result=result_dec, success=True),
            DeckData(name="deck_2", display_name="Deck 2", result=result_jan, success=True)
        ]
        return self.format_multi_deck_comparison(decks_data, tool_name, query)
    
    def _index_by_restricao_patamar_periodo(self, limites: List[Dict]) -> Dict[str, Dict[int, Dict]]:
        """
        Indexa limites por (nome_restricao, patamar, período).
        Retorna: {nome_restricao: {patamar: {nome_patamar: str, periodos: {periodo_key: record}}}}
        """
        indexed = {}
        
        for record in limites:
            nome_restricao = record.get('nome_restricao')
            if not nome_restricao:
                nome_restricao = f"Restrição {record.get('cod_rest', 'N/A')}"
            
            patamar = record.get('patamar')
            if patamar is None:
                continue
            
            # Criar chave de período
            per_ini = record.get('per_ini')
            per_fin = record.get('per_fin')
            periodo_key = f"{per_ini}_{per_fin}" if per_ini and per_fin else str(per_ini or per_fin or 'N/A')
            
            if nome_restricao not in indexed:
                indexed[nome_restricao] = {}
            
            if patamar not in indexed[nome_restricao]:
                indexed[nome_restricao][patamar] = {
                    'nome_patamar': record.get('nome_patamar', f'Patamar {patamar}'),
                    'periodos': {}
                }
            
            indexed[nome_restricao][patamar]['periodos'][periodo_key] = record
        
        return indexed
    
    def _format_period_label(self, per_ini: Optional[str], per_fin: Optional[str]) -> str:
        """Formata período para label legível."""
        if per_ini and per_fin:
            if per_ini == per_fin:
                return per_ini.replace('/', '-')  # "2025/12" -> "2025-12"
            return f"{per_ini.replace('/', '-')} a {per_fin.replace('/', '-')}"
        elif per_ini:
            return per_ini.replace('/', '-')
        elif per_fin:
            return per_fin.replace('/', '-')
        return "N/A"
    
    def _safe_round(self, value) -> Optional[float]:
        """Arredonda valor com tratamento de NaN/None."""
        if value is None:
            return None
        try:
            rounded = round(float(value), 2)
            if math.isnan(rounded) or math.isinf(rounded):
                return None
            if rounded == int(rounded):
                return int(rounded)
            return rounded
        except (ValueError, TypeError):
            return None


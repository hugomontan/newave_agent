"""
Formatadores temporais para comparação multi-deck.
Para tools que retornam séries históricas (dados por período).
"""
import math
import re
from typing import Dict, Any, List, Optional, Tuple
from app.agents.multi_deck.formatting.base import ComparisonFormatter


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
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
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
            return self._format_conjunturais(result_dec, result_jan, tool_name, query)
        
        # Se for CVU, usar formato simplificado
        if is_cvu:
            return self._format_cvu_simplified(
                dados_estruturais_dec,
                dados_estruturais_jan,
                result_dec,
                result_jan
            )
        
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
        
        # Se não encontrou, usar padrão baseado no nome do deck comum (NW202512 = 2025)
        # Por padrão, se não conseguir determinar, usar 2025 (ano base comum)
        return 2025
    
    def _format_cvu_simplified(
        self,
        dados_estruturais_dec: List[Dict],
        dados_estruturais_jan: List[Dict],
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formata comparação de CVU de forma simplificada:
        - Tabela: Ano (dinâmico baseado no deck), Deck 1, Deck 2
        - Gráfico: uma linha por deck, eixo Y = CVU, eixo X = Anos
        
        Nota: Para CVU, geralmente há uma única classe térmica. Se houver múltiplas,
        usa a primeira classe encontrada (priorizando a mais frequente nos dados).
        """
        # Obter ano base do deck (tenta extrair do deck de dezembro)
        ano_base = self._get_base_year_from_deck(result_dec)
        # O primeiro ano do estudo (indice_ano_estudo=1) corresponde ao ano seguinte ao ano base
        # Exemplo: deck de 2025 -> primeiro ano do estudo é 2026
        # Identificar a classe principal (mais frequente nos dados)
        classes_count = {}
        classe_nome_map = {}  # Mapear código -> nome para validação
        for record in dados_estruturais_dec + dados_estruturais_jan:
            classe = record.get("codigo_usina")
            nome_usina = record.get("nome_usina", "")
            if classe is not None:
                classes_count[classe] = classes_count.get(classe, 0) + 1
                # Armazenar nome da usina para esta classe (pegar o primeiro nome encontrado)
                if classe not in classe_nome_map and nome_usina:
                    classe_nome_map[classe] = nome_usina
        
        classe_principal = None
        nome_classe_principal = None
        if classes_count:
            # Usar a classe mais frequente
            classe_principal = max(classes_count.items(), key=lambda x: x[1])[0]
            nome_classe_principal = classe_nome_map.get(classe_principal, f"Classe {classe_principal}")
        
        # Agrupar por ano, filtrando pela classe principal se houver múltiplas classes
        dec_by_ano = {}  # {ano: valor}
        jan_by_ano = {}  # {ano: valor}
        
        # Processar dados de dezembro
        for record in dados_estruturais_dec:
            classe = record.get("codigo_usina")
            # Se há classe principal definida, filtrar por ela
            if classe_principal is not None and classe != classe_principal:
                continue
                
            ano = record.get("indice_ano_estudo")
            valor = self._sanitize_number(record.get("valor"))
            if ano is not None and valor is not None:
                # Se já existe valor para este ano, manter o primeiro
                if ano not in dec_by_ano:
                    dec_by_ano[ano] = valor
        
        # Processar dados de janeiro
        for record in dados_estruturais_jan:
            classe = record.get("codigo_usina")
            # Se há classe principal definida, filtrar por ela
            if classe_principal is not None and classe != classe_principal:
                continue
                
            ano = record.get("indice_ano_estudo")
            valor = self._sanitize_number(record.get("valor"))
            if ano is not None and valor is not None:
                if ano not in jan_by_ano:
                    jan_by_ano[ano] = valor
        
        # Obter todos os anos únicos e ordenar
        all_anos = sorted(set(list(dec_by_ano.keys()) + list(jan_by_ano.keys())))
        
        # Construir tabela comparativa simplificada
        comparison_table = []
        chart_labels = []
        dec_values = []
        jan_values = []
        
        for indice_ano in all_anos:
            val_dec = dec_by_ano.get(indice_ano)
            val_jan = jan_by_ano.get(indice_ano)
            
            # Calcular o ano real: ano_base + indice_ano_estudo
            # indice_ano_estudo=1 corresponde ao primeiro ano do estudo (ano_base + 1)
            ano_real = ano_base + indice_ano
            
            # Função auxiliar para arredondar e garantir que NaN vire None
            def safe_round(value):
                if value is None:
                    return None
                try:
                    rounded = round(value, 2)
                    # Verificar se o resultado é NaN ou Inf
                    if math.isnan(rounded) or math.isinf(rounded):
                        return None
                    return rounded
                except (ValueError, TypeError):
                    return None
            
            # Adicionar à tabela (sem colunas de diferença e variação %)
            # Campo de validação: "Custos de Classe - Nome da usina"
            classe_info = f"{classe_principal} - {nome_classe_principal}" if classe_principal is not None and nome_classe_principal else "N/A"
            
            table_row = {
                "classe_info": classe_info,  # Campo de validação no início
                "data": ano_real,  # Coluna "Data" com o ano real (dinâmico)
                "ano": ano_real,  # Também incluir campo "ano" para compatibilidade
                "deck_1": safe_round(val_dec),
                "deck_2": safe_round(val_jan),
            }
            
            comparison_table.append(table_row)
            
            # Dados para gráfico
            chart_labels.append(f"Ano {ano_real}")
            dec_values.append(safe_round(val_dec))
            jan_values.append(safe_round(val_jan))
        
        # Construir chart_data (uma linha por deck)
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
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "table_with_line_chart",
            "chart_config": {
                "type": "line",
                "title": "CVU - Custo Variável Unitário",
                "x_axis": "Ano",
                "y_axis": "CVU (R$/MWh)"
            }
        }
    
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
        data_dec = result_dec.get("data", [])
        data_jan = result_jan.get("data", [])
        
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
            
            val_dec = self._extract_value(dec_record)
            val_jan = self._extract_value(jan_record)
            
            if val_dec is not None and val_jan is not None:
                diff = val_jan - val_dec
                comparison_table.append({
                    "periodo": periodo,
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
        return tool_name == "UsinasNaoSimuladasTool" and "data" in result_structure
    
    def get_priority(self) -> int:
        return 75
    
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
        data_dec = result_dec.get("data", [])
        data_jan = result_jan.get("data", [])
        
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
            "visualization_type": "contextual_line_chart",
            "chart_config": {
                "type": "line",
                "title": "Geração de Usinas Não Simuladas",
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)"
            }
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
            "visualization_type": "contextual_line_chart",
            "chart_config": {
                "type": "line",
                "title": titulo,
                "x_axis": "Período",
                "y_axis": "Geração (MWméd)"
            }
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
        from app.config import safe_print
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
        from app.config import safe_print
        
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


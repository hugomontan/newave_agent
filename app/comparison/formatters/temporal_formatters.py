"""
Formatadores temporais para comparação multi-deck.
Para tools que retornam séries históricas (dados por período).
"""
import math
from typing import Dict, Any, List, Optional
from app.comparison.base import ComparisonFormatter


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
    
    def _format_cvu_simplified(
        self,
        dados_estruturais_dec: List[Dict],
        dados_estruturais_jan: List[Dict],
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formata comparação de CVU de forma simplificada:
        - Tabela: Data (anos), Deck 1, Deck 2, Diferença (nominal + %)
        - Gráfico: uma linha por deck, eixo Y = CVU, eixo X = Anos
        
        Nota: Para CVU, geralmente há uma única classe térmica. Se houver múltiplas,
        usa a primeira classe encontrada (priorizando a mais frequente nos dados).
        """
        # Identificar a classe principal (mais frequente nos dados)
        classes_count = {}
        for record in dados_estruturais_dec + dados_estruturais_jan:
            classe = record.get("codigo_usina")
            if classe is not None:
                classes_count[classe] = classes_count.get(classe, 0) + 1
        
        classe_principal = None
        if classes_count:
            # Usar a classe mais frequente
            classe_principal = max(classes_count.items(), key=lambda x: x[1])[0]
        
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
        
        for ano in all_anos:
            val_dec = dec_by_ano.get(ano)
            val_jan = jan_by_ano.get(ano)
            
            # Calcular diferença (deck novo - deck antigo = janeiro - dezembro)
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
            
            # Adicionar à tabela
            table_row = {
                "data": ano,  # Coluna "Data" com o ano
                "deck_1": safe_round(val_dec),
                "deck_2": safe_round(val_jan),
            }
            
            # Adicionar diferença (nominal + porcentagem)
            if diff is not None:
                table_row["diferenca"] = safe_round(diff)
                if diff_percent is not None:
                    table_row["diferenca_percent"] = safe_round(diff_percent)
                else:
                    table_row["diferenca_percent"] = None
            else:
                table_row["diferenca"] = None
                table_row["diferenca_percent"] = None
            
            comparison_table.append(table_row)
            
            # Dados para gráfico
            chart_labels.append(f"Ano {ano}")
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
            
            # Adicionar à tabela (mesmo formato do CVU)
            table_row = {
                "data": periodo_label,  # Coluna "Data" com ano-mês formatado (ex: "Dez/2025")
                "ano": ano,  # Ano extraído do periodo_key (para detecção no frontend)
                "mes": mes,  # Mês extraído do periodo_key (para detecção no frontend)
                "deck_1": safe_round(val_dec),
                "deck_2": safe_round(val_jan),
            }
            
            # Adicionar diferença (nominal + porcentagem)
            if diff is not None:
                table_row["diferenca"] = safe_round(diff)
                if diff_percent is not None:
                    table_row["diferenca_percent"] = safe_round(diff_percent)
                else:
                    table_row["diferenca_percent"] = None
            else:
                table_row["diferenca"] = None
                table_row["diferenca_percent"] = None
            
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
    Apenas linhas com diferenças são incluídas.
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
        Agrupa por par de submercados e sentido, mostrando apenas diferenças.
        
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
        
        # Construir tabela comparativa (apenas linhas com diferenças) e charts_by_par
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
                
                # Construir dados do gráfico para este par (incluir todos os períodos, não apenas diferenças)
                par_dec_values = []
                par_jan_values = []
                
                for periodo in all_periodos:
                    dec_record = dec_records.get(periodo, {})
                    jan_record = jan_records.get(periodo, {})
                    
                    val_dec = self._sanitize_number(dec_record.get("valor"))
                    val_jan = self._sanitize_number(jan_record.get("valor"))
                    
                    # Dados para gráfico (todos os períodos)
                    par_dec_values.append(self._safe_round(val_dec))
                    par_jan_values.append(self._safe_round(val_jan))
                    
                    # Calcular diferença para tabela (apenas diferenças)
                    diff = None
                    diff_percent = None
                    
                    if val_dec is not None and val_jan is not None:
                        diff = val_jan - val_dec
                        # Incluir apenas se houver diferença
                        if diff != 0:
                            diff_percent = ((val_jan - val_dec) / val_dec * 100) if val_dec != 0 else None
                    elif val_jan is not None:
                        # Apenas no deck 2 (adicionado)
                        diff = val_jan
                        diff_percent = None
                    elif val_dec is not None:
                        # Apenas no deck 1 (removido)
                        diff = -val_dec
                        diff_percent = None
                    
                    # Incluir apenas linhas com diferenças na tabela
                    if diff is not None and diff != 0:
                        # Formatar período como YYYY-MM
                        periodo_formatted = periodo  # Já vem no formato YYYY-MM
                        
                        comparison_table.append({
                            "data": periodo_formatted,
                            "par_key": par_key,
                            "par": par_label,
                            "sentido": sentido_label,
                            "deck_1": self._safe_round(val_dec),
                            "deck_2": self._safe_round(val_jan),
                            "diferenca": self._safe_round(diff),
                            "diferenca_percent": self._safe_round(diff_percent) if diff_percent is not None else None
                        })
                
                # Criar chart_data para este par
                par_chart_data = {
                    "labels": all_periodos,
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
                "total_differences": len(comparison_table),
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
    
    def _safe_round(self, value) -> Optional[float]:
        """Arredonda valor com tratamento de NaN/None."""
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


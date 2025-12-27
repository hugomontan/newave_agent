"""
Tool que executa outra tool em dois decks e compara os resultados.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
import pandas as pd
from app.tools.base import NEWAVETool
from app.tools.semantic_matcher import find_best_tool_semantic
from app.utils.deck_loader import get_december_deck_path, get_january_deck_path

class MultiDeckComparisonTool(NEWAVETool):
    """
    Wrapper que executa outra tool em dois decks e compara resultados.
    Sempre executa comparação entre dezembro e janeiro.
    """
    
    def __init__(self, deck_path: str):
        super().__init__(deck_path)
        try:
            self.deck_december = get_december_deck_path()
            self.deck_january = get_january_deck_path()
        except FileNotFoundError as e:
            print(f"[MULTI-DECK] ⚠️ Erro ao carregar decks: {e}")
            self.deck_december = None
            self.deck_january = None
    
    def can_handle(self, query: str) -> bool:
        """
        Sempre retorna True - intercepta todas as queries para comparação.
        Mas só executa se os decks estiverem disponíveis.
        """
        return self.deck_december is not None and self.deck_january is not None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a tool correta em ambos os decks e compara resultados.
        """
        if not self.deck_december or not self.deck_january:
            return {
                "success": False,
                "error": "Decks de dezembro ou janeiro não encontrados"
            }
        
        print(f"[MULTI-DECK] Iniciando comparação para query: {query[:100]}")
        
        # 1. Encontrar tool correta usando o deck de dezembro como referência
        try:
            # Importar aqui para evitar circular import
            from app.tools import get_available_tools
            tools = get_available_tools(str(self.deck_december))
            best_tool, score = find_best_tool_semantic(query, tools)
            
            if not best_tool or score < 0.4:
                print(f"[MULTI-DECK] ⚠️ Tool não encontrada ou score baixo ({score})")
                return {
                    "success": False,
                    "error": "Nenhuma tool adequada encontrada para esta query"
                }
            
            tool_class = best_tool.__class__
            tool_name = tool_class.__name__
            print(f"[MULTI-DECK] ✅ Tool identificada: {tool_name} (score: {score:.2f})")
            
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro ao identificar tool: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao identificar tool: {str(e)}"
            }
        
        # 2. Executar em paralelo
        print(f"[MULTI-DECK] Executando {tool_name} em paralelo nos dois decks...")
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_dec = executor.submit(
                    self._execute_tool_safe,
                    tool_class,
                    str(self.deck_december),
                    query,
                    "Dezembro 2025"
                )
                future_jan = executor.submit(
                    self._execute_tool_safe,
                    tool_class,
                    str(self.deck_january),
                    query,
                    "Janeiro 2026"
                )
                
                result_dec = future_dec.result()
                result_jan = future_jan.result()
            
            print(f"[MULTI-DECK] ✅ Execução paralela concluída")
            
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro na execução paralela: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao executar tool nos decks: {str(e)}"
            }
        
        # 3. Comparar e formatar resultados
        try:
            comparison = self._format_comparison(
                result_dec,
                result_jan,
                tool_name,
                query
            )
            print(f"[MULTI-DECK] ✅ Comparação formatada com sucesso")
            return comparison
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro ao formatar comparação: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao formatar comparação: {str(e)}"
            }
    
    def _execute_tool_safe(self, tool_class, deck_path: str, query: str, deck_name: str) -> Dict[str, Any]:
        """Executa uma tool de forma segura, capturando erros."""
        try:
            print(f"[MULTI-DECK] Executando {tool_class.__name__} em {deck_name} (deck_path: {deck_path})")
            tool = tool_class(deck_path)
            result = tool.execute(query)
            result["deck_name"] = deck_name
            
            # Log dos dados retornados
            data_count = len(result.get("data", []))
            dados_estruturais_count = len(result.get("dados_estruturais", []))
            print(f"[MULTI-DECK] ✅ {deck_name}: success={result.get('success')}, data_count={data_count}, dados_estruturais_count={dados_estruturais_count}")
            
            if result.get("success") and data_count > 0:
                # Log de exemplo dos primeiros dados
                first_record = result.get("data", [])[0] if result.get("data") else {}
                print(f"[MULTI-DECK]   Primeiro registro de {deck_name}: {list(first_record.keys())[:5]}...")
            
            return result
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro ao executar tool em {deck_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "deck_name": deck_name
            }
    
    def _format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata os resultados em uma estrutura de comparação."""
        comparison = {
            "success": True,
            "is_comparison": True,
            "tool_used": tool_name,
            "query": query,
            "deck_1": {
                "name": result_dec.get("deck_name", "Dezembro 2025"),
                "success": result_dec.get("success", False),
                "data": result_dec.get("data", []) or result_dec.get("dados_estruturais", []),
                "summary": result_dec.get("summary", {}),
                "error": result_dec.get("error")
            },
            "deck_2": {
                "name": result_jan.get("deck_name", "Janeiro 2026"),
                "success": result_jan.get("success", False),
                "data": result_jan.get("data", []) or result_jan.get("dados_estruturais", []),
                "summary": result_jan.get("summary", {}),
                "error": result_jan.get("error")
            },
            "chart_data": None,
            "differences": []
        }
        
        # Calcular diferenças e gerar gráfico se ambos tiverem sucesso
        if result_dec.get("success") and result_jan.get("success"):
            # Extrair dados - algumas tools retornam em "data", outras em "dados_estruturais"
            data_dec = result_dec.get("data", [])
            data_jan = result_jan.get("data", [])
            
            # Se não houver "data", tentar "dados_estruturais" (para ClastValoresTool)
            if not data_dec and result_dec.get("dados_estruturais"):
                data_dec = result_dec.get("dados_estruturais", [])
            if not data_jan and result_jan.get("dados_estruturais"):
                data_jan = result_jan.get("dados_estruturais", [])
            
            print(f"[MULTI-DECK] Dados extraídos - Dezembro: {len(data_dec)} registros, Janeiro: {len(data_jan)} registros")
            
            if data_dec and data_jan:
                # Log de exemplo das colunas
                sample_dec = data_dec[0] if data_dec else {}
                sample_jan = data_jan[0] if data_jan else {}
                print(f"[MULTI-DECK] Colunas Dezembro: {list(sample_dec.keys())}")
                print(f"[MULTI-DECK] Colunas Janeiro: {list(sample_jan.keys())}")
            
            # Calcular diferenças entre os dados
            differences = self._calculate_differences(
                data_dec,
                data_jan,
                tolerance_percent=0.1  # 0.1% de tolerância
            )
            comparison["differences"] = differences
            
            # Gerar dados para gráfico - SEMPRE tentar gerar
            print(f"[MULTI-DECK] Gerando dados do gráfico...")
            chart_data = self._generate_chart_data(
                data_dec,
                data_jan,
                result_dec.get("deck_name", "Dezembro 2025"),
                result_jan.get("deck_name", "Janeiro 2026")
            )
            if chart_data:
                print(f"[MULTI-DECK] ✅ Gráfico gerado: {len(chart_data.get('labels', []))} períodos, {len(chart_data.get('datasets', []))} datasets")
                print(f"[MULTI-DECK]   Labels: {chart_data.get('labels', [])[:5]}... (primeiros 5)")
                for i, dataset in enumerate(chart_data.get('datasets', [])):
                    non_null_count = len([d for d in dataset.get('data', []) if d is not None])
                    print(f"[MULTI-DECK]   Dataset {i} ({dataset.get('label')}): {non_null_count} valores não-nulos de {len(dataset.get('data', []))} total")
            else:
                print(f"[MULTI-DECK] ⚠️ Gráfico não gerado (retornou None)")
                print(f"[MULTI-DECK]   Dados disponíveis: dec={len(data_dec)} registros, jan={len(data_jan)} registros")
            comparison["chart_data"] = chart_data
        
        return comparison
    
    def _calculate_differences(
        self,
        data_dec: List[Dict],
        data_jan: List[Dict],
        tolerance_percent: float = 0.1
    ) -> List[Dict]:
        """
        Calcula diferenças entre os dados dos dois decks.
        
        Args:
            data_dec: Dados do deck de dezembro
            data_jan: Dados do deck de janeiro
            tolerance_percent: Tolerância percentual para considerar diferença significativa
            
        Returns:
            Lista de diferenças encontradas
        """
        differences = []
        
        if not data_dec or not data_jan:
            return differences
        
        try:
            df_dec = pd.DataFrame(data_dec)
            df_jan = pd.DataFrame(data_jan)
            
            # Identificar colunas numéricas para comparar
            numeric_cols_dec = df_dec.select_dtypes(include=['number']).columns.tolist()
            numeric_cols_jan = df_jan.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [col for col in numeric_cols_dec if col in numeric_cols_jan]
            
            if not numeric_cols:
                return differences
            
            # Identificar colunas de identificação para fazer merge correto
            # Para CargaMensalTool: precisa de codigo_submercado, ano, mes
            # Para ClastValoresTool: precisa de indice_ano_estudo, codigo_usina
            # Tentar identificar todas as colunas de identificação relevantes
            id_cols = []
            
            # Colunas de período/tempo - ADICIONAR TODAS as colunas relevantes
            period_cols = ["indice_ano_estudo", "ano", "mes", "periodo", "ano_estudo"]
            for col in period_cols:
                if col in df_dec.columns and col in df_jan.columns:
                    if col not in id_cols:  # Evitar duplicatas
                        id_cols.append(col)
            
            # IMPORTANTE: Para dados mensais, garantir que 'mes' seja incluído se disponível
            if 'mes' in df_dec.columns and 'mes' in df_jan.columns and 'mes' not in id_cols:
                id_cols.append('mes')
            
            # Colunas de identificação (submercado, usina, etc)
            entity_cols = ["codigo_submercado", "codigo_usina", "nome_submercado", "nome_usina"]
            for col in entity_cols:
                if col in df_dec.columns and col in df_jan.columns:
                    if col not in id_cols:  # Evitar duplicatas
                        id_cols.append(col)
            
            # Se não encontrou colunas de identificação, usar todas as colunas não-numéricas
            if not id_cols:
                non_numeric_cols = [col for col in df_dec.columns 
                                  if col not in numeric_cols and col in df_jan.columns]
                id_cols = non_numeric_cols[:3]  # Limitar a 3 colunas para evitar merge muito complexo
            
            if id_cols:
                print(f"[MULTI-DECK] Usando colunas de identificação para merge: {id_cols}")
                # Mesclar por todas as colunas de identificação para comparar valores correspondentes
                merged = pd.merge(
                    df_dec,
                    df_jan,
                    on=id_cols,
                    suffixes=('_dec', '_jan'),
                    how='outer'
                )
                
                print(f"[MULTI-DECK] Colunas numéricas para comparar: {numeric_cols}")
                print(f"[MULTI-DECK] Colunas após merge: {list(merged.columns)[:10]}...")
                
                for col in numeric_cols:
                    col_dec = f"{col}_dec"
                    col_jan = f"{col}_jan"
                    
                    if col_dec in merged.columns and col_jan in merged.columns:
                        print(f"[MULTI-DECK] Comparando coluna '{col}' (dec: {col_dec}, jan: {col_jan})")
                        for idx, row in merged.iterrows():
                            val_dec = row[col_dec]
                            val_jan = row[col_jan]
                            
                            # Criar identificador do período usando as colunas de ID
                            # Formatar como "Ano - Mês" (ex: "2026 - Janeiro")
                            period_parts = []
                            ano_val = None
                            mes_val = None
                            mes_nome = None
                            
                            # Extrair ano e mês separadamente
                            for id_col in id_cols:
                                if id_col == 'ano' and id_col in row and pd.notna(row[id_col]):
                                    ano_val = int(row[id_col]) if pd.notna(row[id_col]) else None
                                elif id_col == 'mes' and id_col in row and pd.notna(row[id_col]):
                                    mes_val = int(row[id_col]) if pd.notna(row[id_col]) else None
                            
                            # Se não encontrou nas colunas de ID, tentar nas colunas originais
                            if ano_val is None and 'ano' in row and pd.notna(row.get('ano')):
                                ano_val = int(row['ano'])
                            if mes_val is None and 'mes_dec' in row and pd.notna(row.get('mes_dec')):
                                mes_val = int(row['mes_dec'])
                            elif mes_val is None and 'mes_jan' in row and pd.notna(row.get('mes_jan')):
                                mes_val = int(row['mes_jan'])
                            
                            # Converter número do mês para nome
                            meses_nomes = {
                                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
                            }
                            if mes_val and mes_val in meses_nomes:
                                mes_nome = meses_nomes[mes_val]
                            
                            # Formatar período
                            if ano_val and mes_nome:
                                period_val = f"{ano_val} - {mes_nome}"
                            elif ano_val and mes_val:
                                period_val = f"{ano_val} - {mes_val}"
                            elif ano_val:
                                period_val = str(ano_val)
                            else:
                                # Fallback: usar todas as colunas de ID
                                for id_col in id_cols:
                                    if id_col in row and pd.notna(row[id_col]):
                                        period_parts.append(str(row[id_col]))
                                period_val = " | ".join(period_parts) if period_parts else f"Registro {idx+1}"
                            
                            # Comparar apenas se ambos valores existirem
                            if pd.notna(val_dec) and pd.notna(val_jan):
                                # Debug: log dos primeiros valores
                                if len(differences) < 3:
                                    print(f"[MULTI-DECK]   Exemplo {len(differences)+1}: {col} - Dec={val_dec}, Jan={val_jan}, Period={period_val}")
                                val_dec_float = float(val_dec)
                                val_jan_float = float(val_jan)
                                
                                # Calcular diferença: deck mais novo (Janeiro) - deck mais antigo (Dezembro)
                                # Não usar valor absoluto - manter o sinal
                                diff_nominal = val_jan_float - val_dec_float
                                
                                # Calcular diferença absoluta apenas para verificar se é significativa
                                diff_abs = abs(diff_nominal)
                                
                                # Calcular diferença relativa (percentual) COM SINAL
                                # ((Janeiro - Dezembro) / Dezembro) * 100
                                if abs(val_dec_float) > 1e-10:  # Evitar divisão por zero
                                    diff_rel = (diff_nominal / val_dec_float) * 100
                                else:
                                    diff_rel = 100.0 if diff_abs > 1e-10 else 0.0
                                
                                # Considerar diferença significativa se:
                                # - Diferença relativa absoluta > tolerância percentual OU
                                # - Diferença absoluta > 0.01 (para valores pequenos)
                                if abs(diff_rel) > tolerance_percent or diff_abs > 0.01:
                                    differences.append({
                                        "field": f"{col}",
                                        "period": str(period_val) if pd.notna(period_val) else f"Registro {idx+1}",
                                        "deck_1_value": val_dec_float,
                                        "deck_2_value": val_jan_float,
                                        "difference": diff_nominal,  # Diferença com sinal (Janeiro - Dezembro)
                                        "difference_percent": diff_rel
                                    })
            else:
                # Se não houver coluna de período, comparar por índice
                min_len = min(len(df_dec), len(df_jan))
                for col in numeric_cols:
                    for i in range(min_len):
                        val_dec = df_dec[col].iloc[i]
                        val_jan = df_jan[col].iloc[i]
                        
                        if pd.notna(val_dec) and pd.notna(val_jan):
                            val_dec_float = float(val_dec)
                            val_jan_float = float(val_jan)
                            
                            # Calcular diferença: deck mais novo (Janeiro) - deck mais antigo (Dezembro)
                            # Não usar valor absoluto - manter o sinal
                            diff_nominal = val_jan_float - val_dec_float
                            
                            # Calcular diferença absoluta apenas para verificar se é significativa
                            diff_abs = abs(diff_nominal)
                            
                            # Calcular diferença relativa (percentual) COM SINAL
                            # ((Janeiro - Dezembro) / Dezembro) * 100
                            if abs(val_dec_float) > 1e-10:
                                diff_rel = (diff_nominal / val_dec_float) * 100
                            else:
                                diff_rel = 100.0 if diff_abs > 1e-10 else 0.0
                            
                            if abs(diff_rel) > tolerance_percent or diff_abs > 0.01:
                                differences.append({
                                    "field": f"{col}",
                                    "period": f"Registro {i+1}",
                                    "deck_1_value": val_dec_float,
                                    "deck_2_value": val_jan_float,
                                    "difference": diff_nominal,  # Diferença com sinal (Janeiro - Dezembro)
                                    "difference_percent": diff_rel
                                })
            
            print(f"[MULTI-DECK] ✅ {len(differences)} diferença(s) significativa(s) encontrada(s)")
            
        except Exception as e:
            print(f"[MULTI-DECK] ⚠️ Erro ao calcular diferenças: {e}")
            import traceback
            traceback.print_exc()
        
        return differences
    
    def _generate_chart_data(
        self,
        data_dec: List[Dict],
        data_jan: List[Dict],
        name_dec: str,
        name_jan: str
    ) -> Dict[str, Any]:
        """Gera dados formatados para gráfico comparativo."""
        if not data_dec or not data_jan:
            print(f"[MULTI-DECK] ⚠️ Dados vazios para gráfico: dec={len(data_dec) if data_dec else 0}, jan={len(data_jan) if data_jan else 0}")
            return None
        
        # Tentar identificar coluna de tempo/período e coluna de valor
        # Para CVU: geralmente tem "ano" ou "indice_ano_estudo" e "valor"
        # Para carga mensal: tem "ano", "mes" e valor
        
        # Converter para DataFrames para facilitar manipulação
        try:
            df_dec = pd.DataFrame(data_dec)
            df_jan = pd.DataFrame(data_jan)
            
            print(f"[MULTI-DECK] Gerando gráfico: {len(df_dec)} registros dezembro, {len(df_jan)} registros janeiro")
            print(f"[MULTI-DECK] Colunas dezembro: {list(df_dec.columns)}")
            print(f"[MULTI-DECK] Colunas janeiro: {list(df_jan.columns)}")
            
            # Identificar coluna de valor
            value_cols = ["valor", "cvu", "carga", "demanda", "potencia", "geracao"]
            value_col = None
            for col in value_cols:
                if col in df_dec.columns:
                    value_col = col
                    break
            
            # Se não encontrou, usar primeira coluna numérica como valor (exceto códigos)
            if not value_col:
                numeric_cols = df_dec.select_dtypes(include=['number']).columns
                # Excluir colunas de código/ID
                exclude_cols = ['codigo_submercado', 'codigo_usina', 'mes', 'ano']
                numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
                if len(numeric_cols) > 0:
                    value_col = numeric_cols[0]
            
            if not value_col:
                print(f"[MULTI-DECK] ⚠️ Coluna de valor não encontrada")
                return None
            
            print(f"[MULTI-DECK] Coluna de valor identificada: {value_col}")
            
            # Para dados mensais: criar chave composta de ano-mes
            # Para CVU: usar indice_ano_estudo ou ano
            if 'ano' in df_dec.columns and 'mes' in df_dec.columns:
                # Dados mensais: criar label "Ano - Mês"
                meses_nomes = {
                    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
                    5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                    9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
                }
                
                # Criar chave composta para ordenação
                df_dec['_period_key'] = df_dec['ano'].astype(str) + '-' + df_dec['mes'].astype(str).str.zfill(2)
                df_dec['_period_label'] = df_dec['ano'].astype(str) + ' - ' + df_dec['mes'].map(meses_nomes)
                df_jan['_period_key'] = df_jan['ano'].astype(str) + '-' + df_jan['mes'].astype(str).str.zfill(2)
                df_jan['_period_label'] = df_jan['ano'].astype(str) + ' - ' + df_jan['mes'].map(meses_nomes)
                
                # Obter todos os períodos únicos ordenados
                all_periods = sorted(set(
                    list(df_dec['_period_key'].astype(str)) + 
                    list(df_jan['_period_key'].astype(str))
                ))
                
                # Criar labels correspondentes
                labels = []
                for p_key in all_periods:
                    # Buscar label correspondente
                    dec_match = df_dec[df_dec['_period_key'] == p_key]
                    jan_match = df_jan[df_jan['_period_key'] == p_key]
                    if not dec_match.empty:
                        labels.append(dec_match.iloc[0]['_period_label'])
                    elif not jan_match.empty:
                        labels.append(jan_match.iloc[0]['_period_label'])
                    else:
                        labels.append(p_key)
                
                # Criar dicionários para lookup
                dec_dict = dict(zip(
                    df_dec['_period_key'].astype(str),
                    df_dec[value_col]
                ))
                jan_dict = dict(zip(
                    df_jan['_period_key'].astype(str),
                    df_jan[value_col]
                ))
                
                dataset_dec = [dec_dict.get(p, None) for p in all_periods]
                dataset_jan = [jan_dict.get(p, None) for p in all_periods]
                
            elif 'indice_ano_estudo' in df_dec.columns:
                # Dados de CVU: usar indice_ano_estudo
                period_col = 'indice_ano_estudo'
                all_periods = sorted(set(
                    list(df_dec[period_col].astype(str)) + 
                    list(df_jan[period_col].astype(str))
                ))
                labels = all_periods
                
                dec_dict = dict(zip(
                    df_dec[period_col].astype(str),
                    df_dec[value_col]
                ))
                jan_dict = dict(zip(
                    df_jan[period_col].astype(str),
                    df_jan[value_col]
                ))
                
                dataset_dec = [dec_dict.get(p, None) for p in labels]
                dataset_jan = [jan_dict.get(p, None) for p in labels]
                
            elif 'ano' in df_dec.columns:
                # Apenas ano disponível
                period_col = 'ano'
                all_periods = sorted(set(
                    list(df_dec[period_col].astype(str)) + 
                    list(df_jan[period_col].astype(str))
                ))
                labels = all_periods
                
                dec_dict = dict(zip(
                    df_dec[period_col].astype(str),
                    df_dec[value_col]
                ))
                jan_dict = dict(zip(
                    df_jan[period_col].astype(str),
                    df_jan[value_col]
                ))
                
                dataset_dec = [dec_dict.get(p, None) for p in labels]
                dataset_jan = [jan_dict.get(p, None) for p in labels]
            else:
                # Fallback: usar índice como período
                max_len = max(len(df_dec), len(df_jan))
                labels = [str(i+1) for i in range(max_len)]
                dataset_dec = df_dec[value_col].tolist() if value_col in df_dec.columns else []
                dataset_jan = df_jan[value_col].tolist() if value_col in df_jan.columns else []
                # Preencher com None se necessário
                while len(dataset_dec) < max_len:
                    dataset_dec.append(None)
                while len(dataset_jan) < max_len:
                    dataset_jan.append(None)
            
            print(f"[MULTI-DECK] ✅ Gráfico gerado: {len(labels)} períodos, {len([d for d in dataset_dec if d is not None])} valores dezembro, {len([d for d in dataset_jan if d is not None])} valores janeiro")
            
            return {
                "labels": labels,
                "datasets": [
                    {
                        "label": name_dec,
                        "data": dataset_dec
                    },
                    {
                        "label": name_jan,
                        "data": dataset_jan
                    }
                ]
            }
        except Exception as e:
            print(f"[MULTI-DECK] ⚠️ Erro ao gerar dados do gráfico: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_description(self) -> str:
        """Retorna descrição da tool."""
        return """Tool que executa outras tools em dois decks (dezembro e janeiro) 
        e compara os resultados lado a lado com gráfico comparativo."""


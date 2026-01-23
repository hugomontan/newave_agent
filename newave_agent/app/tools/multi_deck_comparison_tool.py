"""
Tool que executa outra tool em N decks e compara os resultados.
Suporta comparação dinâmica entre múltiplos decks.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
import math
from newave_agent.app.tools.base import NEWAVETool
from newave_agent.app.tools.semantic_matcher import find_best_tool_semantic
from newave_agent.app.config import debug_print, safe_print
from newave_agent.app.utils.deck_loader import (
    list_available_decks,
    load_multiple_decks,
    get_deck_display_name,
)


class MultiDeckComparisonTool(NEWAVETool):
    """
    Wrapper que executa outra tool em N decks e compara resultados.
    Suporta comparação de múltiplos decks em paralelo.
    """
    
    def __init__(self, deck_path: str, selected_decks: Optional[List[str]] = None, forced_tool_class: Optional[type] = None):
        """
        Inicializa a tool de comparação multi-deck.
        
        Args:
            deck_path: Caminho do deck principal (para compatibilidade)
            selected_decks: Lista de nomes dos decks a comparar. Se None, usa os dois mais recentes.
            forced_tool_class: Classe da tool a ser usada diretamente (evita semantic matching)
        """
        super().__init__(deck_path)
        self.selected_decks = selected_decks or []
        self.deck_paths: Dict[str, str] = {}
        self.deck_display_names: Dict[str, str] = {}
        self.forced_tool_class = forced_tool_class  # Tool forçada (já identificada pelo router)
        
        try:
            # Se não foram especificados decks, usar os dois mais recentes
            if not self.selected_decks:
                available = list_available_decks()
                if len(available) >= 2:
                    self.selected_decks = [d["name"] for d in available[-2:]]
                elif len(available) == 1:
                    self.selected_decks = [available[0]["name"]]
            
            # Carregar caminhos dos decks selecionados
            if self.selected_decks:
                paths = load_multiple_decks(self.selected_decks)
                self.deck_paths = {name: str(path) for name, path in paths.items()}
                self.deck_display_names = {
                    name: get_deck_display_name(name) 
                    for name in self.selected_decks
                }
                print(f"[MULTI-DECK] Decks carregados: {list(self.deck_display_names.values())}")
        except Exception as e:
            print(f"[MULTI-DECK] ⚠️ Erro ao carregar decks: {e}")
            self.selected_decks = []
            self.deck_paths = {}
            self.deck_display_names = {}
    
    def can_handle(self, query: str) -> bool:
        """Retorna True se os decks estiverem disponíveis."""
        return len(self.deck_paths) >= 1
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a tool correta em N decks e compara resultados.
        """
        if not self.deck_paths:
            return {
                "success": False,
                "error": "Nenhum deck disponível para comparação"
            }
        
        print(f"[MULTI-DECK] ========== INÍCIO: MultiDeckComparisonTool.execute ==========")
        print(f"[MULTI-DECK] Query: {query[:100]}")
        print(f"[MULTI-DECK] Decks selecionados: {self.selected_decks}")
        print(f"[MULTI-DECK] Número de decks: {len(self.selected_decks)}")
        print(f"[MULTI-DECK] Deck paths disponíveis: {list(self.deck_paths.keys())}")
        
        if len(self.selected_decks) < 2:
            print(f"[MULTI-DECK] ⚠️ AVISO: Apenas {len(self.selected_decks)} deck(s) selecionado(s). Comparação requer pelo menos 2 decks.")
        
        # 1. Encontrar tool correta
        first_deck_path = self.deck_paths[self.selected_decks[0]]
        print(f"[MULTI-DECK] Primeiro deck path: {first_deck_path}")
        
        # Se uma tool foi forçada (já identificada pelo router), usar diretamente
        if self.forced_tool_class:
            tool_class = self.forced_tool_class
            tool_name = tool_class.__name__
            print(f"[MULTI-DECK] ✅ Tool forçada (já identificada pelo router): {tool_name}")
        else:
            # Fazer semantic matching para encontrar a tool
            try:
                from newave_agent.app.tools import get_available_tools
                # IMPORTANTE: Usar modo "comparison" para incluir VariacaoReservatorioInicialTool, etc.
                tools = get_available_tools(first_deck_path, analysis_mode="comparison")
                print(f"[MULTI-DECK] Tools disponíveis no modo comparison: {len(tools)}")
                result = find_best_tool_semantic(query, tools)
                
                # Tratar caso de None (quando não encontra tool)
                if result is None:
                    print(f"[MULTI-DECK] ⚠️ Tool não encontrada (find_best_tool_semantic retornou None)")
                    return {
                        "success": False,
                        "error": "Nenhuma tool adequada encontrada para esta query"
                    }
                
                best_tool, score = result
                
                if not best_tool or score < 0.4:
                    print(f"[MULTI-DECK] ⚠️ Tool não encontrada ou score baixo (tool: {best_tool}, score: {score})")
                    return {
                        "success": False,
                        "error": "Nenhuma tool adequada encontrada para esta query"
                    }
                
                tool_class = best_tool.__class__
                tool_name = tool_class.__name__
                print(f"[MULTI-DECK] ✅ Tool identificada via semantic matching: {tool_name} (score: {score:.2f})")
                
            except Exception as e:
                print(f"[MULTI-DECK] ❌ Erro ao identificar tool: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": f"Erro ao identificar tool: {str(e)}"}
        
        # 2. Executar em paralelo nos N decks
        print(f"[MULTI-DECK] ========== EXECUTANDO TOOL EM {len(self.selected_decks)} DECKS ==========")
        print(f"[MULTI-DECK] Tool: {tool_name}")
        print(f"[MULTI-DECK] Decks a processar: {self.selected_decks}")
        
        deck_results = {}
        try:
            max_workers = min(len(self.selected_decks), 8)  # Limitar workers
            print(f"[MULTI-DECK] Usando {max_workers} workers para processamento paralelo")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._execute_tool_safe, tool_class, self.deck_paths[deck_name], query
                    ): deck_name
                    for deck_name in self.selected_decks
                }
                print(f"[MULTI-DECK] ✅ {len(futures)} futures criados para processamento paralelo")
                
                completed_count = 0
                for future in as_completed(futures):
                    deck_name = futures[future]
                    completed_count += 1
                    try:
                        result = future.result()
                        deck_results[deck_name] = result
                        display_name = self.deck_display_names.get(deck_name, deck_name)
                        print(f"[MULTI-DECK] ✅ [{completed_count}/{len(futures)}] Deck {display_name} ({deck_name}) processado: success={result.get('success', False)}")
                    except Exception as e:
                        display_name = self.deck_display_names.get(deck_name, deck_name)
                        print(f"[MULTI-DECK] ❌ [{completed_count}/{len(futures)}] Erro ao processar deck {display_name} ({deck_name}): {e}")
                        import traceback
                        traceback.print_exc()
                        deck_results[deck_name] = {"success": False, "error": str(e)}
                
                print(f"[MULTI-DECK] ========== PROCESSAMENTO PARALELO CONCLUÍDO ==========")
                print(f"[MULTI-DECK] Total de decks processados: {len(deck_results)}")
                print(f"[MULTI-DECK] Decks com sucesso: {sum(1 for r in deck_results.values() if r.get('success', False))}")
                print(f"[MULTI-DECK] Decks com erro: {sum(1 for r in deck_results.values() if not r.get('success', False))}")
            
            print(f"[MULTI-DECK] ✅ Execução concluída em {len(deck_results)} decks")
            
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro na execução: {e}")
            return {"success": False, "error": f"Erro ao executar tool: {str(e)}"}
        
        # 3. Formatar e comparar resultados
        return self._build_comparison_result_multi(deck_results, tool_name, query)
    
    def _execute_tool_safe(self, tool_class, deck_path: str, query: str) -> Dict[str, Any]:
        """Executa uma tool de forma segura."""
        import traceback
        try:
            print(f"[MULTI-DECK] [DEBUG] Iniciando execução da tool {tool_class.__name__} no deck: {deck_path}")
            tool = tool_class(deck_path)
            result = tool.execute(query)
            
            # Verificar se o resultado indica sucesso ou falha
            if result is None:
                print(f"[MULTI-DECK] [ERRO] Tool retornou None para deck: {deck_path}")
                return {"success": False, "error": "Tool retornou None"}
            
            # Verificar se result tem campo success
            if isinstance(result, dict):
                success = result.get("success", True)  # Default True se não especificado
                if not success:
                    error_msg = result.get("error", "Erro desconhecido")
                    print(f"[MULTI-DECK] [ERRO] Tool retornou success=False para deck {deck_path}: {error_msg}")
                else:
                    # Verificar se há dados válidos
                    data = result.get("data", [])
                    dados = result.get("dados", [])  # ConfhdTool, DsvaguaTool, etc.
                    dados_volume_inicial = result.get("dados_volume_inicial", [])  # VariacaoReservatorioInicialTool
                    dados_estruturais = result.get("dados_estruturais", [])
                    dados_conjunturais = result.get("dados_conjunturais", [])
                    dados_por_submercado = result.get("dados_por_submercado", {})
                    comparison_table = result.get("comparison_table", [])  # MudancasGeracoesTermicasTool
                    
                    has_data = (
                        (isinstance(data, list) and len(data) > 0) or
                        (isinstance(dados, list) and len(dados) > 0) or
                        (isinstance(dados_volume_inicial, list) and len(dados_volume_inicial) > 0) or
                        (isinstance(dados_estruturais, list) and len(dados_estruturais) > 0) or
                        (isinstance(dados_conjunturais, list) and len(dados_conjunturais) > 0) or
                        (isinstance(dados_por_submercado, dict) and len(dados_por_submercado) > 0) or
                        (isinstance(comparison_table, list) and len(comparison_table) > 0)
                    )
                    
                    if not has_data:
                        print(f"[MULTI-DECK] [AVISO] Tool executou com sucesso mas não retornou dados para deck: {deck_path}")
                        print(f"[MULTI-DECK] [DEBUG] Campos no resultado: {list(result.keys())}")
                    else:
                        print(f"[MULTI-DECK] [OK] Tool executou com sucesso para deck: {deck_path} (dados encontrados)")
            
            return result
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"[MULTI-DECK] [ERRO] Erro ao executar tool {tool_class.__name__} no deck {deck_path}: {e}")
            print(f"[MULTI-DECK] [ERRO] Traceback completo:\n{error_trace}")
            return {"success": False, "error": str(e), "error_type": type(e).__name__, "traceback": error_trace}
    
    def _extract_data_from_result(self, result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados do resultado da tool, verificando multiplos campos possiveis.
        Cada tool pode retornar dados em campos diferentes.
        
        Campos verificados (em ordem de prioridade):
        - data: campo padrao para a maioria das tools
        - dados_estruturais: ClastValoresTool (custos estruturais)
        - dados_conjunturais: ClastValoresTool (custos conjunturais)
        - dados_expansoes: ExptOperacaoTool
        - dados_por_tipo: ModifOperacaoTool (dicionario de listas)
        """
        if not result:
            return []
        
        # Campos de dados em ordem de prioridade
        data_fields = [
            "data",
            "dados",  # ConfhdTool, DsvaguaTool, UsinasNaoSimuladasTool, RestricaoEletricaTool
            "dados_volume_inicial",  # VariacaoReservatorioInicialTool
            "comparison_table",  # MudancasGeracoesTermicasTool
            "dados_estruturais",  # ClastValoresTool
            "dados_conjunturais",  # ClastValoresTool
            "dados_expansoes",  # ExptOperacaoTool
        ]
        
        for field in data_fields:
            data = result.get(field)
            if data and isinstance(data, list) and len(data) > 0:
                print(f"[MULTI-DECK] Dados encontrados no campo '{field}': {len(data)} registros")
                return data
        
        # Verificar dados_por_tipo (dicionario de listas)
        dados_por_tipo = result.get("dados_por_tipo")
        if dados_por_tipo and isinstance(dados_por_tipo, dict):
            # Concatenar todas as listas
            all_data = []
            for tipo, dados in dados_por_tipo.items():
                if isinstance(dados, list):
                    all_data.extend(dados)
            if all_data:
                print(f"[MULTI-DECK] Dados encontrados em 'dados_por_tipo': {len(all_data)} registros")
                return all_data
        
        print(f"[MULTI-DECK] [AVISO] Nenhum dado encontrado nos campos conhecidos")
        print(f"[MULTI-DECK]   Campos disponiveis: {list(result.keys())}")
        return []
    
    def _build_comparison_result_multi(
        self,
        deck_results: Dict[str, Dict[str, Any]],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Constrói o resultado da comparação para N decks.
        
        Formato:
        - decks: Lista de resultados por deck (ordenados cronologicamente)
        - differences: Tabela comparativa
        - chart_data: Dados para gráfico com N séries
        """
        # Extrair dados de cada deck (ordenados cronologicamente)
        decks_data = []
        for deck_name in self.selected_decks:  # Já está ordenado cronologicamente
            result = deck_results.get(deck_name, {})
            display_name = self.deck_display_names.get(deck_name, deck_name)
            
            # Debug: verificar o que veio no resultado
            print(f"[MULTI-DECK] [DEBUG] Processando deck: {display_name} ({deck_name})")
            print(f"[MULTI-DECK] [DEBUG] Resultado tem 'success': {'success' in result}")
            if 'success' in result:
                print(f"[MULTI-DECK] [DEBUG] success = {result.get('success')}")
            if 'error' in result:
                print(f"[MULTI-DECK] [DEBUG] error = {result.get('error')}")
            print(f"[MULTI-DECK] [DEBUG] Campos no resultado: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            data = self._extract_data_from_result(result)
            
            # Preservar o resultado completo original para que os formatters possam acessar
            # campos como dados_estruturais, dados_conjunturais, etc.
            full_result = result.copy() if result else {}
            
            # Determinar sucesso: verificar se result indica sucesso E se há dados
            result_success = result.get("success", True)  # Default True se não especificado
            has_data = len(data) > 0
            final_success = result_success and has_data
            
            if not final_success:
                if not result_success:
                    print(f"[MULTI-DECK] [FALHA] Deck {display_name} falhou: result.success = False")
                    if 'error' in result:
                        print(f"[MULTI-DECK] [FALHA] Erro reportado: {result.get('error')}")
                elif not has_data:
                    print(f"[MULTI-DECK] [FALHA] Deck {display_name} não retornou dados: {len(data)} registros")
                    print(f"[MULTI-DECK] [DEBUG] Campos disponíveis no resultado: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            decks_data.append({
                "name": deck_name,
                "display_name": display_name,
                "success": final_success,
                "data": data,
                "error": result.get("error"),
                "full_result": full_result  # Preservar estrutura completa original
            })
            print(f"[MULTI-DECK] Dados {display_name}: {len(data)} registros, success={final_success}")
        
        # Verificar se temos dados suficientes
        decks_with_data = [d for d in decks_data if d["data"]]
        if len(decks_with_data) < 1:
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": "Dados não encontrados nos decks selecionados",
                "decks": decks_data,
                "differences": [],
                "chart_data": None
            }
        
        # Verificar se algum deck já retorna comparison_table (ex: MudancasGeracoesTermicasTool)
        # Nesse caso, preservar a estrutura original em vez de reprocessar
        first_deck_result = decks_data[0].get("full_result", {})
        stats = None
        description = None
        if "comparison_table" in first_deck_result and isinstance(first_deck_result.get("comparison_table"), list):
            print(f"[MULTI-DECK] ✅ Tool já retorna comparison_table - preservando estrutura original")
            # Preservar comparison_table, stats e description do primeiro deck (ou agregar se necessário)
            comparison_table = first_deck_result.get("comparison_table", [])
            stats = first_deck_result.get("stats", {})
            description = first_deck_result.get("description", "")
            chart_data = None  # Tools com comparison_table geralmente não têm chart_data
        else:
            # Construir tabela de comparação e gráfico normalmente
            comparison_table, chart_data = self._build_comparison_table_multi(decks_data)
        
        print(f"[MULTI-DECK] ✅ Tabela gerada: {len(comparison_table)} linhas, {len(decks_data)} decks")
        
        # Manter compatibilidade com formato antigo (deck_1, deck_2) quando são 2 decks
        result = {
            "success": True,
            "is_comparison": True,
            "is_multi_deck": len(decks_data) > 2,
            "tool_used": tool_name,
            "query": query,
            "decks": decks_data,
            "differences": comparison_table,
            "chart_data": chart_data,
            "deck_names": [d["display_name"] for d in decks_data]
        }
        
        # Preservar stats e description se disponíveis
        if stats is not None:
            result["stats"] = stats
        if description is not None:
            result["description"] = description
        
        # Adicionar deck_1 e deck_2 para compatibilidade com formatters legados
        # Incluir full_result preservando a estrutura original completa
        if len(decks_data) >= 2:
            result["deck_1"] = {
                "name": decks_data[0]["display_name"],
                "deck_name": decks_data[0]["name"],
                "success": decks_data[0]["success"],
                "data": decks_data[0]["data"],
                "error": decks_data[0].get("error"),
                "full_result": decks_data[0].get("full_result", {
                    "success": decks_data[0]["success"],
                    "data": decks_data[0]["data"],
                    "error": decks_data[0].get("error")
                })
            }
            result["deck_2"] = {
                "name": decks_data[-1]["display_name"],
                "deck_name": decks_data[-1]["name"],
                "success": decks_data[-1]["success"],
                "data": decks_data[-1]["data"],
                "error": decks_data[-1].get("error"),
                "full_result": decks_data[-1].get("full_result", {
                    "success": decks_data[-1]["success"],
                    "data": decks_data[-1]["data"],
                    "error": decks_data[-1].get("error")
                })
            }
        
        return result
    
    def _build_comparison_table_multi(
        self,
        decks_data: List[Dict[str, Any]]
    ) -> tuple:
        """
        Constrói a tabela de comparação e dados do gráfico para N decks.
        
        Returns:
            Tuple (differences_list, chart_data)
        """
        differences = []
        chart_labels = []
        chart_datasets = []
        
        # Criar índice por período para cada deck
        decks_by_period = {}
        for deck_info in decks_data:
            data = deck_info.get("data", [])
            decks_by_period[deck_info["name"]] = self._index_by_period(data)
        
        # Obter todos os períodos únicos de todos os decks
        all_periods = set()
        for periods in decks_by_period.values():
            all_periods.update(periods.keys())
        all_periods = sorted(all_periods)
        
        print(f"[MULTI-DECK] Períodos encontrados: {len(all_periods)}")
        
        # Inicializar datasets para o gráfico (um por deck)
        for deck_info in decks_data:
            chart_datasets.append({
                "label": deck_info["display_name"],
                "data": []
            })
        
        for period_key in all_periods:
            # Obter valores de cada deck para este período
            values_by_deck = {}
            sample_record = None
            
            for deck_info in decks_data:
                deck_name = deck_info["name"]
                periods_index = decks_by_period.get(deck_name, {})
                record = periods_index.get(period_key, {})
                value = self._sanitize_number(record.get("valor"))
                values_by_deck[deck_name] = value
                if record and not sample_record:
                    sample_record = record
            
            # Formatar período para exibição
            period_label = self._format_period_label(period_key, sample_record or {})
            
            # Construir linha da tabela de diferenças
            row = {"period": period_label, "field": "valor"}
            
            # Adicionar valores de cada deck
            for i, deck_info in enumerate(decks_data):
                deck_name = deck_info["name"]
                value = values_by_deck.get(deck_name)
                row[f"deck_{i+1}_value"] = round(value, 2) if value is not None else None
                row[f"deck_{i+1}_name"] = deck_info["display_name"]
                
                # Adicionar ao dataset do gráfico
                chart_datasets[i]["data"].append(round(value, 2) if value is not None else None)
            
            # Calcular diferença entre primeiro e último deck (se aplicável)
            if len(decks_data) >= 2:
                first_val = values_by_deck.get(decks_data[0]["name"])
                last_val = values_by_deck.get(decks_data[-1]["name"])
                
                if first_val is not None and last_val is not None:
                    diff_nominal = last_val - first_val
                    diff_percent = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                    diff_percent = self._sanitize_number(diff_percent) or 0
                    
                    row["difference"] = round(diff_nominal, 2)
                    row["difference_percent"] = round(diff_percent, 4)
            
            differences.append(row)
            chart_labels.append(period_label)
        
        # Construir chart_data
        chart_data = None
        if chart_labels:
            chart_data = {
                "labels": chart_labels,
                "datasets": chart_datasets
            }
        
        return differences, chart_data
    
    def _index_by_period(self, data: List[Dict]) -> Dict[str, Dict]:
        """
        Cria um índice dos dados por período.
        Suporta diferentes formatos de dados:
        - ano + mes (CargaMensalTool, etc)
        - indice_ano_estudo (ClastValoresTool)
        - ano sozinho
        
        Returns:
            Dict com chave "YYYY-MM" ou "ANO-X" e valor sendo o registro
        """
        index = {}
        
        for record in data:
            period_key = None
            
            # Formato 1: ano + mes (ex: CargaMensalTool)
            ano = record.get("ano")
            mes = record.get("mes")
            
            if ano is not None and mes is not None:
                try:
                    ano_int = int(ano)
                    mes_int = int(mes)
                    period_key = f"{ano_int:04d}-{mes_int:02d}"
                except (ValueError, TypeError):
                    pass
            
            # Formato 2: indice_ano_estudo (ex: ClastValoresTool)
            if period_key is None:
                indice_ano = record.get("indice_ano_estudo")
                if indice_ano is not None:
                    try:
                        ano_int = int(indice_ano)
                        period_key = f"ANO-{ano_int}"
                    except (ValueError, TypeError):
                        pass
            
            # Formato 3: apenas ano
            if period_key is None and ano is not None:
                try:
                    ano_int = int(ano)
                    period_key = f"{ano_int:04d}"
                except (ValueError, TypeError):
                    pass
            
            if period_key is not None:
                index[period_key] = record
        
        return index
    
    def _format_period_label(self, period_key: str, record: Dict) -> str:
        """
        Formata o período para exibição amigável.
        Ex: "2026-01" -> "Jan/2026"
        Ex: "ANO-1" -> "Ano 1"
        """
        meses_nomes = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
            5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
            9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
        }
        
        try:
            # Formato ANO-X (ClastValoresTool)
            if period_key.startswith("ANO-"):
                ano_num = int(period_key.split("-")[1])
                return f"Ano {ano_num}"
            
            parts = period_key.split("-")
            if len(parts) == 2:
                ano = int(parts[0])
                mes = int(parts[1])
                mes_nome = meses_nomes.get(mes, str(mes))
                return f"{mes_nome}/{ano}"
            elif len(parts) == 1:
                return f"Ano {parts[0]}"
        except:
            pass
        
        return period_key
    
    def _sanitize_number(self, value) -> Optional[float]:
        """
        Sanitiza um valor numérico, retornando None se for NaN ou inválido.
        """
        if value is None:
            return None
        
        try:
            float_val = float(value)
            # Verificar se é NaN ou infinito
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    def get_description(self) -> str:
        """Retorna descrição da tool."""
        return """Tool que executa outras tools em dois decks (dezembro e janeiro) 
        e compara os resultados lado a lado com gráfico comparativo."""

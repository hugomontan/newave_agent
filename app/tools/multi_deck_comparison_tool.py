"""
Tool que executa outra tool em dois decks e compara os resultados.
Versão simplificada e robusta.
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
import math
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
            self.deck_december_name = "Dezembro 2025"
            self.deck_january_name = "Janeiro 2026"
        except FileNotFoundError as e:
            print(f"[MULTI-DECK] ⚠️ Erro ao carregar decks: {e}")
            self.deck_december = None
            self.deck_january = None
    
    def can_handle(self, query: str) -> bool:
        """Retorna True se os decks estiverem disponíveis."""
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
        
        # 1. Encontrar tool correta
        try:
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
            return {"success": False, "error": f"Erro ao identificar tool: {str(e)}"}
        
        # 2. Executar em paralelo nos dois decks
        print(f"[MULTI-DECK] Executando {tool_name} em paralelo...")
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_dec = executor.submit(
                    self._execute_tool_safe, tool_class, str(self.deck_december), query
                )
                future_jan = executor.submit(
                    self._execute_tool_safe, tool_class, str(self.deck_january), query
                )
                result_dec = future_dec.result()
                result_jan = future_jan.result()
            
            print(f"[MULTI-DECK] ✅ Execução concluída")
            
        except Exception as e:
            print(f"[MULTI-DECK] ❌ Erro na execução: {e}")
            return {"success": False, "error": f"Erro ao executar tool: {str(e)}"}
        
        # 3. Formatar e comparar resultados
        return self._build_comparison_result(result_dec, result_jan, tool_name, query)
    
    def _execute_tool_safe(self, tool_class, deck_path: str, query: str) -> Dict[str, Any]:
        """Executa uma tool de forma segura."""
        try:
            tool = tool_class(deck_path)
            result = tool.execute(query)
            return result
        except Exception as e:
            print(f"[MULTI-DECK] [ERRO] Erro ao executar tool: {e}")
            return {"success": False, "error": str(e)}
    
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
    
    def _build_comparison_result(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Constrói o resultado da comparação de forma simples e direta.
        
        Formato da tabela:
        | Data | Deck Dezembro | Deck Janeiro | Diferença | Diferença % |
        """
        # Extrair dados - verificar multiplos campos possiveis
        # Cada tool pode retornar dados em campos diferentes
        data_dec = self._extract_data_from_result(result_dec)
        data_jan = self._extract_data_from_result(result_jan)
        
        print(f"[MULTI-DECK] Dados: Dezembro={len(data_dec)}, Janeiro={len(data_jan)}")
        
        if not data_dec or not data_jan:
            return {
                "success": False,
                "is_comparison": True,
                "error": "Dados não encontrados em um ou ambos os decks",
                "deck_1": {"name": self.deck_december_name, "success": bool(data_dec), "data": data_dec},
                "deck_2": {"name": self.deck_january_name, "success": bool(data_jan), "data": data_jan},
                "differences": [],
                "chart_data": None
            }
        
        # Construir tabela de comparação e gráfico
        comparison_table, chart_data = self._build_comparison_table(data_dec, data_jan)
        
        print(f"[MULTI-DECK] ✅ Tabela gerada: {len(comparison_table)} linhas")
        
        return {
            "success": True,
            "is_comparison": True,
            "tool_used": tool_name,
            "query": query,
            "deck_1": {
                "name": self.deck_december_name,
                "success": True,
                "data": data_dec
            },
            "deck_2": {
                "name": self.deck_january_name,
                "success": True,
                "data": data_jan
            },
            "differences": comparison_table,
            "chart_data": chart_data
        }
    
    def _build_comparison_table(
        self,
        data_dec: List[Dict],
        data_jan: List[Dict]
    ) -> tuple:
        """
        Constrói a tabela de comparação e dados do gráfico.
        
        Returns:
            Tuple (differences_list, chart_data)
        """
        differences = []
        chart_labels = []
        chart_values_dec = []
        chart_values_jan = []
        
        # Criar índice por período para cada deck
        dec_by_period = self._index_by_period(data_dec)
        jan_by_period = self._index_by_period(data_jan)
        
        # Obter todos os períodos únicos e ordenar
        all_periods = sorted(set(dec_by_period.keys()) | set(jan_by_period.keys()))
        
        print(f"[MULTI-DECK] Períodos encontrados: {len(all_periods)}")
        
        for period_key in all_periods:
            # Obter valores de cada deck
            dec_record = dec_by_period.get(period_key, {})
            jan_record = jan_by_period.get(period_key, {})
            
            val_dec = dec_record.get("valor")
            val_jan = jan_record.get("valor")
            
            # Formatar período para exibição
            period_label = self._format_period_label(period_key, dec_record or jan_record)
            
            # Calcular diferenças (apenas se ambos valores existem)
            if val_dec is not None and val_jan is not None:
                # Sanitizar valores (converter NaN para None)
                val_dec = self._sanitize_number(val_dec)
                val_jan = self._sanitize_number(val_jan)
                
                if val_dec is not None and val_jan is not None:
                    diff_nominal = val_jan - val_dec  # Janeiro - Dezembro
                    diff_percent = ((val_jan - val_dec) / val_dec * 100) if val_dec != 0 else 0
                    diff_percent = self._sanitize_number(diff_percent) or 0
                    
                    differences.append({
                        "period": period_label,
                        "field": "valor",
                        "deck_1_value": round(val_dec, 2),
                        "deck_2_value": round(val_jan, 2),
                        "difference": round(diff_nominal, 2),
                        "difference_percent": round(diff_percent, 4)
                    })
                    
                    # Dados para o gráfico
                    chart_labels.append(period_label)
                    chart_values_dec.append(round(val_dec, 2))
                    chart_values_jan.append(round(val_jan, 2))
        
        # Construir chart_data
        chart_data = None
        if chart_labels:
            chart_data = {
                "labels": chart_labels,
                "datasets": [
                    {
                        "label": self.deck_december_name,
                        "data": chart_values_dec
                    },
                    {
                        "label": self.deck_january_name,
                        "data": chart_values_jan
                    }
                ]
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

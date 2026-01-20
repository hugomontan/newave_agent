"""
Tool Multi-Deck para consultar gerações de pequenas usinas (PQ) em múltiplos decks DECOMP.
Executa PQPequenasUsinasTool em paralelo em todos os decks selecionados.
SEMPRE usa apenas estágio 1 para cálculo de MW médio ponderado.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.tools.pq_pequenas_usinas_tool import PQPequenasUsinasTool
from decomp_agent.app.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from decomp_agent.app.config import safe_print
import multiprocessing
import re


class PQMultiDeckTool(DECOMPTool):
    """
    Tool para consultar gerações de pequenas usinas (PQ) em múltiplos decks DECOMP.
    
    Executa PQPequenasUsinasTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    IMPORTANTE: SEMPRE usa apenas estágio 1 para cálculo de MW médio ponderado.
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de PQ.
        
        Args:
            deck_paths: Dict mapeando nome do deck para seu caminho (ex: {"DC202501-sem1": "/path/to/deck"})
        """
        # Usar o primeiro deck como deck_path base (para compatibilidade com DECOMPTool)
        first_deck_path = list(deck_paths.values())[0] if deck_paths else ""
        super().__init__(first_deck_path)
        self.deck_paths = deck_paths
        self.deck_display_names = {
            name: get_deck_display_name(name) 
            for name in deck_paths.keys()
        }
        # OTIMIZAÇÃO: Calcular workers ótimos baseado em CPU cores
        self.max_workers = min(len(deck_paths), max(multiprocessing.cpu_count() * 2, 8))
    
    def get_name(self) -> str:
        return "PQMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre gerações de pequenas usinas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "pequenas usinas",
            "geração pequenas usinas",
            "geracoes pequenas usinas",
            "bloco pq",
            "registro pq",
            "pq decomp",
            "pch", "pct", "eol", "ufv",
            "pchgd", "pctgd", "eolgd", "ufvgd",
            "pequenas centrais",
            "eólica", "fotovoltaica",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar gerações de pequenas usinas (Bloco PQ) em múltiplos decks DECOMP.
        
        Executa PQPequenasUsinasTool em paralelo em todos os decks selecionados,
        SEMPRE usando apenas estágio 1 para cálculo de MW médio ponderado.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal (timeseries) por tipo de geração.
        
        OTIMIZADO para máxima performance com paralelismo inteligente.
        """
    
    def _extract_tipo_from_query(self, query: str) -> Optional[str]:
        """
        Extrai tipo de geração da query (PCH, PCT, EOL, UFV, etc.).
        
        LÓGICA SIMPLES:
        - Se "gd" aparecer em QUALQUER lugar da query → retorna tipo+GD (ex: EOLGD)
        - Se "gd" NÃO aparecer → retorna apenas tipo base (ex: EOL)
        
        Args:
            query: Query do usuário
            
        Returns:
            Tipo extraído em UPPERCASE (EOL, EOLGD, PCH, PCHGD, etc.) ou None
        """
        query_lower = query.lower()
        
        # Verificar se "gd" aparece em qualquer lugar da query
        tem_gd = "gd" in query_lower
        
        # Mapeamento de termos para tipos base
        termos_tipo = {
            "pch": "PCH",
            "pct": "PCT",
            "eol": "EOL",
            "eólica": "EOL",
            "eolica": "EOL",
            "vento": "EOL",
            "ufv": "UFV",
            "fotovoltaica": "UFV",
            "fotovoltaico": "UFV",
            "solar": "UFV",
        }
        
        # Buscar tipo base na query
        tipo_base = None
        for termo, tipo in termos_tipo.items():
            if termo in query_lower:
                tipo_base = tipo
                break
        
        # Fallback: buscar por padrões regex
        if not tipo_base:
            pattern = r'\b(PCH|PCT|EOL|UFV)\b'
            match = re.search(pattern, query.upper())
            if match:
                tipo_base = match.group(1)
        
        if not tipo_base:
            return None
        
        # Se "gd" aparece na query, adicionar GD ao tipo
        if tem_gd:
            return f"{tipo_base}GD"
        else:
            return tipo_base
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de gerações de pequenas usinas em paralelo em todos os decks.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com resultados agregados de todos os decks
        """
        if not self.deck_paths:
            return {
                "success": False,
                "error": "Nenhum deck disponível para comparação"
            }
        
        # Extrair tipo da query para validação
        tipo_filtrado = self._extract_tipo_from_query(query)
        
        safe_print(f"[PQ MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[PQ MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[PQ MULTI-DECK] Tipo filtrado: {tipo_filtrado or 'TODOS'}")
        safe_print(f"[PQ MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[PQ MULTI-DECK] Workers: {self.max_workers}")
        
        # Executar consulta em paralelo
        safe_print(f"[PQ MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
        deck_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._execute_single_deck,
                    deck_name,
                    deck_path,
                    query
                ): deck_name
                for deck_name, deck_path in self.deck_paths.items()
            }
            
            for future in as_completed(futures):
                deck_name = futures[future]
                try:
                    result = future.result(timeout=30)
                    
                    date = None
                    if deck_name and "-" in deck_name:
                        parsed = parse_deck_name(deck_name)
                        if parsed and parsed.get("week"):
                            date = calculate_week_thursday(
                                parsed["year"],
                                parsed["month"],
                                parsed["week"]
                            )
                    
                    if result.get("success") and date:
                        result["date"] = date
                    
                    # IMPORTANTE: Tratar decks sem dados como sucesso (será 0 em comparações)
                    sem_dados = result.get("sem_dados", False)
                    success = result.get("success", False) or sem_dados
                    
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": result,
                        "success": success,
                        "error": result.get("error") if not success else None,
                        "date": date
                    })
                    
                    if success:
                        data_count = len(result.get("data", []))
                        if sem_dados:
                            # Extrair informações da região e tipo para mensagem
                            filtros = result.get("filtros", {})
                            regiao = filtros.get("regiao", "região não especificada")
                            tipo = filtros.get("tipo_encontrado") or filtros.get("tipo", "tipo não especificado")
                            safe_print(f"[PQ MULTI-DECK] ⚠️ {deck_name}: Sem dados para tipo '{tipo}' na região '{regiao}' (será tratado como 0)")
                        else:
                            safe_print(f"[PQ MULTI-DECK] ✅ {deck_name}: {data_count} registros processados")
                    else:
                        safe_print(f"[PQ MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[PQ MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[PQ MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": str(e),
                        "date": None
                    })
        
        successful_results = [r for r in deck_results if r["success"]]
        
        if len(successful_results) == 0:
            return {
                "success": False,
                "error": "Nenhum deck foi processado com sucesso",
                "decks": deck_results
            }
        
        if any(r.get("date") for r in deck_results):
            deck_results.sort(key=lambda x: (
                x.get("date") or "9999-99-99",
                x["name"]
            ))
        
        # Obter tipo REAL encontrado nos dados (não o tipo da query)
        tipo_encontrado_real = tipo_filtrado  # Fallback para tipo da query
        for deck_result in successful_results:
            result = deck_result.get("result", {})
            # Verificar se há tipo_encontrado no resultado
            if result.get("tipo_encontrado"):
                tipo_encontrado_real = result.get("tipo_encontrado")
                break
            # Fallback: extrair do primeiro registro de data
            elif result.get("data") and len(result.get("data", [])) > 0:
                primeiro_registro = result.get("data")[0]
                if primeiro_registro.get("tipo"):
                    tipo_encontrado_real = primeiro_registro.get("tipo")
                    break
        
        safe_print(f"[PQ MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[PQ MULTI-DECK] Tipo encontrado REAL: {tipo_encontrado_real} (query: {tipo_filtrado})")
        safe_print(f"[PQ MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "tool_name": "PQPequenasUsinasTool",
            "tipo_filtrado": tipo_filtrado,  # Tipo da query
            "tipo_encontrado": tipo_encontrado_real  # IMPORTANTE: Tipo REAL encontrado nos dados
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Executa PQPequenasUsinasTool em um único deck.
        IMPORTANTE: Sempre usa estágio 1 para cálculo de MW médio ponderado.
        """
        try:
            tool = PQPequenasUsinasTool(deck_path)
            
            # A tool já tem lógica para sempre usar estágio 1 e calcular MW médio
            result = tool.execute(query, verbose=False)
            
            # Garantir que o resultado tenha apenas estágio 1 e MW médio calculado
            if result.get("success") and result.get("data"):
                data = result.get("data", [])
                # Filtrar dados para garantir que apenas estágio 1 está presente
                filtered_data = [
                    d for d in data 
                    if d.get("estagio") == 1 or d.get("estagio") is None
                ]
                result["data"] = filtered_data
                
                # Extrair MW médios dos dados para facilitar o processamento no formatter
                mw_medios = []
                for record in filtered_data:
                    mw_medio = record.get("mw_medio")
                    tipo = record.get("tipo")
                    nome = record.get("nome")
                    regiao = record.get("regiao")
                    
                    if mw_medio is not None and tipo:
                        mw_medios.append({
                            "tipo": tipo,
                            "nome": nome,
                            "regiao": regiao,
                            "mw_medio": mw_medio
                        })
                
                if mw_medios:
                    result["mw_medios"] = mw_medios
            
            return result
        except Exception as e:
            safe_print(f"[PQ MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

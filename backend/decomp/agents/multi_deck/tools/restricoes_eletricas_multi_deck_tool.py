"""
Tool Multi-Deck para consultar restrições elétricas em múltiplos decks DECOMP.
Executa RestricoesEletricasDECOMPTool em paralelo em todos os decks selecionados.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.restricoes_eletricas_tool import RestricoesEletricasDECOMPTool
from backend.decomp.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from backend.decomp.config import safe_print
import multiprocessing


class RestricoesEletricasMultiDeckTool(DECOMPTool):
    """
    Tool para consultar restrições elétricas em múltiplos decks DECOMP.
    
    Executa RestricoesEletricasDECOMPTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    OTIMIZAÇÕES APLICADAS:
    - Execução paralela de consultas
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de restrições elétricas.
        
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
        return "RestricoesEletricasMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre restrições elétricas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "restricao eletrica",
            "restrição elétrica",
            "restricoes eletricas",
            "restrições elétricas",
            "restrição re",
            "bloco re",
            "registro re",
            "restricao de",
            "restrição de",
            "qual a restricao",
            "qual a restrição",
            "gmin", "gmax",
            "limites minimos",
            "limites maximos",
            "limite minimo",
            "limite maximo",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar restrições elétricas (bloco RE/LU) em múltiplos decks DECOMP.
        
        Esta tool permite consultar restrições elétricas por nome (ex: SEFAC, SERRA DO FACAO, CORUMBA I)
        em múltiplos decks, retornando os valores de GMIN (limite mínimo) e GMAX (limite máximo)
        por patamar para cada restrição.
        
        Executa a consulta de restrições elétricas em paralelo em todos os decks selecionados,
        retornando valores de GMIN e GMAX por patamar para comparação temporal.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal e comparação entre decks.
        
        Use para consultar: restrições elétricas, bloco RE, registro RE, limites elétricos,
        restrição de [NOME], GMIN, GMAX, limites mínimos e máximos de restrições.
        
        OTIMIZADO para máxima performance com paralelismo inteligente.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de restrições elétricas em paralelo em todos os decks.
        
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
        
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] Workers: {self.max_workers}")
        
        # Executar consultas em paralelo
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] Executando consultas em {len(self.deck_paths)} decks em paralelo...")
        
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
                    result = future.result(timeout=60)
                    
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
                    
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": result,
                        "success": result.get("success", False),
                        "error": result.get("error"),
                        "date": date
                    })
                    
                    if result.get("success"):
                        data_count = len(result.get("data", []))
                        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ✅ {deck_name}: {data_count} registro(s)")
                    else:
                        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
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
                "decks": deck_results,
                "tool_name": "RestricoesEletricasDECOMPTool"
            }
        
        # Ordenar por data
        if any(r.get("date") for r in deck_results):
            deck_results.sort(key=lambda x: (
                x.get("date") or "9999-99-99",
                x["name"]
            ))
        
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "is_multi_deck": True,
            "decks": deck_results,
            "tool_name": "RestricoesEletricasDECOMPTool"
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        query: str
    ) -> Dict[str, Any]:
        """Executa RestricoesEletricasDECOMPTool em um único deck."""
        try:
            tool = RestricoesEletricasDECOMPTool(deck_path)
            result = tool.execute(query)
            return result
        except Exception as e:
            safe_print(f"[RESTRICOES ELETRICAS MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

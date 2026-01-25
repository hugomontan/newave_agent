"""
Tool Multi-Deck para consultar carga ANDE em múltiplos decks DECOMP.
Executa CargaAndeTool em paralelo em todos os decks selecionados.
SEMPRE usa apenas estágio 1 para carga média ponderada.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.carga_ande_tool import CargaAndeTool
from backend.decomp.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from backend.decomp.config import safe_print
import multiprocessing


class CargaAndeMultiDeckTool(DECOMPTool):
    """
    Tool para consultar carga ANDE em múltiplos decks DECOMP.
    
    Executa CargaAndeTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    IMPORTANTE: SEMPRE usa apenas estágio 1 para carga média ponderada.
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de Carga ANDE.
        
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
        return "CargaAndeMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga ANDE.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "carga ande",
            "ande itaipu",
            "participação ande",
            "participacao ande",
            "ande",
            "bloco ri ande",
            "restrição itaipu ande",
            "restricao itaipu ande",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar carga ANDE em múltiplos decks DECOMP.
        
        Executa CargaAndeTool em paralelo em todos os decks selecionados,
        SEMPRE usando apenas estágio 1 para carga média ponderada.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal (timeseries).
        
        OTIMIZADO para máxima performance com paralelismo inteligente.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de carga ANDE em paralelo em todos os decks.
        
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
        
        safe_print(f"[CARGA ANDE MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[CARGA ANDE MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[CARGA ANDE MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[CARGA ANDE MULTI-DECK] Workers: {self.max_workers}")
        
        # Executar consulta em paralelo
        safe_print(f"[CARGA ANDE MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
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
                    
                    # Extrair carga ANDE ponderada do resultado
                    carga_ande_ponderada = None
                    if result.get("success") and result.get("data"):
                        data = result.get("data", [])
                        if data:
                            primeiro_registro = data[0]
                            carga_ande_ponderada = (
                                primeiro_registro.get("carga_ande_media_ponderada") or
                                primeiro_registro.get("mw_medio")
                            )
                    
                    # Adicionar carga_ande_ponderada ao result para facilitar acesso no formatter
                    if carga_ande_ponderada is not None:
                        result["carga_ande_ponderada"] = carga_ande_ponderada
                    
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": result,
                        "success": result.get("success", False),
                        "error": result.get("error"),
                        "date": date,
                        "carga_ande_ponderada": carga_ande_ponderada
                    })
                    
                    if result.get("success"):
                        safe_print(f"[CARGA ANDE MULTI-DECK] ✅ {deck_name}: Carga ANDE = {carga_ande_ponderada} MW")
                    else:
                        safe_print(f"[CARGA ANDE MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[CARGA ANDE MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None,
                        "carga_ande_ponderada": None
                    })
                except Exception as e:
                    safe_print(f"[CARGA ANDE MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": str(e),
                        "date": None,
                        "carga_ande_ponderada": None
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
        
        safe_print(f"[CARGA ANDE MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[CARGA ANDE MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "tool_name": "CargaAndeTool"
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Executa CargaAndeTool em um único deck.
        IMPORTANTE: Sempre usa estágio 1 para carga média ponderada.
        """
        try:
            tool = CargaAndeTool(deck_path)
            
            # A tool já tem lógica para assumir estágio 1
            result = tool.execute(query, verbose=False)
            
            return result
        except Exception as e:
            safe_print(f"[CARGA ANDE MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

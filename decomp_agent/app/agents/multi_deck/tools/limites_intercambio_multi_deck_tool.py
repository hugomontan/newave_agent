"""
Tool Multi-Deck para consultar limites de intercâmbio em múltiplos decks DECOMP.
Executa LimitesIntercambioDECOMPTool em paralelo em todos os decks selecionados.
SEMPRE usa apenas estágio 1 para MW médio ponderado.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.tools.limites_intercambio_tool import LimitesIntercambioDECOMPTool
from decomp_agent.app.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from decomp_agent.app.config import safe_print
import multiprocessing


class LimitesIntercambioMultiDeckTool(DECOMPTool):
    """
    Tool para consultar limites de intercâmbio em múltiplos decks DECOMP.
    
    Executa LimitesIntercambioDECOMPTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    IMPORTANTE: SEMPRE usa apenas estágio 1 para MW médio ponderado.
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de Limites de Intercâmbio.
        
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
        return "LimitesIntercambioMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre limites de intercâmbio.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        keywords = [
            "limite de intercambio",
            "limite de intercâmbio",
            "limites de intercambio",
            "limites de intercâmbio",
            "intercambio entre",
            "intercâmbio entre",
            "limite de",
            "limite para",
            "limite entre",
            "registro ia",
        ]
        
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar limites de intercâmbio em múltiplos decks DECOMP.
        
        Executa LimitesIntercambioDECOMPTool em paralelo em todos os decks selecionados,
        SEMPRE usando apenas estágio 1 para MW médio ponderado.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal (timeseries).
        
        OTIMIZADO para máxima performance com paralelismo inteligente.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de limites de intercâmbio em paralelo em todos os decks.
        
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
        
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] Workers: {self.max_workers}")
        
        # Executar consulta em paralelo
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
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
                    
                    # Extrair MW médios de cada sentido do resultado
                    mw_medios_por_sentido = {}
                    if result.get("success") and result.get("data"):
                        data = result.get("data", [])
                        for record in data:
                            # MW médio DE->PARA
                            mw_medio_de_para = record.get("mw_medio_de_para")
                            if mw_medio_de_para is not None:
                                sub_de = record.get("sub_de", "?")
                                sub_para = record.get("sub_para", "?")
                                sentido_key = f"{sub_de}→{sub_para}"
                                mw_medios_por_sentido[sentido_key] = {
                                    "sentido": f"{sub_de} → {sub_para}",
                                    "mw_medio": mw_medio_de_para,
                                    "sub_de": sub_de,
                                    "sub_para": sub_para
                                }
                            
                            # MW médio PARA->DE
                            mw_medio_para_de = record.get("mw_medio_para_de")
                            if mw_medio_para_de is not None:
                                sub_de = record.get("sub_de", "?")
                                sub_para = record.get("sub_para", "?")
                                sentido_key = f"{sub_para}→{sub_de}"
                                mw_medios_por_sentido[sentido_key] = {
                                    "sentido": f"{sub_para} → {sub_de}",
                                    "mw_medio": mw_medio_para_de,
                                    "sub_de": sub_para,
                                    "sub_para": sub_de
                                }
                    
                    # Adicionar mw_medios_por_sentido ao result para facilitar acesso no formatter
                    if mw_medios_por_sentido:
                        result["mw_medios_por_sentido"] = mw_medios_por_sentido
                    
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": result,
                        "success": result.get("success", False),
                        "error": result.get("error"),
                        "date": date,
                        "mw_medios_por_sentido": mw_medios_por_sentido
                    })
                    
                    if result.get("success"):
                        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ✅ {deck_name}: {len(mw_medios_por_sentido)} sentidos encontrados")
                    else:
                        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None,
                        "mw_medios_por_sentido": {}
                    })
                except Exception as e:
                    safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": str(e),
                        "date": None,
                        "mw_medios_por_sentido": {}
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
        
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "tool_name": "LimitesIntercambioDECOMPTool"
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Executa LimitesIntercambioDECOMPTool em um único deck.
        IMPORTANTE: Sempre usa estágio 1 para MW médio ponderado.
        """
        try:
            tool = LimitesIntercambioDECOMPTool(deck_path)
            
            # A tool já tem lógica para assumir estágio 1
            result = tool.execute(query)
            
            return result
        except Exception as e:
            safe_print(f"[LIMITES INTERCAMBIO MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

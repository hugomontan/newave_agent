"""
Tool Multi-Deck para consultar carga dos subsistemas (DP) em múltiplos decks DECOMP.
Executa DPCargaSubsistemasTool em paralelo em todos os decks selecionados.
SEMPRE usa apenas estágio 1 para carga média ponderada.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.dp_carga_subsistemas_tool import DPCargaSubsistemasTool
from backend.decomp.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from backend.decomp.config import safe_print
import multiprocessing


class DPMultiDeckTool(DECOMPTool):
    """
    Tool para consultar carga dos subsistemas (DP) em múltiplos decks DECOMP.
    
    Executa DPCargaSubsistemasTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    IMPORTANTE: SEMPRE usa apenas estágio 1 para carga média ponderada.
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de DP.
        
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
        return "DPMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga dos subsistemas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        # Excluir explicitamente carga mensal (deve ser CargaMensalTool do NEWAVE)
        if "carga mensal" in query_lower or "demanda mensal" in query_lower:
            return False
        
        keywords = [
            "carga dos subsistemas",
            "carga subsistemas",
            "demanda subsistemas",
            "demanda dos subsistemas",
            "bloco dp",
            "registro dp",
            "dp decomp",
            "patamares de carga",
            "patamares carga",
            "duração patamares",
            "duracao patamares",
            "demanda por patamar",
            "carga por patamar",
            "mwmed",
            "mw médio",
            "mw medio",
            "carga média ponderada",
            "carga media ponderada",
            "calcular carga média",
            "calcular carga media",
            "carga média dos patamares",
            "carga media dos patamares",
            "média ponderada carga",
            "media ponderada carga",
            "calcular mw médio",
            "calcular mw medio",
            "carga ponderada",
            "demanda média ponderada",
            "demanda media ponderada",
        ]
        
        # Verificar se há keywords relacionados a carga/patamares
        tem_keyword = any(kw in query_lower for kw in keywords)
        
        # Verificar se menciona algum nome de submercado junto com termos relacionados a carga/patamares
        nomes_submercados = ["sudeste", "sul", "nordeste", "norte"]
        tem_nome_submercado = any(nome in query_lower for nome in nomes_submercados)
        tem_termo_carga = any(termo in query_lower for termo in [
            "carga", "demanda", "patamar", "mw", "média", "media", "ponderada"
        ])
        
        # Se menciona nome de submercado E termos relacionados a carga, também pode processar
        return tem_keyword or (tem_nome_submercado and tem_termo_carga)
    
    def get_description(self) -> str:
        return """
        Tool para consultar carga/demanda dos subsistemas (Bloco DP) em múltiplos decks DECOMP.
        
        Responde perguntas como:
        - Qual a carga do Sudeste?
        - Qual a demanda do Sul?
        - Carga do Nordeste
        - Demanda do Norte
        - Carga de todos os subsistemas
        - Patamares de carga por submercado
        
        Subsistemas disponíveis: Sudeste, Sul, Nordeste, Norte.
        
        Executa DPCargaSubsistemasTool em paralelo em todos os decks selecionados,
        usando estágio 1 para carga média ponderada.
        
        Retorna resultados agregados com datas calculadas para visualização temporal.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de carga dos subsistemas em paralelo em todos os decks.
        
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
        
        safe_print(f"[DP MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[DP MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[DP MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[DP MULTI-DECK] Workers: {self.max_workers}")
        
        # Executar consulta em paralelo
        safe_print(f"[DP MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
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
                    
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": result,
                        "success": result.get("success", False),
                        "error": result.get("error"),
                        "date": date
                    })
                    
                    if result.get("success"):
                        mw_medios_count = len(result.get("mw_medios", []))
                        safe_print(f"[DP MULTI-DECK] ✅ {deck_name}: {mw_medios_count} MW médios calculados")
                    else:
                        safe_print(f"[DP MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[DP MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[DP MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
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
        
        safe_print(f"[DP MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[DP MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "tool_name": "DPCargaSubsistemasTool"
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Executa DPCargaSubsistemasTool em um único deck.
        IMPORTANTE: Sempre usa estágio 1 para carga média ponderada.
        """
        try:
            tool = DPCargaSubsistemasTool(deck_path)
            
            # A tool já tem lógica para assumir estágio 1 quando não especificado
            # e calcular MW médio automaticamente
            result = tool.execute(query, verbose=False)
            
            # Garantir que o resultado tenha apenas estágio 1 e MW médio calculado
            if result.get("success") and result.get("data"):
                data = result.get("data", [])
                # Filtrar dados para garantir que apenas estágio 1 está presente
                filtered_data = [
                    d for d in data 
                    if d.get("estagio") == 1 or d.get("estágio") == 1 or d.get("estagio") is None
                ]
                result["data"] = filtered_data
                
                # Extrair MW médios dos dados para facilitar o processamento no formatter
                mw_medios = []
                calcular_media = result.get("calcular_media_ponderada", False)
                
                if calcular_media or any("mw_medio" in d for d in filtered_data):
                    for record in filtered_data:
                        mw_medio = record.get("mw_medio") or record.get("carga_media_ponderada")
                        if mw_medio is not None:
                            estagio = record.get("estagio") or record.get("ip")
                            codigo_submercado = (
                                record.get("codigo_submercado") or 
                                record.get("submercado") or 
                                record.get("s")
                            )
                            if codigo_submercado is not None:
                                mw_medios.append({
                                    "estagio": estagio,
                                    "codigo_submercado": codigo_submercado,
                                    "mw_medio": mw_medio
                                })
                
                if mw_medios:
                    result["mw_medios"] = mw_medios
            
            return result
        except Exception as e:
            safe_print(f"[DP MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

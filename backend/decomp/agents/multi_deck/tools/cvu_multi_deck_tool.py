"""
Tool Multi-Deck para consultar CVU de usinas térmicas em múltiplos decks DECOMP.
Executa CTUsinasTermelétricasTool em paralelo em todos os decks selecionados.
SEMPRE usa apenas estágio 1 para CVU.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.ct_usinas_termelétricas_tool import CTUsinasTermelétricasTool
from backend.decomp.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import multiprocessing


class CVUMultiDeckTool(DECOMPTool):
    """
    Tool para consultar CVU de usinas térmicas em múltiplos decks DECOMP.
    
    Executa CTUsinasTermelétricasTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    IMPORTANTE: SEMPRE usa apenas estágio 1 para CVU, ignorando qualquer especificação.
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Pré-processamento de arquivos dadger
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    - Otimização de filtragem de DataFrames
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de CVU.
        
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
        return "CVUMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre CVU de usina.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "cvu",
            "cvu usina",
            "cvu da usina",
            "custo variável",
            "custo variavel",
            "cvu de",
            "cvu cubatao",
            "cvu angra",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar CVU (Custo Variável Unitário) de uma usina termelétrica em múltiplos decks DECOMP.
        
        Executa CTUsinasTermelétricasTool em paralelo em todos os decks selecionados,
        SEMPRE usando apenas estágio 1 para CVU.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal.
        
        OTIMIZADO para máxima performance com paralelismo inteligente.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de CVU em paralelo em todos os decks.
        
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
        
        safe_print(f"[CVU MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[CVU MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[CVU MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[CVU MULTI-DECK] Workers: {self.max_workers}")

        # Permitir correção de usina via follow-up (forced_plant_code)
        forced_plant_code = kwargs.get("forced_plant_code")
        
        # OTIMIZAÇÃO 1: Carregar dadgers em paralelo primeiro
        safe_print(f"[CVU MULTI-DECK] Carregando {len(self.deck_paths)} dadgers em paralelo...")
        dadger_cache = self._load_all_dadgers_parallel()
        
        safe_print(f"[CVU MULTI-DECK] ✅ {len(dadger_cache)}/{len(self.deck_paths)} dadgers carregados")
        
        # OTIMIZAÇÃO 2: Identificar usina usando o MESMO pipeline da CTUsinasTermelétricasTool
        safe_print(f"[CVU MULTI-DECK] Tentando identificar usina da query (pipeline CT): '{query}'")
        
        # Importar o matcher térmico DECOMP (mesmo usado em CTUsinasTermelétricasTool)
        from backend.decomp.utils.thermal_plant_matcher import get_decomp_thermal_plant_matcher
        
        # Montar lista de usinas disponíveis a partir dos dadgers carregados
        available_plants: list = []
        decks_to_check = min(5, len(dadger_cache))
        checked_decks = 0
        
        for deck_name, dadger in dadger_cache.items():
            if checked_decks >= decks_to_check:
                break
            
            try:
                # IMPORTANTE: Sempre usar estágio 1 para CVU
                ct_df = dadger.ct(estagio=1, df=True)
                if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                    if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                        # Converter para dicts no formato esperado pelo matcher (lista de usinas disponíveis)
                        for _, row in ct_df[['codigo_usina', 'nome_usina']].drop_duplicates().iterrows():
                            codigo = int(row['codigo_usina'])
                            nome_original = str(row['nome_usina']).strip()
                            if nome_original and nome_original.lower() != 'nan':
                                available_plants.append(
                                    {
                                        "codigo_usina": codigo,
                                        "nome_usina": nome_original,
                                    }
                                )
                        checked_decks += 1
            except Exception as e:
                safe_print(f"[CVU MULTI-DECK] ⚠️ Erro ao coletar usinas do deck {deck_name}: {e}")
                continue
        
        if not available_plants:
            # Fallback idêntico: tentar pelo primeiro deck disponível
            first_deck_path = list(self.deck_paths.values())[0]
            safe_print(f"[CVU MULTI-DECK] Tentando identificar usina da query (fallback CT): '{query}'")
            try:
                from backend.decomp.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(first_deck_path)
                if dadger:
                    ct_df = dadger.ct(estagio=1, df=True)
                    if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                        if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                            for _, row in ct_df[['codigo_usina', 'nome_usina']].drop_duplicates().iterrows():
                                codigo = int(row['codigo_usina'])
                                nome_original = str(row['nome_usina']).strip()
                                if nome_original and nome_original.lower() != 'nan':
                                    available_plants.append(
                                        {
                                            "codigo_usina": codigo,
                                            "nome_usina": nome_original,
                                        }
                                    )
            except Exception as e:
                safe_print(f"[CVU MULTI-DECK] ⚠️ Erro no fallback CT: {e}")
        
        # Quando NÃO há código forçado, precisamos de available_plants para o matcher
        if not available_plants and forced_plant_code is None:
            safe_print(f"[CVU MULTI-DECK] ❌ Nenhuma usina encontrada nos decks (pipeline CT)")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'CVU de Cubatao' ou 'CVU da usina 97')",
                "decks": [],
                "tool_name": "CTUsinasTermelétricasTool"
            }
        
        # Definir código da usina: ou vindo do follow-up (forced_plant_code) ou via matcher
        if forced_plant_code is not None:
            codigo_usina = int(forced_plant_code)
            safe_print(f"[CVU MULTI-DECK] ⚙️ Código de usina forçado via follow-up: {codigo_usina}")
        else:
            matcher = get_decomp_thermal_plant_matcher()
            codigo_usina = matcher.extract_plant_from_query(
                query=query,
                available_plants=available_plants,
                entity_type="usina",
                threshold=0.5,
            )
        
        if codigo_usina is None:
            safe_print(f"[CVU MULTI-DECK] ❌ Usina não identificada na query pelo DecompThermalPlantMatcher: '{query}'")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'CVU de Cubatao' ou 'CVU da usina 97')",
                "decks": [],
                "tool_name": "CTUsinasTermelétricasTool"
            }
        
        # Descobrir o nome da usina correspondente ao código retornado (se possível)
        nome_usina = None
        for plant in available_plants:
            try:
                if int(plant.get("codigo_usina")) == int(codigo_usina):
                    nome_usina = plant.get("nome_usina")
                    break
            except (TypeError, ValueError):
                continue
        
        if nome_usina:
            safe_print(f"[CVU MULTI-DECK] ✅ Usina identificada: {nome_usina} (código {codigo_usina})")
        else:
            safe_print(f"[CVU MULTI-DECK] ⚠️ Nome da usina não encontrado para código {codigo_usina}")
        
        # OTIMIZAÇÃO 3: Executar consulta em paralelo
        safe_print(f"[CVU MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
        deck_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._execute_single_deck,
                    deck_name,
                    deck_path,
                    codigo_usina,
                    dadger_cache.get(deck_name)
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
                        data_count = len(result.get("data", []))
                        safe_print(f"[CVU MULTI-DECK] ✅ {deck_name}: {data_count} registros CVU (estágio 1)")
                    else:
                        safe_print(f"[CVU MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[CVU MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[CVU MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
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
        
        safe_print(f"[CVU MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[CVU MULTI-DECK] ========== FIM ==========")

        # Dados da usina selecionada para follow-up de correção
        selected_plant = {
            "type": "thermal",
            "codigo": codigo_usina,
            "nome": nome_usina,
            "nome_completo": nome_usina,
            "context": "decomp",
            "tool_name": "CTUsinasTermelétricasTool",
        }

        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina,
            },
            "tool_name": "CTUsinasTermelétricasTool",
            "selected_plant": selected_plant,
        }
    
    def _load_all_dadgers_parallel(self) -> Dict[str, Any]:
        """Carrega todos os dadgers em paralelo."""
        dadger_cache = {}
        
        def load_dadger(deck_name: str, deck_path: str) -> tuple[str, Any]:
            try:
                from backend.decomp.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(deck_path)
                if dadger:
                    return (deck_name, dadger)
                return (deck_name, None)
            except Exception as e:
                safe_print(f"[CVU MULTI-DECK] ⚠️ Erro ao carregar dadger para {deck_name}: {e}")
                return (deck_name, None)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_deck = {
                executor.submit(load_dadger, deck_name, deck_path): deck_name
                for deck_name, deck_path in self.deck_paths.items()
            }
            
            for future in as_completed(future_to_deck):
                deck_name = future_to_deck[future]
                try:
                    deck_name_result, dadger = future.result(timeout=60)
                    if dadger is not None:
                        dadger_cache[deck_name_result] = dadger
                except FutureTimeoutError:
                    safe_print(f"[CVU MULTI-DECK] ⏱️ Timeout ao carregar dadger para {deck_name}")
                except Exception as e:
                    safe_print(f"[CVU MULTI-DECK] ⚠️ Erro ao obter resultado de carregamento para {deck_name}: {e}")
        
        return dadger_cache
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        codigo_usina: int,
        dadger: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Executa CTUsinasTermelétricasTool em um único deck.
        IMPORTANTE: Sempre usa estágio 1 para CVU.
        """
        try:
            if dadger is None:
                from backend.decomp.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(deck_path)
                if not dadger:
                    return {
                        "success": False,
                        "error": "Arquivo dadger não encontrado"
                    }
            
            # IMPORTANTE: Criar query que força estágio 1 e CVU apenas
            # A tool CTUsinasTermelétricasTool já tem lógica para forçar estágio 1 quando detecta CVU
            tool = CTUsinasTermelétricasTool(deck_path)
            
            # Query que força CVU apenas e estágio 1
            query = f"cvu da usina {codigo_usina}"
            
            result = tool.execute(query, verbose=False)
            
            # Garantir que o resultado tenha apenas estágio 1
            if result.get("success") and result.get("data"):
                data = result.get("data", [])
                # Filtrar dados para garantir que apenas estágio 1 está presente
                filtered_data = [
                    d for d in data 
                    if d.get("estagio") == 1 or d.get("estágio") == 1 or d.get("estagio") is None
                ]
                result["data"] = filtered_data
            
            return result
        except Exception as e:
            safe_print(f"[CVU MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

"""
Tool Multi-Deck para consultar volume inicial de usinas hidrelétricas em múltiplos decks DECOMP.
Executa UHUsinasHidrelétricasTool em paralelo em todos os decks selecionados.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.uh_usinas_hidreletricas_tool import UHUsinasHidrelétricasTool
from backend.decomp.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import multiprocessing
import pandas as pd


class VolumeInicialMultiDeckTool(DECOMPTool):
    """
    Tool para consultar volume inicial de usinas hidrelétricas em múltiplos decks DECOMP.
    
    Executa UHUsinasHidrelétricasTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de volume inicial.
        
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
        # Calcular workers ótimos baseado em CPU cores
        self.max_workers = min(len(deck_paths), max(multiprocessing.cpu_count() * 2, 8))
    
    def get_name(self) -> str:
        return "VolumeInicialMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre volume inicial de usina hidrelétrica.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "volume inicial",
            "volume inicial da usina",
            "nível de partida",
            "nivel de partida",
            "vini",
            "volume inicial de",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar volume inicial (nível de partida) de uma usina hidrelétrica em múltiplos decks DECOMP.
        
        Executa UHUsinasHidrelétricasTool em paralelo em todos os decks selecionados.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de volume inicial em paralelo em todos os decks.
        
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
        
        safe_print(f"[VOLUME INICIAL MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Workers: {self.max_workers}")

        # Permitir correção de usina via follow-up (forced_plant_code)
        forced_plant_code = kwargs.get("forced_plant_code")

        # OTIMIZAÇÃO 1: Carregar dadgers em paralelo primeiro
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Carregando {len(self.deck_paths)} dadgers em paralelo...")
        dadger_cache = self._load_all_dadgers_parallel()

        safe_print(f"[VOLUME INICIAL MULTI-DECK] ✅ {len(dadger_cache)}/{len(self.deck_paths)} dadgers carregados")

        # OTIMIZAÇÃO 2: Identificar usina usando matcher hídrico centralizado
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Tentando identificar usina da query (pipeline UH): '{query}'")

        from backend.decomp.utils.hydraulic_plant_matcher import get_decomp_hydraulic_plant_matcher

        # Usar matcher hídrico centralizado também para obter nomes a partir do CSV
        matcher = get_decomp_hydraulic_plant_matcher()

        available_plants: List[Dict[str, Any]] = []
        decks_to_check = min(5, len(dadger_cache))
        checked_decks = 0

        for deck_name, dadger in dadger_cache.items():
            if checked_decks >= decks_to_check:
                break

            try:
                uh_df = dadger.uh(df=True)
                if uh_df is not None and isinstance(uh_df, pd.DataFrame) and not uh_df.empty:
                    # Em alguns decks o bloco UH não traz nome da usina,
                    # apenas o código. Para garantir robustez, usamos o
                    # CSV de de-para do matcher hídrico para obter o nome.
                    if "codigo_usina" in uh_df.columns:
                        codigos = (
                            uh_df["codigo_usina"]
                            .dropna()
                            .astype(int)
                            .unique()
                        )

                        for codigo in codigos:
                            nome_decomp = None
                            nome_completo = None

                            if codigo in matcher.code_to_names:
                                nome_decomp, nome_completo, _ = matcher.code_to_names[codigo]

                            nome = (nome_completo or nome_decomp or "").strip()
                            if not nome:
                                nome = f"Usina {int(codigo)}"

                            available_plants.append(
                                {
                                    "codigo_usina": int(codigo),
                                    "nome_usina": nome,
                                }
                            )

                        checked_decks += 1
            except Exception as e:
                safe_print(f"[VOLUME INICIAL MULTI-DECK] ⚠️ Erro ao coletar usinas UH do deck {deck_name}: {e}")
                continue

        if not available_plants:
            first_deck_path = list(self.deck_paths.values())[0]
            safe_print(f"[VOLUME INICIAL MULTI-DECK] Tentando identificar usina da query (fallback UH): '{query}'")
            try:
                from backend.decomp.utils.dadger_cache import get_cached_dadger

                dadger = get_cached_dadger(first_deck_path)
                if dadger:
                    uh_df = dadger.uh(df=True)
                    if uh_df is not None and isinstance(uh_df, pd.DataFrame) and not uh_df.empty:
                        if "codigo_usina" in uh_df.columns and "nome_usina" in uh_df.columns:
                            for _, row in uh_df[["codigo_usina", "nome_usina"]].drop_duplicates().iterrows():
                                codigo = int(row["codigo_usina"])
                                nome_original = str(row["nome_usina"]).strip()
                                if nome_original and nome_original.lower() != "nan":
                                    available_plants.append(
                                        {
                                            "codigo_usina": codigo,
                                            "nome_usina": nome_original,
                                        }
                                    )
            except Exception as e:
                safe_print(f"[VOLUME INICIAL MULTI-DECK] ⚠️ Erro no fallback UH: {e}")

        # Quando NÃO há código forçado, precisamos de available_plants para o matcher
        if not available_plants and forced_plant_code is None:
            safe_print(f"[VOLUME INICIAL MULTI-DECK] ❌ Nenhuma usina hidrelétrica encontrada nos decks (pipeline UH)")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'volume inicial de Itaipu' ou 'volume inicial da usina 97')",
                "decks": [],
                "tool_name": "UHUsinasHidrelétricasTool",
            }

        matcher = get_decomp_hydraulic_plant_matcher()
        if forced_plant_code is not None:
            codigo_usina = int(forced_plant_code)
            safe_print(
                f"[VOLUME INICIAL MULTI-DECK] ⚙️ Código de usina forçado via follow-up: {codigo_usina}"
            )
        else:
            codigo_usina = matcher.extract_plant_from_query(
                query=query,
                available_plants=available_plants,
                return_format="codigo",
                threshold=0.5,
            )

        if codigo_usina is None:
            safe_print(
                f"[VOLUME INICIAL MULTI-DECK] ❌ Usina não identificada na query pelo DecompHydraulicPlantMatcher: '{query}'"
            )
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'volume inicial de Itaipu' ou 'volume inicial da usina 97')",
                "decks": [],
                "tool_name": "UHUsinasHidrelétricasTool",
            }

        nome_usina = None
        for plant in available_plants:
            try:
                if int(plant.get("codigo_usina")) == int(codigo_usina):
                    nome_usina = plant.get("nome_usina")
                    break
            except (TypeError, ValueError):
                continue

        safe_print(
            f"[VOLUME INICIAL MULTI-DECK] ✅ Usina identificada via DecompHydraulicPlantMatcher: {nome_usina} (código {codigo_usina})"
        )

        # Executar consulta em paralelo
        safe_print(f"[VOLUME INICIAL MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
        deck_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._execute_single_deck,
                    deck_name,
                    deck_path,
                    codigo_usina,
                    dadger_cache.get(deck_name),
                ): deck_name
                for deck_name, deck_path in self.deck_paths.items()
            }
            
            for future in as_completed(futures):
                deck_name = futures[future]
                try:
                    result = future.result(timeout=30)
                    
                    # Calcular data da quinta-feira da semana
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
                        volume = result.get("volume_inicial")
                        usina_nome = result.get("usina", {}).get("nome", "N/A")
                        safe_print(f"[VOLUME INICIAL MULTI-DECK] ✅ {deck_name}: {volume}% para {usina_nome}")
                    else:
                        safe_print(f"[VOLUME INICIAL MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[VOLUME INICIAL MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[VOLUME INICIAL MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
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
        
        # Ordenar por data
        if any(r.get("date") for r in deck_results):
            deck_results.sort(key=lambda x: (
                x.get("date") or "9999-99-99",
                x["name"]
            ))
        
        # Extrair informações da usina do primeiro resultado bem-sucedido
        usina_info = {
            "codigo": codigo_usina,
            "nome": nome_usina or f"Usina {codigo_usina}",
        }

        safe_print(f"[VOLUME INICIAL MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[VOLUME INICIAL MULTI-DECK] ========== FIM ==========")
        
        # Dados da usina selecionada para follow-up de correção
        selected_plant = {
            "type": "hydraulic",
            "codigo": codigo_usina,
            "nome": usina_info.get("nome"),
            "nome_completo": usina_info.get("nome"),
            "context": "decomp",
            "tool_name": "UHUsinasHidrelétricasTool",
        }

        return {
            "success": True,
            "is_comparison": True,
            "is_multi_deck": True,
            "decks": deck_results,
            "usina": usina_info or {},
            "tool_name": "UHUsinasHidrelétricasTool",
            "selected_plant": selected_plant,
        }

    def _load_all_dadgers_parallel(self) -> Dict[str, Any]:
        """Carrega todos os dadgers em paralelo."""
        dadger_cache: Dict[str, Any] = {}

        def load_dadger(deck_name: str, deck_path: str) -> tuple[str, Any]:
            try:
                from backend.decomp.utils.dadger_cache import get_cached_dadger

                dadger = get_cached_dadger(deck_path)
                if dadger:
                    return (deck_name, dadger)
                return (deck_name, None)
            except Exception as e:
                safe_print(f"[VOLUME INICIAL MULTI-DECK] ⚠️ Erro ao carregar dadger para {deck_name}: {e}")
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
                except TimeoutError as e:
                    safe_print(f"[VOLUME INICIAL MULTI-DECK] ⏱️ Timeout ao carregar dadger para {deck_name}: {e}")
                except Exception as e:
                    safe_print(
                        f"[VOLUME INICIAL MULTI-DECK] ⚠️ Erro ao obter resultado de carregamento para {deck_name}: {e}"
                    )

        return dadger_cache

    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        codigo_usina: int,
        dadger: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Executa UHUsinasHidrelétricasTool em um único deck, usando código de usina já identificado.
        """
        try:
            if dadger is None:
                from backend.decomp.utils.dadger_cache import get_cached_dadger

                dadger = get_cached_dadger(deck_path)
                if not dadger:
                    return {
                        "success": False,
                        "error": "Arquivo dadger não encontrado",
                    }

            tool = UHUsinasHidrelétricasTool(deck_path)
            # A tool single-deck aceita query textual; aqui forçamos a usina por código para consistência
            query = f"volume inicial da usina {codigo_usina}"
            result = tool.execute(query, verbose=False)
            return result
        except Exception as e:
            safe_print(f"[VOLUME INICIAL MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

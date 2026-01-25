"""
Tool Multi-Deck para calcular inflexibilidade de usinas térmicas em múltiplos decks DECOMP.
Executa InflexibilidadeUsinaTool em paralelo em todos os decks selecionados.
OTIMIZADO para máxima performance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, List, Optional
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.tools.inflexibilidade_usina_tool import InflexibilidadeUsinaTool
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


class InflexibilidadeMultiDeckTool(DECOMPTool):
    """
    Tool para calcular inflexibilidade de usinas térmicas em múltiplos decks DECOMP.
    
    Executa InflexibilidadeUsinaTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    
    OTIMIZAÇÕES APLICADAS:
    - Carregamento paralelo de dadgers
    - Pré-processamento de arquivos dadger
    - Workers dinâmicos baseados em CPU cores
    - Redução de logs em modo paralelo
    - Otimização de filtragem de DataFrames
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de inflexibilidade.
        
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
        return "InflexibilidadeMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cálculo de inflexibilidade de usina.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "inflexibilidade",
            "inflexibilidade usina",
            "inflexibilidade da usina",
            "calcular inflexibilidade",
            "inflexibilidade total",
            "inflexibilidade de",
            "inflexibilidade cubatao",
            "inflexibilidade angra",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar disponibilidade de uma usina termelétrica em múltiplos decks DECOMP.
        
        Responde perguntas como:
        - Qual a disponibilidade da [usina]?
        - Potência disponível da [usina]
        - Capacidade disponível da térmica [nome]
        
        Executa o cálculo de disponibilidade em paralelo em todos os decks selecionados,
        usando dados do bloco CT (usinas termelétricas).
        
        Retorna resultados agregados com datas calculadas para visualização temporal.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa o cálculo de disponibilidade em paralelo em todos os decks.
        
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
        
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Query: {query[:100]}")
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Decks: {list(self.deck_paths.keys())}")
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Workers: {self.max_workers}")
        
        # OTIMIZAÇÃO 1: Carregar dadgers em paralelo primeiro
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Carregando {len(self.deck_paths)} dadgers em paralelo...")
        dadger_cache = self._load_all_dadgers_parallel()
        
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ✅ {len(dadger_cache)}/{len(self.deck_paths)} dadgers carregados")
        
        # OTIMIZAÇÃO 2: Identificar nome canônico primeiro, depois buscar código
        # ESTRATÉGIA: Usar matcher centralizado para identificar nome canônico,
        # depois buscar código correspondente em qualquer deck que tenha essa usina
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Tentando identificar usina da query: '{query}'")
        
        from backend.core.utils.usina_name_matcher import find_usina_match, normalize_usina_name
        
        # ETAPA 1: Coletar todos os nomes de usinas disponíveis em múltiplos decks
        all_available_names = set()
        nome_to_codigo_map = {}  # Mapeia nome normalizado -> (codigo, nome_original)
        
        # Verificar em até 5 decks para coletar nomes
        decks_to_check = min(5, len(dadger_cache))
        checked_decks = 0
        
        for deck_name, dadger in dadger_cache.items():
            if checked_decks >= decks_to_check:
                break
            
            try:
                ct_df = dadger.ct(estagio=1, df=True)
                if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                    if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                        for _, row in ct_df[['codigo_usina', 'nome_usina']].drop_duplicates().iterrows():
                            codigo = int(row['codigo_usina'])
                            nome_original = str(row['nome_usina']).strip()
                            if nome_original and nome_original.lower() != 'nan':
                                nome_normalized = normalize_usina_name(nome_original)
                                all_available_names.add(nome_original)
                                # Se já existe, manter o código menor (mais comum) ou o nome mais específico
                                if nome_normalized not in nome_to_codigo_map:
                                    nome_to_codigo_map[nome_normalized] = (codigo, nome_original)
                                else:
                                    # Se o nome normalizado é mais longo, é mais específico
                                    existing_codigo, existing_nome = nome_to_codigo_map[nome_normalized]
                                    if len(nome_normalized) > len(normalize_usina_name(existing_nome)):
                                        nome_to_codigo_map[nome_normalized] = (codigo, nome_original)
                        checked_decks += 1
            except Exception as e:
                safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro ao coletar nomes do deck {deck_name}: {e}")
                continue
        
        # Se não coletou nomes, tentar carregar um deck
        if not all_available_names:
            first_deck_path = list(self.deck_paths.values())[0]
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Tentando identificar usina da query (fallback): '{query}'")
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
                                    nome_normalized = normalize_usina_name(nome_original)
                                    all_available_names.add(nome_original)
                                    if nome_normalized not in nome_to_codigo_map:
                                        nome_to_codigo_map[nome_normalized] = (codigo, nome_original)
            except Exception as e:
                safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro no fallback: {e}")
        
        if not all_available_names:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ❌ Nenhuma usina encontrada nos decks")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'inflexibilidade de Cubatao' ou 'inflexibilidade da usina 97')",
                "decks": [],
                "tool_name": "InflexibilidadeUsinaTool"
            }
        
        # ETAPA 2: Usar matcher centralizado para encontrar o nome canônico
        available_names_list = list(all_available_names)
        match_result = find_usina_match(query, available_names_list, threshold=0.5)
        
        if not match_result:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ❌ Usina não identificada na query: '{query}'")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'inflexibilidade de Cubatao' ou 'inflexibilidade da usina 97')",
                "decks": [],
                "tool_name": "InflexibilidadeUsinaTool"
            }
        
        matched_name_original, score = match_result
        matched_name_normalized = normalize_usina_name(matched_name_original)
        
        # ETAPA 3: Buscar código correspondente ao nome canônico
        # Primeiro tentar no mapa de nomes normalizados
        if matched_name_normalized in nome_to_codigo_map:
            codigo_usina, nome_usina = nome_to_codigo_map[matched_name_normalized]
        else:
            # Se não encontrou no mapa, buscar em qualquer deck disponível
            codigo_usina = None
            nome_usina = matched_name_original
            
            for deck_name, dadger in dadger_cache.items():
                try:
                    ct_df = dadger.ct(estagio=1, df=True)
                    if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                        if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                            # Buscar por nome normalizado
                            for _, row in ct_df.iterrows():
                                nome_ct = str(row['nome_usina']).strip()
                                if normalize_usina_name(nome_ct) == matched_name_normalized:
                                    codigo_usina = int(row['codigo_usina'])
                                    nome_usina = nome_ct
                                    break
                    if codigo_usina:
                        break
                except Exception:
                    continue
        
        if not codigo_usina:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ❌ Código não encontrado para usina: '{matched_name_original}'")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Nome da usina identificado ('{matched_name_original}'), mas código não encontrado nos decks.",
                "decks": [],
                "tool_name": "InflexibilidadeUsinaTool"
            }
        
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ✅ Usina identificada: {nome_usina} (código {codigo_usina}) - nome canônico: '{matched_name_normalized}' (score: {score:.2f})")
        
        # OTIMIZAÇÃO 3: Executar cálculo em paralelo usando dadgers já carregados
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Executando cálculo em {len(self.deck_paths)} decks em paralelo...")
        
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
                    result = future.result(timeout=30)  # Timeout de 30s por deck
                    
                    # OTIMIZAÇÃO: Calcular data da quinta-feira apenas se necessário (evitar parse se não há "-")
                    date = None
                    if deck_name and "-" in deck_name:
                        parsed = parse_deck_name(deck_name)
                        if parsed and parsed.get("week"):
                            date = calculate_week_thursday(
                                parsed["year"],
                                parsed["month"],
                                parsed["week"]
                            )
                    
                    # Adicionar data ao resultado para que o formatter possa acessá-la
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
                        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ✅ {deck_name}: {result.get('inflexibilidade_total', 'N/A')} MW")
                    else:
                        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": str(e),
                        "date": None
                    })
        
        # Filtrar resultados bem-sucedidos
        successful_results = [r for r in deck_results if r["success"]]
        
        if len(successful_results) == 0:
            return {
                "success": False,
                "error": "Nenhum deck foi processado com sucesso",
                "decks": deck_results
            }
        
        # OTIMIZAÇÃO: Ordenar por data apenas se houver datas válidas
        if any(r.get("date") for r in deck_results):
            deck_results.sort(key=lambda x: (
                x.get("date") or "9999-99-99",
                x["name"]
            ))
        
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina
            },
            "tool_name": "InflexibilidadeUsinaTool"
        }
    
    def _load_all_dadgers_parallel(self) -> Dict[str, Any]:
        """
        Carrega todos os dadgers em paralelo.
        OTIMIZADO: Usa ThreadPoolExecutor com workers otimizados.
        
        Returns:
            Dict mapeando deck_name para objeto Dadger carregado
        """
        dadger_cache = {}
        
        def load_dadger(deck_name: str, deck_path: str) -> tuple[str, Any]:
            """Carrega um dadger e retorna (deck_name, dadger_obj) ou (deck_name, None) em caso de erro"""
            try:
                # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
                from backend.decomp.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(deck_path)
                if dadger:
                    return (deck_name, dadger)
                return (deck_name, None)
            except Exception as e:
                safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro ao carregar dadger para {deck_name}: {e}")
                return (deck_name, None)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_deck = {
                executor.submit(load_dadger, deck_name, deck_path): deck_name
                for deck_name, deck_path in self.deck_paths.items()
            }
            
            for future in as_completed(future_to_deck):
                deck_name = future_to_deck[future]
                try:
                    deck_name_result, dadger = future.result(timeout=60)  # Timeout de 60s por arquivo
                    if dadger is not None:
                        dadger_cache[deck_name_result] = dadger
                except FutureTimeoutError:
                    safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⏱️ Timeout ao carregar dadger para {deck_name}")
                except Exception as e:
                    safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro ao obter resultado de carregamento para {deck_name}: {e}")
        
        return dadger_cache
    
    def _extract_usina_from_query_optimized(self, query: str, dadger: Any) -> Optional[Dict[str, Any]]:
        """
        Extrai informações da usina da query (versão otimizada).
        OTIMIZADO: Reutiliza dadger já carregado, evita carregar CT novamente.
        
        Args:
            query: Query do usuário
            dadger: Objeto Dadger já carregado
            
        Returns:
            Dict com codigo e nome da usina, ou None se não encontrada
        """
        try:
            # Usar a mesma lógica da InflexibilidadeUsinaTool
            from backend.decomp.tools.inflexibilidade_usina_tool import InflexibilidadeUsinaTool
            # Criar tool temporária apenas para usar o método de extração
            temp_tool = InflexibilidadeUsinaTool(self.deck_path)
            codigo_usina = temp_tool._extract_usina_from_query_fast(query, dadger.ct(estagio=1, df=True))
            
            if codigo_usina is None:
                return None
            
            # OTIMIZAÇÃO: Buscar nome da usina usando filtragem direta (evita criar cópia desnecessária)
            ct_df = dadger.ct(estagio=1, df=True)
            if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                    # OTIMIZAÇÃO: Filtrar diretamente no DataFrame sem criar cópia
                    mask = ct_df['codigo_usina'] == codigo_usina
                    usina_row = ct_df[mask]
                    if not usina_row.empty:
                        nome_usina = usina_row.iloc[0]['nome_usina']
                        return {
                            "codigo": codigo_usina,
                            "nome": str(nome_usina).strip() if nome_usina else f"Usina {codigo_usina}"
                        }
            
            return {
                "codigo": codigo_usina,
                "nome": f"Usina {codigo_usina}"
            }
            
        except Exception as e:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro ao extrair usina: {e}")
            return None
    
    def _extract_usina_from_query_once(self, query: str, deck_path: str) -> Optional[Dict[str, Any]]:
        """
        Extrai informações da usina da query uma única vez (otimização).
        Reutiliza a lógica da DisponibilidadeUsinaTool.
        
        Args:
            query: Query do usuário
            deck_path: Caminho de um deck (para carregar dadger)
            
        Returns:
            Dict com codigo e nome da usina, ou None se não encontrada
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from backend.decomp.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(deck_path)
            
            if not dadger:
                return None
            
            # Usar a mesma lógica da InflexibilidadeUsinaTool
            from backend.decomp.tools.inflexibilidade_usina_tool import InflexibilidadeUsinaTool
            temp_tool = InflexibilidadeUsinaTool(deck_path)
            ct_df = dadger.ct(estagio=1, df=True)
            codigo_usina = temp_tool._extract_usina_from_query_fast(query, ct_df)
            
            if codigo_usina is None:
                return None
            
            # Buscar nome da usina
            if ct_df is not None and isinstance(ct_df, pd.DataFrame) and not ct_df.empty:
                if 'codigo_usina' in ct_df.columns and 'nome_usina' in ct_df.columns:
                    usina_row = ct_df[ct_df['codigo_usina'] == codigo_usina]
                    if not usina_row.empty:
                        nome_usina = usina_row.iloc[0]['nome_usina']
                        return {
                            "codigo": codigo_usina,
                            "nome": str(nome_usina).strip() if nome_usina else f"Usina {codigo_usina}"
                        }
            
            return {
                "codigo": codigo_usina,
                "nome": f"Usina {codigo_usina}"
            }
            
        except Exception as e:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] ⚠️ Erro ao extrair usina: {e}")
            return None
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        codigo_usina: int,
        dadger: Optional[Any]
    ) -> Dict[str, Any]:
        """
        Executa InflexibilidadeUsinaTool em um único deck (versão otimizada).
        
        Args:
            deck_name: Nome do deck
            deck_path: Caminho do deck
            codigo_usina: Código da usina já identificado
            dadger: Objeto Dadger já carregado (do cache)
            
        Returns:
            Resultado da InflexibilidadeUsinaTool
        """
        try:
            # Se dadger não foi fornecido (não estava no cache), carregar agora
            if dadger is None:
                # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
                from backend.decomp.utils.dadger_cache import get_cached_dadger
                dadger = get_cached_dadger(deck_path)
                if not dadger:
                    return {
                        "success": False,
                        "error": "Arquivo dadger não encontrado"
                    }
            
            # Usar método otimizado que pula leitura de arquivo e extração de usina
            tool = InflexibilidadeUsinaTool(deck_path)
            result = tool.execute_with_codigo_usina(
                codigo_usina=codigo_usina,
                dadger=dadger,
                verbose=False  # Desabilitar logs detalhados em paralelo
            )
            return result
        except Exception as e:
            safe_print(f"[INFLEXIBILIDADE MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

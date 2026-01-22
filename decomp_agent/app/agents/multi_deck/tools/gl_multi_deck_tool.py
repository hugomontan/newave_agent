"""
Tool Multi-Deck para consultar gerações GNL (Registro GL) em múltiplos decks DECOMP.
Executa GLGeracoesGNLTool em paralelo em todos os decks selecionados.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Dict, Any, Optional
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.tools.gl_geracoes_gnl_tool import GLGeracoesGNLTool
from decomp_agent.app.utils.deck_loader import (
    parse_deck_name,
    calculate_week_thursday,
    get_deck_display_name
)
from decomp_agent.app.config import safe_print
import multiprocessing
import re


class GLMultiDeckTool(DECOMPTool):
    """
    Tool para consultar gerações GNL (Registro GL) em múltiplos decks DECOMP.
    
    Executa GLGeracoesGNLTool em paralelo em todos os decks selecionados
    e retorna resultados agregados com datas calculadas (quinta-feira de cada semana).
    """
    
    def __init__(self, deck_paths: Dict[str, str]):
        """
        Inicializa a tool multi-deck de GL.
        
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
        return "GLMultiDeckTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre gerações GNL (Registro GL).
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "geracoes gnl",
            "gerações gnl",
            "geracao gnl",
            "geração gnl",
            "registro gl",
            "bloco gl",
            "gl decomp",
            "despacho antecipado",
            "despacho antecipado gnl",
            "termelétricas gnl",
            "termeletricas gnl",
            "gnl já comandadas",
            "gnl ja comandadas",
        ]
        
        # Verificar se há keywords relacionados a GL/GNL
        tem_keyword = any(kw in query_lower for kw in keywords)
        
        # Verificar se menciona "gl" junto com termos relacionados a geração/usina
        tem_gl = "gl" in query_lower
        tem_termo_geracao = any(termo in query_lower for termo in [
            "geracao", "geração", "despacho", "gnl", "usina", "termelétrica", "termeletrica"
        ])
        
        return tem_keyword or (tem_gl and tem_termo_geracao)
    
    def get_description(self) -> str:
        return """
        Tool para consultar gerações GNL já comandadas (Registro GL) em múltiplos decks DECOMP.
        
        Executa a consulta em paralelo em todos os decks selecionados,
        retornando dados de geração por patamar para usinas GNL.
        
        Retorna resultados agregados com datas calculadas (quinta-feira de cada semana)
        para visualização temporal.
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta GL em paralelo em todos os decks.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com resultados agregados de todos os decks
        """
        safe_print(f"[GL MULTI-DECK] ========== INÍCIO ==========")
        safe_print(f"[GL MULTI-DECK] Processando {len(self.deck_paths)} decks")
        
        # Extrair código da usina da query
        codigo_usina = self._extract_codigo_usina(query)
        nome_usina = None
        
        # Se não encontrou código, tentar buscar por nome
        if codigo_usina is None:
            codigo_usina = self._extract_usina_from_query(query)
        
        # Obter nome da usina usando mapeamento hardcoded
        if codigo_usina is not None:
            nome_usina = self._get_nome_usina(codigo_usina)
        
        if codigo_usina is None:
            safe_print(f"[GL MULTI-DECK] ❌ Não foi possível identificar a usina na query")
            return {
                "success": False,
                "is_comparison": True,
                "is_multi_deck": True,
                "error": f"Não foi possível identificar a usina na query '{query}'. Por favor, especifique o nome ou código da usina (ex: 'gerações GNL de Santa Cruz' ou 'GL usina 86')",
                "decks": [],
                "tool_name": "GLGeracoesGNLTool"
            }
        
        safe_print(f"[GL MULTI-DECK] ✅ Usina identificada: {nome_usina} (código {codigo_usina})")
        
        # Executar consulta em paralelo
        safe_print(f"[GL MULTI-DECK] Executando consulta em {len(self.deck_paths)} decks em paralelo...")
        
        deck_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._execute_single_deck,
                    deck_name,
                    deck_path,
                    codigo_usina
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
                        total_registros = result.get("total_registros", 0)
                        safe_print(f"[GL MULTI-DECK] ✅ {deck_name}: {total_registros} registro(s) GL")
                    else:
                        safe_print(f"[GL MULTI-DECK] ❌ {deck_name}: {result.get('error', 'Erro desconhecido')}")
                        
                except FutureTimeoutError:
                    safe_print(f"[GL MULTI-DECK] ⏱️ Timeout ao processar {deck_name}")
                    deck_results.append({
                        "name": deck_name,
                        "display_name": self.deck_display_names.get(deck_name, deck_name),
                        "result": {},
                        "success": False,
                        "error": "Timeout ao processar deck",
                        "date": None
                    })
                except Exception as e:
                    safe_print(f"[GL MULTI-DECK] ❌ Erro ao processar {deck_name}: {e}")
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
        
        safe_print(f"[GL MULTI-DECK] ✅ {len(successful_results)}/{len(deck_results)} decks processados com sucesso")
        safe_print(f"[GL MULTI-DECK] ========== FIM ==========")
        
        return {
            "success": True,
            "is_comparison": True,
            "decks": deck_results,
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina
            },
            "tool_name": "GLGeracoesGNLTool"
        }
    
    def _execute_single_deck(
        self,
        deck_name: str,
        deck_path: str,
        codigo_usina: int
    ) -> Dict[str, Any]:
        """Executa GLGeracoesGNLTool em um único deck."""
        try:
            tool = GLGeracoesGNLTool(deck_path)
            # Criar query específica para a usina
            query = f"geracoes gnl usina {codigo_usina}"
            result = tool.execute(query, verbose=False)
            return result
        except Exception as e:
            safe_print(f"[GL MULTI-DECK] Erro ao executar tool em {deck_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_codigo_usina(self, query: str) -> Optional[int]:
        """Extrai código da usina da query."""
        patterns = [
            r'usina\s*(\d+)',
            r'ute\s*(\d+)',
            r'gl\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_usina_from_query(self, query: str) -> Optional[int]:
        """
        Extrai código da usina da query usando nomes conhecidos.
        """
        query_lower = query.lower()
        
        # Mapeamento de nomes conhecidos para códigos
        usinas_conhecidas = {
            "santa cruz": 86,
            "luiz ormelo": 15,
            "luizormelo": 15,
            "psergipe": 224,
            "psergipe i": 224,
        }
        
        for nome, codigo in usinas_conhecidas.items():
            if nome in query_lower:
                safe_print(f"[GL MULTI-DECK] ✅ Usina encontrada por nome: {nome} -> {codigo}")
                return codigo
        
        return None
    
    def _get_nome_usina(self, codigo_usina: int) -> Optional[str]:
        """
        Busca o nome da usina usando mapeamento hardcoded.
        As usinas GL não estão cadastradas no bloco CT, então usamos mapeamento fixo.
        
        Args:
            codigo_usina: Código da usina
            
        Returns:
            Nome da usina ou None se não encontrado
        """
        # Mapeamento hardcoded das usinas GL (não estão no bloco CT)
        mapeamento_gl = {
            86: "SANTA CRUZ",
            224: "PSERGIPE I",
        }
        
        nome_usina = mapeamento_gl.get(codigo_usina)
        if nome_usina:
            safe_print(f"[GL MULTI-DECK] ✅ Nome encontrado para usina {codigo_usina} (hardcoded): '{nome_usina}'")
            return nome_usina
        
        safe_print(f"[GL MULTI-DECK] ⚠️ Usina {codigo_usina} não encontrada no mapeamento GL")
        return None

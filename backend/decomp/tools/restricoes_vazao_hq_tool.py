"""
Tool para consultar restrições de vazão (macro HQ/LQ/CQ) associadas a uma UHE.

Fluxo:
- Resolve nome da UHE -> codigo_usina via bloco UH (hidrelétricas)
- Usa bloco CQ para descobrir quais códigos de restrição (HQ) usam essa usina
- Lê HQ/LQ como DataFrame e devolve limites por estágio/patamar
- Opcional: integra durações de patamares via DP para cálculo de vazão média ponderada
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import os
import sys
from pathlib import Path

import pandas as pd
from idecomp.decomp import Dadger

from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import safe_print

# Cache global para mapeamento código -> nome das usinas hidrelétricas (igual UHUsinasHidrelétricasTool)
_HIDR_MAPPING_CACHE: Optional[Dict[int, str]] = None
_HIDR_CACHE_DECK_PATH: Optional[str] = None


class RestricoesVazaoHQTool(DECOMPTool):
    """
    Consulta restrições de vazão (HQ/LQ/CQ) do DECOMP associadas a uma UHE.

    Exemplos de queries:
    - "Restrição de vazão de Serra da Mesa"
    - "Quais HQ envolvem a usina 45?"
    - "Vazão mínima das usinas de Itaipu"
    """

    def get_name(self) -> str:
        return "RestricoesVazaoHQTool"

    def can_handle(self, query: str) -> bool:
        """
        Detecta queries sobre restrições de vazão/hidráulicas/HQ.
        """
        q = query.lower()

        # Se a query fala explicitamente em "conjunta"/"somatório", deixar
        # essa responsabilidade para a RestricoesVazaoHQConjuntaTool.
        if "conjunta" in q or "somatorio" in q or "somatório" in q:
            return False
        keywords = [
            "restricao de vazao",
            "restrição de vazão",
            "restricao vazao",
            "restrição vazão",
            "bloco hq",
            "registro hq",
            "restricao hidraulica",
            "restrição hidráulica",
            "vazao minima",
            "vazão mínima",
            "vazao mínima",
            "vazao minima",
            "vazao de",
            "vazão de",
        ]
        if not any(k in q for k in keywords):
            return False

        # Se tem keyword de restrição de vazão, aceitar se:
        # 1. Mencionar "usina" ou "uhe" explicitamente
        # 2. Tiver padrão "restricao de vazao de [nome]" ou "restricao de vazao da [nome]"
        # 3. Tiver "vazao de [nome]" ou "vazão de [nome]"
        
        if "usina" in q or "uhe" in q:
            return True
        
        # Verificar padrões como "restricao de vazao de X" ou "restricao de vazao da X"
        import re
        patterns = [
            r"restri[çc][aã]o\s+de\s+vaz[aã]o\s+(?:de|da|do)\s+\w+",
            r"vaz[aã]o\s+(?:de|da|do)\s+\w+",
            r"restri[çc][aã]o\s+vaz[aã]o\s+\w+",
        ]
        for pattern in patterns:
            if re.search(pattern, q):
                return True

        # Fallback: aceitar se tiver alguma palavra típica de UHE conhecida
        candidatos_usina = ["serra", "furnas", "itaipu", "cavao", "cavalho", "corumba", "piraju"]
        return any(c in q for c in candidatos_usina)

    def get_description(self) -> str:
        return """
        Consulta restrições de vazão (bloco HQ/LQ/CQ) associadas a uma usina hidrelétrica no DECOMP.
        
        Esta tool permite consultar limites de vazão mínima e máxima por patamar para uma UHE específica.
        Resolve o nome da usina, encontra as restrições HQ associadas via bloco CQ, e retorna os limites
        de vazão (limites inferiores e superiores) por estágio e patamar do bloco LQ.
        
        Palavras-chave relacionadas:
        - restrição de vazão, restrição vazão, restrições de vazão
        - restrição hidráulica, restrição hídrica
        - vazão mínima, vazão máxima, limites de vazão
        - bloco HQ, bloco LQ, bloco CQ, registro HQ, registro LQ
        - HQ/LQ/CQ, limites HQ, limites LQ
        - vazão de usina, vazão da UHE, vazão hidrelétrica
        
        Fluxo técnico:
        - Resolve nome da UHE -> código da usina via bloco UH (hidrelétricas)
        - Usa bloco CQ para descobrir quais códigos de restrição HQ usam essa usina
        - Lê HQ/LQ como DataFrame e devolve limites por estágio/patamar
        - Opcionalmente calcula vazão média ponderada usando durações do bloco DP

        Exemplos de queries:
        - "Restrição de vazão da usina Serra da Mesa"
        - "Qual a restrição de vazão da Itaipu?"
        - "Mostrar limites de vazão da UHE 45"
        - "Vazão mínima da usina Furnas"
        - "Quais restrições HQ envolvem Sobradinho?"
        - "Restrição hidráulica da usina Tucuruí"
        """

    def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        safe_print(f"[HQ] Query: {query}")
        safe_print(f"[HQ] Deck: {self.deck_path}")

        try:
            # 1) Carregar Dadger via cache
            dadger = self._get_dadger()
            if dadger is None:
                return self._error("Arquivo dadger não encontrado (nenhum dadger.rv* / dadger.rvx).")

            # 2) Resolver usina principal (codigo_usina, nome_usina)
            codigo_usina, nome_usina = self._resolver_codigo_usina(query, dadger)
            if codigo_usina is None:
                return {
                    "success": False,
                    "error": "Não consegui identificar a UHE na pergunta.",
                    "tool": self.get_name(),
                }

            safe_print(f"[HQ] UHE resolvida: codigo={codigo_usina}, nome='{nome_usina}'")

            # 3) Detectar TODAS as usinas mencionadas na query
            usinas_mencionadas = self._listar_usinas_na_query(query, dadger)

            # Garantir que, pelo menos, a usina principal esteja presente
            if not usinas_mencionadas:
                usinas_mencionadas = [(codigo_usina, nome_usina)]
            else:
                codigos_mencionados = {c for c, _ in usinas_mencionadas}
                if codigo_usina not in codigos_mencionados:
                    usinas_mencionadas.insert(0, (codigo_usina, nome_usina))

            safe_print(
                f"[HQ] Usinas mencionadas na query: "
                f"{[(c, n) for c, n in usinas_mencionadas]}"
            )

            # 4) Buscar restrições HQ:
            #    - se apenas 1 usina: considerar apenas HQ "puras" dessa usina
            #      (somente_usina_exata=True), ou seja, ignorar HQ multi-usina
            #    - se 2+ usinas: interseção de HQ entre TODAS as usinas, ou seja,
            #      somente as HQ que são, de fato, conjuntas
            if len(usinas_mencionadas) == 1:
                restricoes = self._buscar_restricoes_vazao_por_usina(
                    codigo_usina,
                    nome_usina,
                    dadger,
                    somente_usina_exata=True,
                )
            else:
                # Usina de referência (primeira da lista) para montar os registros
                cod_ref, nome_ref = usinas_mencionadas[0]
                safe_print(f"[HQ] Modo multi-usina. Usina de referência: {cod_ref} '{nome_ref}'")

                restricoes_ref = self._buscar_restricoes_vazao_por_usina(
                    cod_ref,
                    nome_ref,
                    dadger,
                    somente_usina_exata=False,
                )

                if not restricoes_ref:
                    restricoes = []
                else:
                    codigos_comuns = {
                        r.get("codigo_restricao")
                        for r in restricoes_ref
                        if r.get("codigo_restricao") is not None
                    }

                    for cod_u, nome_u in usinas_mencionadas[1:]:
                        restricoes_u = self._buscar_restricoes_vazao_por_usina(
                            cod_u,
                            nome_u,
                            dadger,
                            somente_usina_exata=False,
                        )
                        codigos_u = {
                            r.get("codigo_restricao")
                            for r in restricoes_u
                            if r.get("codigo_restricao") is not None
                        }
                        safe_print(
                            f"[HQ] Códigos HQ da usina {cod_u} ('{nome_u}'): "
                            f"{sorted(codigos_u)}"
                        )
                        codigos_comuns &= codigos_u

                    safe_print(f"[HQ] Códigos HQ em comum entre as usinas: {sorted(codigos_comuns)}")

                    if not codigos_comuns:
                        restricoes = []
                    else:
                        restricoes = [
                            r
                            for r in restricoes_ref
                            if r.get("codigo_restricao") in codigos_comuns
                        ]

                # Atualizar usina principal para a de referência (para título/metadata)
                codigo_usina, nome_usina = cod_ref, nome_ref

            if not restricoes:
                # Mensagem mais específica quando múltiplas usinas foram citadas
                if len(usinas_mencionadas) > 1:
                    nomes = " e ".join(n for _, n in usinas_mencionadas)
                    return {
                        "success": False,
                        "error": (
                            f"As usinas {nomes} não possuem nenhuma restrição de vazão "
                            "HQ/LQ em comum neste deck."
                        ),
                        "tool": self.get_name(),
                    }

                return {
                    "success": False,
                    "error": (
                        f"A usina {codigo_usina} ('{nome_usina}') não participa de "
                        "nenhuma restrição de vazão (HQ) nesse deck."
                    ),
                    "codigo_usina": codigo_usina,
                    "nome_usina": nome_usina,
                    "tool": self.get_name(),
                }

            # 5) (Opcional) Integrar durações de patamar via DP para média ponderada
            duracoes = self._extrair_duracoes_patamares(dadger)
            if duracoes and all(v is not None for v in duracoes.values()):
                safe_print(f"[HQ] Durações de patamar encontradas: {duracoes}")
                for r in restricoes:
                    self._calcular_vazao_media_ponderada_inplace(r, duracoes)

            # 6) Resposta final
            codigos_encontrados = sorted(
                {r.get("codigo_restricao") for r in restricoes if r.get("codigo_restricao")}
            )
            return {
                "success": True,
                "usina": {
                    "codigo_usina": codigo_usina,
                    "nome_usina": nome_usina,
                },
                "codigos_encontrados": codigos_encontrados,
                "total_registros": len(restricoes),
                "duracoes": duracoes,
                "data": restricoes,
                "tool": self.get_name(),
            }

        except Exception as e:  # pragma: no cover
            safe_print(f"[HQ] Erro: {e}")
            import traceback

            traceback.print_exc()
            return self._error(str(e))

    # ------------------------------------------------------------------ #
    # Helpers principais
    # ------------------------------------------------------------------ #

    def _get_dadger(self) -> Optional[Dadger]:
        """
        Obtém objeto Dadger usando cache global (quando disponível).
        """
        try:
            from backend.decomp.utils.dadger_cache import get_cached_dadger

            return get_cached_dadger(self.deck_path)
        except ImportError:
            # Fallback: tentar leitura direta
            import os

            for ext in range(10):
                candidate = os.path.join(self.deck_path, f"dadger.rv{ext}")
                if os.path.exists(candidate):
                    return Dadger.read(candidate)
            candidate = os.path.join(self.deck_path, "dadger.rvx")
            if os.path.exists(candidate):
                return Dadger.read(candidate)
            return None

    # 1) Resolver nome de UHE -> codigo_usina via UH
    # Usa EXATAMENTE o mesmo mecanismo da UHUsinasHidrelétricasTool

    def _resolver_codigo_usina(
        self, query: str, dadger: Any
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Resolve nome/código de UHE usando EXATAMENTE o mesmo mecanismo da UHUsinasHidrelétricasTool.
        
        Fluxo:
        1. Carrega UH como DataFrame e converte para dict
        2. Cria mapeamento código->nome usando HIDR.DAT (via _create_codigo_nome_mapping)
        3. Usa _extract_usina_from_query para encontrar código
        4. Retorna código e nome correspondente
        """
        # Obter TODOS os dados das usinas para buscar por nome (igual UHUsinasHidrelétricasTool)
        uh_data = dadger.uh(df=True)
        
        if uh_data is None or (isinstance(uh_data, pd.DataFrame) and uh_data.empty):
            safe_print("[HQ] Nenhuma usina encontrada no bloco UH")
            return None, None
        
        # Converter para formato padronizado (igual UHUsinasHidrelétricasTool)
        if isinstance(uh_data, pd.DataFrame):
            data = uh_data.to_dict('records')
        elif isinstance(uh_data, list):
            data = [self._uh_to_dict(u) for u in uh_data]
        else:
            data = [self._uh_to_dict(uh_data)]
        
        # Criar mapeamento código -> nome das usinas (usando HIDR.DAT do NEWAVE)
        # Reaproveita método da UHUsinasHidrelétricasTool
        mapeamento_codigo_nome = self._create_codigo_nome_mapping(dadger, data)
        
        # Extrair código da usina da query (código numérico ou nome) - EXATAMENTE como UHUsinasHidrelétricasTool
        codigo_usina = self._extract_codigo_usina(query)
        
        # Se não encontrou código numérico, tentar buscar por nome
        if codigo_usina is None:
            safe_print(f"[HQ] Tentando extrair usina da query (código ou nome)...")
            codigo_usina = self._extract_usina_from_query(query, dadger, data, mapeamento_codigo_nome)
        
        if codigo_usina is None:
            return None, None
        
        # Obter nome correspondente
        nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
        
        safe_print(f"[HQ] UHE identificada: código {codigo_usina}, nome '{nome_usina}'")
        return codigo_usina, nome_usina
    
    def _uh_to_dict(self, uh_obj) -> Dict[str, Any]:
        """Converte objeto UH para dict (igual UHUsinasHidrelétricasTool)."""
        if isinstance(uh_obj, dict):
            return uh_obj
        if hasattr(uh_obj, '__dict__'):
            return uh_obj.__dict__
        
        # Extrair atributos conhecidos do registro UH
        result = {}
        result["codigo_usina"] = (
            getattr(uh_obj, 'codigo_usina', None) or
            getattr(uh_obj, 'uhe', None)
        )
        result["codigo_ree"] = (
            getattr(uh_obj, 'codigo_ree', None) or
            getattr(uh_obj, 'ree', None)
        )
        result["volume_inicial"] = (
            getattr(uh_obj, 'volume_inicial', None) or
            getattr(uh_obj, 'vini', None)
        )
        result["evaporacao"] = getattr(uh_obj, 'evaporacao', None)
        return result
    
    def _create_codigo_nome_mapping(self, dadger: Any, data_usinas: list) -> Dict[int, str]:
        """
        Cria mapeamento código -> nome das usinas usando hidr.dat.
        
        Prioridade:
        1. Usar hidr.dat do próprio deck DECOMP
        2. Buscar em data/newave/decks se não encontrar
        """
        global _HIDR_MAPPING_CACHE, _HIDR_CACHE_DECK_PATH
        
        codigos_usinas = {d.get('codigo_usina') for d in data_usinas if d.get('codigo_usina') is not None}
        
        # ETAPA 1: Verificar cache global
        if _HIDR_MAPPING_CACHE is not None:
            mapeamento = {
                codigo: _HIDR_MAPPING_CACHE.get(codigo, f"Usina {codigo}")
                for codigo in codigos_usinas
            }
            safe_print(f"[HQ] ✅ Usando cache de mapeamento ({len(_HIDR_MAPPING_CACHE)} usinas no cache)")
            return mapeamento
        
        safe_print(f"[HQ] Criando mapeamento para {len(codigos_usinas)} usinas (cache vazio)")
        
        # ETAPA 2: Buscar hidr.dat - primeiro no próprio deck DECOMP, depois no NEWAVE
        mapeamento = {}
        hidr_paths_to_try = []
        
        # 2.1: Tentar hidr.dat do próprio deck DECOMP (preferencial)
        if self.deck_path:
            hidr_paths_to_try.extend([
                os.path.join(self.deck_path, "hidr.dat"),
                os.path.join(self.deck_path, "HIDR.DAT"),
            ])
        
        # 2.2: Construir caminhos para data/newave/decks
        from backend.core.config import DATA_DIR
        newave_decks_dir = DATA_DIR / "newave" / "decks"
        
        if newave_decks_dir.exists():
            try:
                deck_dirs = [d for d in os.listdir(newave_decks_dir) 
                            if os.path.isdir(os.path.join(newave_decks_dir, d))]
                deck_dirs.sort(reverse=True)
                
                for deck_dir in deck_dirs[:3]:
                    deck_full_path = newave_decks_dir / deck_dir
                    hidr_paths_to_try.extend([
                        str(deck_full_path / "HIDR.DAT"),
                        str(deck_full_path / "hidr.dat"),
                    ])
            except Exception as e:
                safe_print(f"[HQ] [AVISO] Erro ao listar decks NEWAVE: {e}")
        
        # 2.3: Tentar cada caminho até encontrar um válido
        for hidr_path in hidr_paths_to_try:
            if not os.path.exists(hidr_path):
                continue
            
            try:
                from inewave.newave import Hidr
                safe_print(f"[HQ] [OK] Lendo hidr.dat: {hidr_path}")
                hidr = Hidr.read(hidr_path)
                
                if hidr.cadastro is not None and not hidr.cadastro.empty:
                    cache_completo = {}
                    for idx, hidr_row in hidr.cadastro.iterrows():
                        codigo_hidr = None
                        nome_hidr = None
                        
                        try:
                            if isinstance(idx, (int, float)) and idx > 0:
                                codigo_hidr = int(idx)
                        except (ValueError, TypeError):
                            pass
                        
                        if codigo_hidr is None:
                            for cod_col in ['codigo_usina', 'codigo', 'codigo_usina_hidr', 'numero_usina', 'numero']:
                                if cod_col in hidr_row.index:
                                    try:
                                        val = hidr_row[cod_col]
                                        if pd.notna(val):
                                            codigo_hidr = int(val)
                                            break
                                    except (ValueError, TypeError):
                                        continue
                        
                        for nome_col in ['nome_usina', 'nome', 'nome_da_usina', 'usina', 'nome_do_posto']:
                            if nome_col in hidr_row.index:
                                val = hidr_row[nome_col]
                                if pd.notna(val):
                                    nome_hidr = str(val).strip()
                                    if nome_hidr and nome_hidr != 'nan' and nome_hidr != '' and nome_hidr.lower() != 'none':
                                        break
                        
                        if codigo_hidr and codigo_hidr > 0 and nome_hidr:
                            cache_completo[codigo_hidr] = nome_hidr
                    
                    if len(cache_completo) == 0:
                        # Fallback: usar índice
                        for idx in hidr.cadastro.index:
                            try:
                                codigo_hidr = int(idx) if isinstance(idx, (int, float)) else None
                                if codigo_hidr and codigo_hidr > 0:
                                    row = hidr.cadastro.loc[idx]
                                    for col in hidr.cadastro.columns:
                                        val = row[col]
                                        if pd.notna(val) and isinstance(val, str) and len(val.strip()) > 2:
                                            nome_hidr = val.strip()
                                            if nome_hidr.lower() not in ['nan', 'none', '']:
                                                cache_completo[codigo_hidr] = nome_hidr
                                                break
                            except Exception:
                                continue
                    
                    if len(cache_completo) > 0:
                        _HIDR_MAPPING_CACHE = cache_completo
                        _HIDR_CACHE_DECK_PATH = hidr_path
                        
                        mapeamento = {
                            codigo: cache_completo.get(codigo, f"Usina {codigo}")
                            for codigo in codigos_usinas
                        }
                        
                        safe_print(f"[HQ] ✅ Cache criado com {len(cache_completo)} usinas de {hidr_path}")
                        break
                        
            except Exception as e:
                safe_print(f"[HQ] [AVISO] Erro ao ler hidr.dat {hidr_path}: {e}")
                continue
        
        # Preencher códigos sem nome com formato genérico
        for codigo in codigos_usinas:
            if codigo not in mapeamento:
                mapeamento[codigo] = f"Usina {codigo}"
        
        safe_print(f"[HQ] Mapeamento completo: {len(mapeamento)} usinas")
        return mapeamento
    
    def _extract_codigo_usina(self, query: str) -> Optional[int]:
        """Extrai código da usina da query (igual UHUsinasHidrelétricasTool)."""
        patterns = [
            r'usina\s*(\d+)',
            r'uh\s*(\d+)',
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
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        dadger: Any, 
        data_usinas: list,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> Optional[int]:
        """
        Extrai código da usina da query usando matching inteligente.
        CÓDIGO IDÊNTICO ao da UHUsinasHidrelétricasTool.
        """
        query_lower = query.lower().strip()
        
        # ETAPA 1: Tentar extrair número explícito (código da usina)
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*hidrelétrica\s*(\d+)',
            r'usina\s*hidreletrica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'uh\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if any(d.get('codigo_usina') == codigo for d in data_usinas):
                        safe_print(f"[HQ] [OK] Codigo {codigo} encontrado por padrao numerico")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina usando mapeamento (HIDR.DAT)
        if not mapeamento_codigo_nome:
            safe_print(f"[HQ] [AVISO] Mapeamento vazio, tentando busca por palavras-chave conhecidas...")
            mapeamento_conhecido = {
                "furnas": [1, 6],
                "tucurui": [2, 20],
                "itaipu": [3, 30],
                "sobradinho": [4, 40],
                "paulo afonso": [5, 50],
                "xingo": [6, 60],
                "serra da mesa": [7],
                "emborcacao": [8],
                "nova ponte": [9, 25],
                "tres marias": [156],
                "camargos": [1],
                "itutinga": [2],
                "funil grande": [4],
                "capim branco": [27, 28],
                "baixo iguacu": [45],
            }
            
            palavras_query = query_lower.split()
            palavras_significativas = [p for p in palavras_query if len(p) > 3]
            
            for palavra in palavras_significativas:
                for nome_usina, codigos_possiveis in mapeamento_conhecido.items():
                    if palavra in nome_usina or nome_usina in palavra:
                        for codigo in codigos_possiveis:
                            if any(d.get('codigo_usina') == codigo for d in data_usinas):
                                safe_print(f"[HQ] [OK] Codigo {codigo} encontrado por palavra-chave '{palavra}' -> '{nome_usina}'")
                                return codigo
            
            safe_print(f"[HQ] [AVISO] Nenhuma usina encontrada por palavras-chave conhecidas")
            return None
        
        # Filtrar apenas usinas com nomes reais (não "Usina X")
        usinas_com_nome = [
            {'codigo': codigo, 'nome': nome}
            for codigo, nome in mapeamento_codigo_nome.items()
            if nome and nome != f"Usina {codigo}" and not nome.startswith("Usina ")
        ]
        
        # Ordenar por tamanho do nome (maior primeiro)
        usinas_sorted = sorted(usinas_com_nome, key=lambda x: len(x['nome']), reverse=True)
        
        safe_print(f"[HQ] Buscando por nome entre {len(usinas_sorted)} usinas com nomes reais")
        
        # ETAPA 2.1: Match exato do nome completo (prioridade máxima)
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Match exato do nome completo
            if nome_usina_lower == query_lower:
                safe_print(f"[HQ] [OK] Codigo {codigo_usina} encontrado por match exato '{nome_usina}'")
                return codigo_usina
            
            # Match exato do nome completo dentro da query (como palavra completa)
            if len(nome_usina_lower) >= 4:
                pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                if re.search(pattern, query_lower):
                    safe_print(f"[HQ] [OK] Codigo {codigo_usina} encontrado por nome completo '{nome_usina}' na query")
                    return codigo_usina
        
        # ETAPA 2.2: Buscar por palavras-chave do nome
        palavras_ignorar = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 
            'em', 'na', 'no', 'nas', 'nos', 'usina', 'usinas', 'uh', 
            'decomp', 'bloco', 'registro', 'hidrelétrica', 'hidreletrica',
            'restricao', 'restrição', 'vazao', 'vazão'
        }
        palavras_query = [p for p in query_lower.split() if len(p) > 3 and p not in palavras_ignorar]
        
        if palavras_query:
            palavras_candidatas = []
            for usina in usinas_sorted:
                codigo_usina = usina['codigo']
                nome_usina = usina['nome']
                nome_usina_lower = nome_usina.lower().strip()
                
                if not nome_usina_lower:
                    continue
                
                palavras_nome = nome_usina_lower.split()
                palavras_nome_sorted = sorted(palavras_nome, key=len, reverse=True)
                
                for palavra in palavras_nome_sorted:
                    if len(palavra) > 3:
                        pattern = r'\b' + re.escape(palavra) + r'\b'
                        if re.search(pattern, query_lower):
                            palavras_candidatas.append({
                                'codigo': codigo_usina,
                                'nome': nome_usina,
                                'palavra': palavra,
                                'tamanho': len(palavra),
                                'tamanho_nome': len(nome_usina_lower)
                            })
            
            if palavras_candidatas:
                melhor_match = max(palavras_candidatas, key=lambda x: (x['tamanho'], x['tamanho_nome']))
                safe_print(f"[HQ] [OK] Codigo {melhor_match['codigo']} encontrado por palavra-chave '{melhor_match['palavra']}' do nome '{melhor_match['nome']}'")
                return melhor_match['codigo']
        
        safe_print(f"[HQ] [AVISO] Nenhuma usina especifica detectada na query")
        return None

    def _listar_usinas_na_query(
        self, query: str, dadger: Any
    ) -> List[Tuple[int, str]]:
        """
        Retorna uma lista [(codigo_usina, nome_usina)] de todas as usinas
        cujo nome aparece textualmente na query.

        Usa o mesmo mapeamento HIDR.DAT que as demais tools (UHUsinasHidrelétricasTool).
        """
        query_lower = query.lower()

        # Carregar UH para ter a lista de códigos presentes no deck
        try:
            uh_data = dadger.uh(df=True)
        except Exception:
            uh_data = None

        if uh_data is None or (isinstance(uh_data, pd.DataFrame) and uh_data.empty):
            return []

        if isinstance(uh_data, pd.DataFrame):
            data_usinas = uh_data.to_dict("records")
        elif isinstance(uh_data, list):
            data_usinas = [self._uh_to_dict(u) for u in uh_data]
        else:
            data_usinas = [self._uh_to_dict(uh_data)]

        # Mapeamento código -> nome a partir do HIDR.DAT
        mapeamento = self._create_codigo_nome_mapping(dadger, data_usinas)

        candidatos: List[Tuple[int, int, str]] = []
        for codigo, nome in mapeamento.items():
            if not nome:
                continue
            nome_lower = str(nome).lower().strip()
            if len(nome_lower) < 3:
                continue
            pos = query_lower.find(nome_lower)
            if pos != -1:
                candidatos.append((pos, int(codigo), str(nome)))

        # Ordenar pela posição do nome na query
        candidatos.sort(key=lambda x: x[0])

        # Remover posição e evitar códigos duplicados
        vistos = set()
        resultado: List[Tuple[int, str]] = []
        for _, cod, nome in candidatos:
            if cod not in vistos:
                vistos.add(cod)
                resultado.append((cod, nome))

        return resultado

    # 2) Mapear codigo_usina -> codigos HQ via CQ e ler HQ/LQ

    def _buscar_restricoes_vazao_por_usina(
        self,
        codigo_usina: int,
        nome_usina: Optional[str],
        dadger: Any,
        somente_usina_exata: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        A partir de codigo_usina, encontra restrições HQ via CQ e monta registros
        combinando HQ/LQ, considerando que uma mesma restrição HQ pode envolver
        múltiplas usinas (multi-usina) via bloco CQ.
        """
        # CQ df
        cq_df = dadger.cq(df=True)
        if cq_df is None or not isinstance(cq_df, pd.DataFrame) or cq_df.empty:
            safe_print("[HQ] Nenhum registro CQ encontrado.")
            return []

        # Detectar colunas
        col_cod_usina = None
        col_cod_restricao = None
        for c in cq_df.columns:
            cl = c.lower()
            if col_cod_usina is None and ("codigo_usina" in cl or cl == "uhe"):
                col_cod_usina = c
            if col_cod_restricao is None and ("codigo_restricao" in cl or "cod_restricao" in cl):
                col_cod_restricao = c

        if col_cod_usina is None or col_cod_restricao is None:
            safe_print(f"[HQ] Colunas CQ não identificadas. Colunas: {list(cq_df.columns)}")
            return []

        # Todas as linhas CQ em que a usina consultada participa
        cq_usina = cq_df[cq_df[col_cod_usina] == codigo_usina]
        if cq_usina.empty:
            safe_print(f"[HQ] Nenhuma linha CQ encontrada para codigo_usina={codigo_usina}.")
            return []

        # Criar mapeamento código->nome das usinas para poder montar,
        # para cada código HQ, a lista de TODAS as usinas envolvidas.
        try:
            uh_data = dadger.uh(df=True)
        except Exception:
            uh_data = None

        data_usinas: List[Dict[str, Any]] = []
        if isinstance(uh_data, pd.DataFrame):
            data_usinas = uh_data.to_dict("records")
        elif isinstance(uh_data, list):
            data_usinas = [self._uh_to_dict(u) for u in uh_data]
        elif uh_data is not None:
            data_usinas = [self._uh_to_dict(uh_data)]

        try:
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(dadger, data_usinas)
        except Exception:
            # Se algo der errado, seguimos apenas com os códigos numéricos
            mapeamento_codigo_nome = {}

        codigos = sorted(
            {int(v) for v in cq_usina[col_cod_restricao].dropna().unique().tolist()}
        )
        safe_print(f"[HQ] Códigos de restrição HQ associados à usina {codigo_usina}: {codigos}")

        if not codigos:
            return []

        # HQ/LQ df (uma vez só)
        hq_df = dadger.hq(df=True)
        lq_df = dadger.lq(df=True)

        if hq_df is None or not isinstance(hq_df, pd.DataFrame):
            hq_df = pd.DataFrame()
        if lq_df is None or not isinstance(lq_df, pd.DataFrame):
            lq_df = pd.DataFrame()

        # Detectar colunas de código em HQ/LQ
        col_cod_hq = None
        if not hq_df.empty:
            for c in hq_df.columns:
                if "codigo_restricao" in c.lower() or "cod_restricao" in c.lower():
                    col_cod_hq = c
                    break

        col_cod_lq = None
        if not lq_df.empty:
            for c in lq_df.columns:
                if "codigo_restricao" in c.lower() or "cod_restricao" in c.lower():
                    col_cod_lq = c
                    break

        resultados: List[Dict[str, Any]] = []

        for cod in codigos:
            # Para este código de restrição HQ, descobrir TODAS as usinas
            # que participam via bloco CQ (multi-usina).
            cq_cod = cq_df[cq_df[col_cod_restricao] == cod]
            cod_usinas_env = sorted(
                {
                    int(v)
                    for v in cq_cod[col_cod_usina].dropna().unique().tolist()
                    if v is not None
                }
            )

            # Se o modo "somente_usina_exata" estiver ativo, queremos
            # ignorar restrições que envolvam OUTRAS usinas além da
            # consultada (ou seja, HQ multi-usina).
            if somente_usina_exata and len(cod_usinas_env) > 1:
                safe_print(
                    f"[HQ] Ignorando código {cod} em modo somente_usina_exata "
                    f"(usinas envolvidas: {cod_usinas_env})"
                )
                continue

            multi_usina_flag = len(cod_usinas_env) > 1

            nomes_usinas_env: List[str] = []
            for cu in cod_usinas_env:
                nome_env = mapeamento_codigo_nome.get(cu, f"Usina {cu}")
                nomes_usinas_env.append(f"{nome_env} ({cu})")

            usinas_envolvidas_str = ", ".join(nomes_usinas_env) if nomes_usinas_env else None

            # HQ cabeçalho
            hq_info: Dict[str, Any] = {}
            if col_cod_hq and not hq_df.empty:
                hq_cod = hq_df[hq_df[col_cod_hq] == cod]
                if not hq_cod.empty:
                    hq_info = hq_cod.iloc[0].to_dict()

            # LQ limites
            if not col_cod_lq or lq_df.empty:
                continue

            lq_cod = lq_df[lq_df[col_cod_lq] == cod]
            if lq_cod.empty:
                safe_print(f"[HQ] Nenhum LQ encontrado para código {cod}.")
                continue

            # Detectar coluna de estágio (se houver)
            col_estagio = None
            for c in lq_cod.columns:
                cl = c.lower()
                if cl == "estagio" or cl == "ip":
                    col_estagio = c
                    break

            for idx, row in lq_cod.iterrows():
                d = row.to_dict()
                d["codigo_restricao"] = cod
                # código da UHE CONSULTADA (que originou a query)
                d["codigo_usina"] = codigo_usina
                d["multi_usina"] = multi_usina_flag

                if col_estagio:
                    d["estagio"] = row.get(col_estagio)

                # Debug: imprimir colunas antes da normalização (apenas primeira linha)
                if idx == lq_cod.index[0]:
                    safe_print(f"[HQ] [DEBUG] Colunas do LQ antes da normalização: {list(d.keys())}")
                    # Mostrar valores de algumas colunas relevantes
                    for key in list(d.keys())[:10]:
                        safe_print(f"[HQ] [DEBUG]   {key}: {d[key]} (tipo: {type(d[key])})")

                # Normalizar campos de limites para o formatter de restrições elétricas,
                # se possível (assumindo padrão limite_inferior_1..3 / limite_superior_1..3)
                self._normalizar_limites_lq(d)
                
                # Debug: verificar se normalização funcionou (apenas primeira linha)
                if idx == lq_cod.index[0]:
                    limites_encontrados = {
                        f"limite_inferior_{i}": d.get(f"limite_inferior_{i}") 
                        for i in (1, 2, 3)
                    }
                    limites_sup_encontrados = {
                        f"limite_superior_{i}": d.get(f"limite_superior_{i}") 
                        for i in (1, 2, 3)
                    }
                    safe_print(f"[HQ] [DEBUG] Limites inferiores após normalização: {limites_encontrados}")
                    safe_print(f"[HQ] [DEBUG] Limites superiores após normalização: {limites_sup_encontrados}")

                # Anexar alguns campos do HQ (se existirem)
                for chave in ["estagio_inicial", "estagio_final", "tipo_limite"]:
                    if chave in hq_info and chave not in d:
                        d[chave] = hq_info.get(chave)

                # Adicionar nome da usina consultada e TODAS as usinas envolvidas na HQ
                if nome_usina:
                    d["nome_usina"] = nome_usina
                if usinas_envolvidas_str:
                    d["usinas_envolvidas"] = usinas_envolvidas_str

                resultados.append(d)

        return resultados

    # 3) Normalização e cálculo de média ponderada

    def _normalizar_limites_lq(self, registro: Dict[str, Any]) -> None:
        """
        Garante que existam chaves:
        - limite_inferior_1/2/3
        - limite_superior_1/2/3

        Tentando mapear a partir de variações possíveis.
        O idecomp pode retornar limites como listas ou como colunas expandidas.
        """
        # Primeiro, tentar expandir se houver colunas de lista
        if "limite_inferior" in registro and isinstance(registro["limite_inferior"], list):
            limites_inf = registro["limite_inferior"]
            for i, val in enumerate(limites_inf[:3], start=1):
                registro[f"limite_inferior_{i}"] = val
        
        if "limite_superior" in registro and isinstance(registro["limite_superior"], list):
            limites_sup = registro["limite_superior"]
            for i, val in enumerate(limites_sup[:3], start=1):
                registro[f"limite_superior_{i}"] = val
        
        # Também tentar limites_inferiores/limites_superiores (plural)
        if "limites_inferiores" in registro and isinstance(registro["limites_inferiores"], list):
            limites_inf = registro["limites_inferiores"]
            for i, val in enumerate(limites_inf[:3], start=1):
                registro[f"limite_inferior_{i}"] = val
        
        if "limites_superiores" in registro and isinstance(registro["limites_superiores"], list):
            limites_sup = registro["limites_superiores"]
            for i, val in enumerate(limites_sup[:3], start=1):
                registro[f"limite_superior_{i}"] = val
        
        # Agora tentar mapear colunas já expandidas
        for pat in (1, 2, 3):
            # Limite inferior
            key_dest_inf = f"limite_inferior_{pat}"
            if key_dest_inf not in registro or registro.get(key_dest_inf) is None:
                candidatos_inf = [
                    key_dest_inf,
                    f"limite_inferior_patamar_{pat}",
                    f"limite_inferior_p{pat}",
                    f"limites_inferiores_{pat}",
                    f"limite_inferior_pat{pat}",
                    # Tentar variações com índice baseado em 0
                    f"limite_inferior_{pat-1}" if pat > 1 else None,
                ]
                for k in candidatos_inf:
                    if k and k in registro and registro.get(k) is not None:
                        registro[key_dest_inf] = registro.get(k)
                        break

            # Limite superior
            key_dest_sup = f"limite_superior_{pat}"
            if key_dest_sup not in registro or registro.get(key_dest_sup) is None:
                candidatos_sup = [
                    key_dest_sup,
                    f"limite_superior_patamar_{pat}",
                    f"limite_superior_p{pat}",
                    f"limites_superiores_{pat}",
                    f"limite_superior_pat{pat}",
                    # Tentar variações com índice baseado em 0
                    f"limite_superior_{pat-1}" if pat > 1 else None,
                ]
                for k in candidatos_sup:
                    if k and k in registro and registro.get(k) is not None:
                        registro[key_dest_sup] = registro.get(k)
                        break
        
        # Tentar buscar por padrões mais genéricos (qualquer coluna que contenha número)
        if not any(registro.get(f"limite_inferior_{i}") is not None for i in (1, 2, 3)):
            # Procurar por colunas que possam ser limites inferiores com índices variados
            for key in registro.keys():
                key_lower = key.lower()
                # Tentar padrões como: limite_inf_1, limiteinf1, etc.
                if "limite" in key_lower and "inf" in key_lower:
                    # Tentar extrair número do nome da coluna
                    num_match = re.search(r'(\d+)', key)
                    if num_match:
                        num = int(num_match.group(1))
                        if 1 <= num <= 3:
                            registro[f"limite_inferior_{num}"] = registro[key]
        
        if not any(registro.get(f"limite_superior_{i}") is not None for i in (1, 2, 3)):
            # Procurar por colunas que possam ser limites superiores com índices variados
            for key in registro.keys():
                key_lower = key.lower()
                if "limite" in key_lower and "sup" in key_lower:
                    # Tentar extrair número do nome da coluna
                    num_match = re.search(r'(\d+)', key)
                    if num_match:
                        num = int(num_match.group(1))
                        if 1 <= num <= 3:
                            registro[f"limite_superior_{num}"] = registro[key]
        
        # Debug: se ainda não encontrou os campos, imprimir colunas disponíveis
        if not any(registro.get(f"limite_inferior_{i}") is not None for i in (1, 2, 3)):
            colunas_disponiveis = [k for k in registro.keys() if "limite" in k.lower() or "inferior" in k.lower() or "superior" in k.lower()]
            if colunas_disponiveis:
                safe_print(f"[HQ] [DEBUG] Colunas de limite encontradas: {colunas_disponiveis}")
                safe_print(f"[HQ] [DEBUG] Todas as colunas do registro: {list(registro.keys())[:30]}")

    def _extrair_duracoes_patamares(self, dadger: Any) -> Dict[str, Optional[float]]:
        """
        Extrai durações dos patamares do bloco DP (estágio 1).

        Reaproveita o padrão de outras tools: tenta duracao_patamar_1,
        duracao_1, horas_1, etc.
        """
        duracoes = {"pesada": None, "media": None, "leve": None}

        try:
            dp_data = dadger.dp(estagio=1, df=True)
        except Exception:
            dp_data = None

        if dp_data is None or not isinstance(dp_data, pd.DataFrame) or dp_data.empty:
            safe_print("[HQ] Não foi possível ler DP para extrair durações.")
            return duracoes

        primeiro = dp_data.iloc[0].to_dict()
        pat_map = {"pesada": 1, "media": 2, "leve": 3}

        for nome, idx in pat_map.items():
            col_candidatas = [
                f"duracao_patamar_{idx}",
                f"duracao_{idx}",
                f"horas_{idx}",
                f"horas_patamar_{idx}",
                f"duracao_pat{idx}",
                f"horas_pat{idx}",
            ]
            for c in col_candidatas:
                if c in primeiro and primeiro[c] is not None:
                    try:
                        duracoes[nome] = float(primeiro[c])
                        break
                    except (ValueError, TypeError):
                        continue

        return duracoes

    def _calcular_vazao_media_ponderada_inplace(
        self,
        registro: Dict[str, Any],
        duracoes: Dict[str, Optional[float]],
    ) -> None:
        """
        Calcula e grava em 'vazao_media_ponderada' se todos os dados existirem.
        Usa limite_superior como referência (podemos ajustar para inferior/superior
        se necessário).
        """
        if any(v is None for v in duracoes.values()):
            return

        try:
            val_pesada = float(registro.get("limite_superior_1") or 0)
            val_media = float(registro.get("limite_superior_2") or 0)
            val_leve = float(registro.get("limite_superior_3") or 0)
        except (TypeError, ValueError):
            return

        dur_pesada = float(duracoes.get("pesada") or 0)
        dur_media = float(duracoes.get("media") or 0)
        dur_leve = float(duracoes.get("leve") or 0)

        if dur_pesada == 0 and dur_media == 0 and dur_leve == 0:
            return

        numerador = val_leve * dur_leve + val_media * dur_media + val_pesada * dur_pesada
        denominador = dur_leve + dur_media + dur_pesada
        if denominador == 0:
            return

        registro["vazao_media_ponderada"] = round(numerador / denominador, 2)


    # ------------------------------------------------------------------ #
    # Utilitário de erro
    # ------------------------------------------------------------------ #

    def _error(self, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": message,
            "tool": self.get_name(),
        }

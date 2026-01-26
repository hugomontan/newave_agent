"""
Tool para consultar informações do Bloco UH (Usinas Hidrelétricas) do DECOMP.
Acessa dados de volume inicial, REE, evaporação e operação das usinas hidrelétricas.
"""
from backend.decomp.tools.base import DECOMPTool
from backend.decomp.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher

# ⚡ Cache global para mapeamento código -> nome das usinas hidrelétricas
# O mapeamento é global (não depende do deck específico), então pode ser compartilhado
_HIDR_MAPPING_CACHE: Optional[Dict[int, str]] = None
_HIDR_CACHE_DECK_PATH: Optional[str] = None


def clear_hidr_mapping_cache():
    """
    Limpa o cache de mapeamento HIDR.DAT.
    Útil para forçar recarregamento do mapeamento.
    """
    global _HIDR_MAPPING_CACHE, _HIDR_CACHE_DECK_PATH
    _HIDR_MAPPING_CACHE = None
    _HIDR_CACHE_DECK_PATH = None
    safe_print("[UH TOOL] 🗑️ Cache de mapeamento HIDR.DAT limpo")


def get_hidr_cache_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do cache de mapeamento HIDR.DAT.
    
    Returns:
        Dict com informações do cache
    """
    return {
        "cached": _HIDR_MAPPING_CACHE is not None,
        "cache_size": len(_HIDR_MAPPING_CACHE) if _HIDR_MAPPING_CACHE else 0,
        "cache_deck_path": _HIDR_CACHE_DECK_PATH
    }


class UHUsinasHidrelétricasTool(DECOMPTool):
    """
    Tool específica para consultar volume inicial/nível de partida de uma usina hidrelétrica.
    
    Foco único: Retornar apenas o volume inicial (VINI) de uma usina específica do Bloco UH do DECOMP.
    """
    
    def get_name(self) -> str:
        return "UHUsinasHidrelétricasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre volume inicial/nível de partida de uma usina hidrelétrica.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        # Verificar se a query menciona volume inicial ou nível de partida
        tem_volume_inicial = any(kw in query_lower for kw in [
            "volume inicial",
            "nível de partida",
            "nivel de partida",
            "vini",
            "volume inicial da",
            "volume inicial de",
            "nível de partida da",
            "nível de partida de",
        ])
        
        # Verificar se menciona usina hidrelétrica
        tem_usina = any(kw in query_lower for kw in [
            "usina",
            "uh",
            "hidrelétrica",
            "hidreletrica",
        ])
        
        return tem_volume_inicial and tem_usina
    
    def get_description(self) -> str:
        return """
        Tool específica para consultar volume inicial/nível de partida de uma usina hidrelétrica.
        
        Acessa dados do Bloco UH do DECOMP que define o volume inicial (VINI) de usinas hidrelétricas.
        Retorna apenas o volume inicial (VINI) do Bloco UH do DECOMP para uma usina específica.
        
        O volume inicial representa o nível de partida do reservatório da usina no início do período de estudo,
        expresso como percentual do volume útil do reservatório.
        
        Palavras-chave relacionadas:
        - volume inicial, volume inicial da usina, volume inicial de [nome usina]
        - nível de partida, nível de partida da usina, nível de partida de [nome usina]
        - VINI, vini da usina, vini de [nome usina]
        - qual o volume inicial, qual o volume inicial de, qual o volume inicial da
        - volume inicial qual, volume inicial de qual usina
        
        Termos-chave: volume inicial, nível de partida, VINI, volume inicial da usina, nível de partida da usina,
        volume inicial de, volume inicial qual, qual volume inicial.
        
        Exemplos de queries:
        - "Qual o volume inicial da usina 1?"
        - "Qual o volume inicial de Camargos"
        - "Volume inicial de Furnas"
        - "Volume inicial de [nome da usina]"
        - "Qual o nível de partida da usina Tucuruí?"
        - "VINI da usina 24"
        - "Volume inicial da usina hidrelétrica de Itaipu"
        - "Qual o volume inicial de [qualquer nome de usina]"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de volume inicial/nível de partida de uma usina hidrelétrica específica.
        
        Args:
            query: Query do usuário (deve mencionar volume inicial/nível de partida e uma usina)
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com volume inicial da usina encontrada
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from backend.decomp.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            safe_print(f"[UH TOOL] Query recebida: {query}")
            
            # Obter TODOS os dados das usinas para buscar por nome
            uh_data = dadger.uh(df=True)
            
            if uh_data is None or (isinstance(uh_data, pd.DataFrame) and uh_data.empty):
                return {
                    "success": False,
                    "error": "Nenhuma usina encontrada no bloco UH"
                }
            
            # Converter para formato padronizado
            if isinstance(uh_data, pd.DataFrame):
                data = uh_data.to_dict('records')
            elif isinstance(uh_data, list):
                data = [self._uh_to_dict(u) for u in uh_data]
            else:
                data = [self._uh_to_dict(uh_data)]
            
            # Criar mapeamento código -> nome das usinas (usando HIDR.DAT do NEWAVE)
            mapeamento_codigo_nome = self._create_codigo_nome_mapping(dadger, data)
            
            # Extrair código da usina da query (código numérico ou nome)
            codigo_usina = self._extract_codigo_usina(query)
            
            # Se não encontrou código numérico, tentar buscar por nome
            if codigo_usina is None:
                safe_print(f"[UH TOOL] Tentando extrair usina da query (código ou nome)...")
                codigo_usina = self._extract_usina_from_query(query, dadger, data, mapeamento_codigo_nome)
            
            if codigo_usina is None:
                return {
                    "success": False,
                    "error": "Não foi possível identificar a usina na query. Por favor, especifique o nome ou código da usina (ex: 'volume inicial da usina Furnas' ou 'volume inicial da usina 1')"
                }
            
            safe_print(f"[UH TOOL] [OK] Usina identificada: código {codigo_usina}")
            
            # Filtrar APENAS essa usina
            usina_encontrada = None
            for d in data:
                if d.get('codigo_usina') == codigo_usina:
                    usina_encontrada = d
                    break
            
            if usina_encontrada is None:
                return {
                    "success": False,
                    "error": f"Usina {codigo_usina} não encontrada no bloco UH"
                }
            
            # Extrair volume inicial (tentar múltiplas variações de nome de campo)
            volume_inicial = (
                usina_encontrada.get('volume_inicial') or 
                usina_encontrada.get('vini') or
                usina_encontrada.get('VINI') or
                usina_encontrada.get('volume_inicial_reservatorio')
            )
            
            if volume_inicial is None:
                return {
                    "success": False,
                    "error": f"Volume inicial não disponível para a usina {codigo_usina}"
                }
            
            # Obter nome da usina
            nome_usina = mapeamento_codigo_nome.get(codigo_usina, f"Usina {codigo_usina}")
            
            safe_print(f"[UH TOOL] ✅ Volume inicial encontrado: {volume_inicial}% para usina {codigo_usina} ({nome_usina})")
            
            return {
                "success": True,
                "volume_inicial": float(volume_inicial),
                "usina": {
                    "codigo": codigo_usina,
                    "nome": nome_usina,
                    "codigo_ree": usina_encontrada.get('codigo_ree'),
                },
                "unidade": "%",
                "descricao": f"Volume inicial (VINI) da usina {nome_usina}",
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[UH TOOL] ❌ Erro ao consultar volume inicial: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar volume inicial: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_codigo_usina(self, query: str) -> Optional[int]:
        """Extrai código da usina da query."""
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
    
    def _extract_codigo_ree(self, query: str) -> Optional[int]:
        """Extrai código do REE da query."""
        patterns = [
            r'ree\s*(\d+)',
            r'reservatório equivalente\s*(\d+)',
            r'reservatorio equivalente\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_volume_inicial(self, query: str) -> Optional[float]:
        """Extrai volume inicial da query."""
        patterns = [
            r'volume inicial\s*[:\-]?\s*(\d+\.?\d*)',
            r'vini\s*[:\-]?\s*(\d+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _create_codigo_nome_mapping(self, dadger: Any, data_usinas: list) -> Dict[int, str]:
        """
        ⚡ OTIMIZADO: Cria mapeamento código -> nome das usinas usando hidr.dat.
        
        Prioridade:
        1. Usar hidr.dat do próprio deck DECOMP (cada deck tem seu próprio arquivo)
        2. Buscar em data/newave/decks se não encontrar no deck DECOMP
        
        Args:
            dadger: Instância do Dadger
            data_usinas: Lista de dados das usinas já carregados
            
        Returns:
            Dict com mapeamento {codigo_usina: nome_usina}
        """
        global _HIDR_MAPPING_CACHE, _HIDR_CACHE_DECK_PATH
        
        codigos_usinas = {d.get('codigo_usina') for d in data_usinas if d.get('codigo_usina') is not None}
        
        # ⚡ ETAPA 1: Verificar cache global
        if _HIDR_MAPPING_CACHE is not None:
            # Filtrar apenas os códigos necessários do cache
            mapeamento = {
                codigo: _HIDR_MAPPING_CACHE.get(codigo, f"Usina {codigo}")
                for codigo in codigos_usinas
            }
            safe_print(f"[UH TOOL] ✅ Usando cache de mapeamento ({len(_HIDR_MAPPING_CACHE)} usinas no cache)")
            return mapeamento
        
        safe_print(f"[UH TOOL] Criando mapeamento para {len(codigos_usinas)} usinas (cache vazio)")
        
        # ⚡ ETAPA 2: Buscar hidr.dat - primeiro no próprio deck DECOMP, depois no NEWAVE
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
            # Listar decks e ordenar por nome (mais recente primeiro)
            try:
                deck_dirs = [d for d in os.listdir(newave_decks_dir) 
                            if os.path.isdir(os.path.join(newave_decks_dir, d))]
                deck_dirs.sort(reverse=True)  # Mais recente primeiro
                
                for deck_dir in deck_dirs[:3]:  # Apenas os 3 mais recentes
                    deck_full_path = newave_decks_dir / deck_dir
                    hidr_paths_to_try.extend([
                        str(deck_full_path / "HIDR.DAT"),
                        str(deck_full_path / "hidr.dat"),
                    ])
            except Exception as e:
                safe_print(f"[UH TOOL] [AVISO] Erro ao listar decks NEWAVE: {e}")
        
        # 2.3: Tentar cada caminho até encontrar um válido
        for hidr_path in hidr_paths_to_try:
            if not os.path.exists(hidr_path):
                continue
            
            try:
                from inewave.newave import Hidr
                safe_print(f"[UH TOOL] [OK] Lendo hidr.dat: {hidr_path}")
                hidr = Hidr.read(hidr_path)
                
                if hidr.cadastro is not None and not hidr.cadastro.empty:
                    safe_print(f"[UH TOOL] [DEBUG] Colunas disponíveis: {list(hidr.cadastro.columns)[:10]}...")
                    safe_print(f"[UH TOOL] [DEBUG] Total de linhas no cadastro: {len(hidr.cadastro)}")
                    
                    # Carregar TODOS os códigos do hidr.dat no cache global
                    cache_completo = {}
                    for idx, hidr_row in hidr.cadastro.iterrows():
                        codigo_hidr = None
                        nome_hidr = None
                        
                        # Tentar usar o índice como código (comum no HIDR.DAT)
                        try:
                            if isinstance(idx, (int, float)) and idx > 0:
                                codigo_hidr = int(idx)
                        except (ValueError, TypeError):
                            pass
                        
                        # Tentar diferentes nomes de coluna para código
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
                        
                        # Tentar diferentes nomes de coluna para nome
                        for nome_col in ['nome_usina', 'nome', 'nome_da_usina', 'usina', 'nome_do_posto']:
                            if nome_col in hidr_row.index:
                                val = hidr_row[nome_col]
                                if pd.notna(val):
                                    nome_hidr = str(val).strip()
                                    if nome_hidr and nome_hidr != 'nan' and nome_hidr != '' and nome_hidr.lower() != 'none':
                                        break
                        
                        if codigo_hidr and codigo_hidr > 0 and nome_hidr:
                            cache_completo[codigo_hidr] = nome_hidr
                    
                    safe_print(f"[UH TOOL] [DEBUG] Usinas extraídas do hidr.dat: {len(cache_completo)}")
                    
                    if len(cache_completo) > 0:
                        # Mostrar alguns exemplos
                        exemplos = list(cache_completo.items())[:5]
                        safe_print(f"[UH TOOL] [DEBUG] Exemplos: {exemplos}")
                        
                        # Salvar no cache global
                        _HIDR_MAPPING_CACHE = cache_completo
                        _HIDR_CACHE_DECK_PATH = hidr_path
                        
                        # Filtrar apenas os códigos necessários para retornar
                        mapeamento = {
                            codigo: cache_completo.get(codigo, f"Usina {codigo}")
                            for codigo in codigos_usinas
                        }
                        
                        safe_print(f"[UH TOOL] ✅ Cache criado com {len(cache_completo)} usinas de {hidr_path}")
                        break
                    else:
                        # Se não encontrou nenhuma usina, tentar usar o índice como código
                        safe_print(f"[UH TOOL] [AVISO] Nenhuma usina encontrada com nomes válidos, tentando usar índice...")
                        for idx in hidr.cadastro.index:
                            try:
                                codigo_hidr = int(idx) if isinstance(idx, (int, float)) else None
                                if codigo_hidr and codigo_hidr > 0:
                                    # Tentar encontrar nome em qualquer coluna de texto
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
                            safe_print(f"[UH TOOL] [DEBUG] Usinas encontradas usando índice: {len(cache_completo)}")
                            _HIDR_MAPPING_CACHE = cache_completo
                            _HIDR_CACHE_DECK_PATH = hidr_path
                            mapeamento = {
                                codigo: cache_completo.get(codigo, f"Usina {codigo}")
                                for codigo in codigos_usinas
                            }
                            break
                            
            except Exception as e:
                safe_print(f"[UH TOOL] [AVISO] Erro ao ler hidr.dat {hidr_path}: {e}")
                continue
        
        # Preencher códigos sem nome com formato genérico
        for codigo in codigos_usinas:
            if codigo not in mapeamento:
                mapeamento[codigo] = f"Usina {codigo}"
        
        safe_print(f"[UH TOOL] Mapeamento completo: {len(mapeamento)} usinas ({len([c for c in codigos_usinas if mapeamento.get(c, '').startswith('Usina ')])} genéricas)")
        return mapeamento
    
    def _extract_usina_from_query(
        self, 
        query: str, 
        dadger: Any, 
        data_usinas: list,
        mapeamento_codigo_nome: Dict[int, str]
    ) -> Optional[int]:
        """
        Extrai código da usina da query usando matching inteligente.
        ESPELHADO do ModifOperacaoTool do NEWAVE.
        
        Prioridade:
        1. Código numérico explícito
        2. Match exato do nome completo
        3. Match do nome completo como palavra (word boundary)
        4. Match por palavra-chave do nome
        
        Args:
            query: Query do usuário
            dadger: Instância do Dadger
            data_usinas: Lista de dados das usinas
            mapeamento_codigo_nome: Mapeamento código -> nome (obtido do HIDR.DAT)
            
        Returns:
            Código da usina ou None
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
                    # Verificar se existe nos dados
                    if any(d.get('codigo_usina') == codigo for d in data_usinas):
                        safe_print(f"[UH TOOL] [OK] Codigo {codigo} encontrado por padrao numerico")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina usando mapeamento (HIDR.DAT)
        if not mapeamento_codigo_nome:
            safe_print(f"[UH TOOL] [AVISO] Mapeamento vazio, tentando busca por palavras-chave conhecidas...")
            # Fallback: usar mapeamento conhecido de nomes de usinas para códigos
            # Baseado em usinas hidrelétricas comuns no sistema brasileiro
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
            }
            
            # Buscar palavras-chave na query
            palavras_query = query_lower.split()
            palavras_significativas = [p for p in palavras_query if len(p) > 3]
            
            for palavra in palavras_significativas:
                for nome_usina, codigos_possiveis in mapeamento_conhecido.items():
                    if palavra in nome_usina or nome_usina in palavra:
                        # Verificar qual código existe nos dados
                        for codigo in codigos_possiveis:
                            if any(d.get('codigo_usina') == codigo for d in data_usinas):
                                safe_print(f"[UH TOOL] [OK] Codigo {codigo} encontrado por palavra-chave '{palavra}' -> '{nome_usina}'")
                                return codigo
            
            safe_print(f"[UH TOOL] [AVISO] Nenhuma usina encontrada por palavras-chave conhecidas")
            return None
        
        # Filtrar apenas usinas com nomes reais (não "Usina X")
        usinas_com_nome = [
            {'codigo': codigo, 'nome': nome}
            for codigo, nome in mapeamento_codigo_nome.items()
            if nome and nome != f"Usina {codigo}" and not nome.startswith("Usina ")
        ]
        
        # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
        usinas_sorted = sorted(usinas_com_nome, key=lambda x: len(x['nome']), reverse=True)
        
        safe_print(f"[UH TOOL] Buscando por nome entre {len(usinas_sorted)} usinas com nomes reais")
        
        # ETAPA 2.1: Match exato do nome completo (prioridade máxima)
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Match exato do nome completo
            if nome_usina_lower == query_lower:
                safe_print(f"[UH TOOL] [OK] Codigo {codigo_usina} encontrado por match exato '{nome_usina}'")
                return codigo_usina
            
            # Match exato do nome completo dentro da query (como palavra completa)
            if len(nome_usina_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                # Usar word boundaries para evitar matches parciais
                pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                if re.search(pattern, query_lower):
                    safe_print(f"[UH TOOL] [OK] Codigo {codigo_usina} encontrado por nome completo '{nome_usina}' na query")
                    return codigo_usina
        
        # ETAPA 2.2: Buscar por palavras-chave do nome (apenas se match exato não encontrou)
        palavras_ignorar = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 
            'em', 'na', 'no', 'nas', 'nos', 'usina', 'usinas', 'uh', 
            'decomp', 'bloco', 'registro', 'hidrelétrica', 'hidreletrica'
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
                # Ordenar palavras por tamanho (maior primeiro)
                palavras_nome_sorted = sorted(palavras_nome, key=len, reverse=True)
                
                for palavra in palavras_nome_sorted:
                    # Apenas palavras com mais de 3 caracteres
                    if len(palavra) > 3:
                        # Verificar se a palavra está na query como palavra completa
                        pattern = r'\b' + re.escape(palavra) + r'\b'
                        if re.search(pattern, query_lower):
                            palavras_candidatas.append({
                                'codigo': codigo_usina,
                                'nome': nome_usina,
                                'palavra': palavra,
                                'tamanho': len(palavra),
                                'tamanho_nome': len(nome_usina_lower)
                            })
            
            # Se encontrou candidatos, escolher o melhor (palavra mais longa + nome mais específico)
            if palavras_candidatas:
                melhor_match = max(palavras_candidatas, key=lambda x: (x['tamanho'], x['tamanho_nome']))
                safe_print(f"[UH TOOL] [OK] Codigo {melhor_match['codigo']} encontrado por palavra-chave '{melhor_match['palavra']}' do nome '{melhor_match['nome']}'")
                return melhor_match['codigo']
        
        safe_print(f"[UH TOOL] [AVISO] Nenhuma usina especifica detectada na query")
        return None
    
    def _extract_search_term(self, query: str) -> Optional[str]:
        """
        Extrai termo de busca da query quando não há código numérico.
        Remove palavras-chave comuns e retorna o termo relevante.
        """
        query_lower = query.lower()
        
        # Palavras-chave a remover
        palavras_ignorar = [
            "uh", "decomp", "usina", "usinas", "hidrelétrica", "hidreletrica",
            "bloco", "registro", "de", "da", "do", "das", "dos",
            "volume", "inicial", "vini", "ree", "reservatório", "equivalente",
            "vazão", "minima", "evaporação", "evaporacao", "operação", "operacao",
            "mostrar", "mostre", "listar", "liste", "quais", "quais são"
        ]
        
        # Remover palavras-chave conhecidas
        palavras = query_lower.split()
        palavras_filtradas = [p for p in palavras if p not in palavras_ignorar]
        
        # Juntar palavras restantes (pode ser um nome como "furnas", "tucurui", etc)
        termo = " ".join(palavras_filtradas).strip()
        
        safe_print(f"[UH TOOL] Palavras originais: {palavras}")
        safe_print(f"[UH TOOL] Palavras filtradas: {palavras_filtradas}")
        safe_print(f"[UH TOOL] Termo final: '{termo}'")
        
        # Se o termo tiver mais de 2 caracteres e não for apenas números, retornar
        if len(termo) > 2 and not termo.isdigit():
            return termo
        
        return None
    
    def _find_ree_by_name(self, dadger: Any, termo_busca: str, data_usinas: list) -> Optional[int]:
        """
        Tenta encontrar código de REE pelo nome.
        Busca no cadastro de REEs do dadger ou usa mapeamento conhecido.
        
        Args:
            dadger: Instância do Dadger
            termo_busca: Termo a buscar (ex: "furnas")
            data_usinas: Lista de dados de usinas já carregados (para verificar REEs existentes)
        """
        termo_upper = termo_busca.upper()
        
        try:
            # Estratégia 1: Tentar acessar cadastro de REEs do dadger
            # No idecomp, o método pode ser 're' (registro RE)
            if hasattr(dadger, 're'):
                try:
                    rees_data = dadger.re(df=True)
                    if rees_data is not None:
                        if isinstance(rees_data, pd.DataFrame):
                            # Buscar por similaridade de nome
                            for idx, row in rees_data.iterrows():
                                # Verificar todas as colunas que podem conter nomes
                                for col in rees_data.columns:
                                    nome_ree = str(row[col]).upper().strip()
                                    # Verificar se o termo está no nome ou vice-versa
                                    if termo_upper in nome_ree or nome_ree in termo_upper:
                                        # Tentar encontrar código do REE
                                        # Geralmente a primeira coluna ou coluna com 'codigo'
                                        for cod_col in rees_data.columns:
                                            if 'codigo' in cod_col.lower() or cod_col.lower() in ['ree', 'numero']:
                                                try:
                                                    codigo = int(row[cod_col])
                                                    # Verificar se este REE existe nos dados das usinas
                                                    if any(d.get('codigo_ree') == codigo for d in data_usinas):
                                                        return codigo
                                                except (ValueError, TypeError):
                                                    continue
                except Exception:
                    pass
            
            # Estratégia 2: Usar mapeamento conhecido e verificar se o REE existe no deck
            mapeamento_rees = {
                "furnas": [1, 10],
                "tucurui": [2, 20],
                "itaipu": [3, 30],
                "sobradinho": [4, 40],
                "paulo afonso": [5, 50],
                "xingo": [6, 60],
                "serra da mesa": [7],
                "emborcacao": [8],
                "nova ponte": [9],
            }
            
            safe_print(f"[UH TOOL] Buscando no mapeamento conhecido de REEs...")
            for nome, codigos in mapeamento_rees.items():
                if nome.upper() in termo_upper or termo_upper in nome.upper():
                    safe_print(f"[UH TOOL] Match encontrado no mapeamento: {nome} -> {codigos}")
                    # Verificar qual dos códigos existe nos dados das usinas
                    rees_existentes = {d.get('codigo_ree') for d in data_usinas if d.get('codigo_ree') is not None}
                    safe_print(f"[UH TOOL] REEs existentes nos dados: {sorted(rees_existentes)}")
                    for codigo in codigos:
                        if codigo in rees_existentes:
                            safe_print(f"[UH TOOL] [OK] Codigo REE {codigo} encontrado nos dados!")
                            return codigo
                    safe_print(f"[UH TOOL] [AVISO] Nenhum dos codigos {codigos} existe nos dados")
                    
        except Exception as e:
            # Se houver erro, continuar tentando outras estratégias
            pass
        
        return None
    
    def _uh_to_dict(self, uh_obj) -> Dict[str, Any]:
        """Converte objeto UH para dict."""
        if isinstance(uh_obj, dict):
            return uh_obj
        if hasattr(uh_obj, '__dict__'):
            return uh_obj.__dict__
        # Se for registro do idecomp, extrair atributos conhecidos
        # Tentar múltiplas variações de nome de campo para volume_inicial
        volume_inicial = (
            getattr(uh_obj, 'volume_inicial', None) or
            getattr(uh_obj, 'vini', None) or
            getattr(uh_obj, 'VINI', None)
        )
        return {
            "codigo_usina": getattr(uh_obj, 'codigo_usina', None),
            "codigo_ree": getattr(uh_obj, 'codigo_ree', None),
            "volume_inicial": volume_inicial,
            "vini": volume_inicial,  # Alias para compatibilidade
            "vazao_minima": getattr(uh_obj, 'vazao_minima', None) or getattr(uh_obj, 'defmin', None),
            "evaporacao": getattr(uh_obj, 'evaporacao', None) or getattr(uh_obj, 'evap', None),
            "operacao": getattr(uh_obj, 'operacao', None) or getattr(uh_obj, 'oper', None),
            "volume_morto_inicial": getattr(uh_obj, 'volume_morto_inicial', None) or getattr(uh_obj, 'vmortoin', None),
            "limite_superior": getattr(uh_obj, 'limite_superior', None) or getattr(uh_obj, 'limsup', None),
        }

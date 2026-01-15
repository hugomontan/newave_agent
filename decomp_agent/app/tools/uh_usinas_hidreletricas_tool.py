"""
Tool para consultar informações do Bloco UH (Usinas Hidrelétricas) do DECOMP.
Acessa dados de volume inicial, REE, evaporação e operação das usinas hidrelétricas.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from difflib import SequenceMatcher


class UHUsinasHidrelétricasTool(DECOMPTool):
    """
    Tool para consultar informações do Bloco UH (Usinas Hidrelétricas) do DECOMP.
    
    Dados disponíveis:
    - Código da usina
    - Código do REE
    - Volume inicial (VINI)
    - Vazão mínima (DEFMIN)
    - Evaporação (EVAP)
    - Operação (OPER)
    - Volume morto inicial (VMORTOINI)
    - Limite superior (LIMSUP)
    - Flag BH (Bacia Hidrográfica)
    - Flag NW (Newave)
    """
    
    def get_name(self) -> str:
        return "UHUsinasHidrelétricasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre usinas hidrelétricas do Bloco UH.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "usina hidrelétrica",
            "usina hidreletrica",
            "bloco uh",
            "registro uh",
            "volume inicial",
            "volume inicial usina",
            "vini",
            "ree",
            "evaporação",
            "evaporacao",
            "vazão mínima",
            "vazao minima",
            "defmin",
            "oper",
            "volume morto",
            "vmortoin",
            "usinas do decomp",
            "uh decomp",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Bloco UH (Usinas Hidrelétricas) do DECOMP.
        
        Acessa dados do registro UH que define:
        - Volume inicial dos reservatórios (VINI)
        - Código do REE (Reservatório Equivalente de Energia)
        - Vazão mínima de defluência (DEFMIN)
        - Consideração de evaporação (EVAP)
        - Modo de operação (OPER)
        - Volume morto inicial (VMORTOINI)
        - Limite superior (LIMSUP)
        
        Exemplos de queries:
        - "Quais são as usinas hidrelétricas do deck?"
        - "Qual o volume inicial da usina 1?"
        - "Mostre todas as usinas do REE 10"
        - "Usinas com evaporação considerada"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre usinas hidrelétricas do Bloco UH.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados das usinas hidrelétricas
        """
        try:
            # Localizar arquivo dadger (pode ser .rvx, .rv0 ou .rv2)
            dadger_paths = [
                os.path.join(self.deck_path, "dadger.rvx"),
                os.path.join(self.deck_path, "dadger.rv0"),
                os.path.join(self.deck_path, "dadger.rv2"),
            ]
            
            dadger_path = None
            for path in dadger_paths:
                if os.path.exists(path):
                    dadger_path = path
                    break
            
            if not dadger_path:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (.rvx, .rv0 ou .rv2)"
                }
            
            # Ler arquivo dadger
            dadger = Dadger.read(dadger_path)
            
            # Extrair filtros da query (códigos numéricos)
            codigo_usina = self._extract_codigo_usina(query)
            codigo_ree = self._extract_codigo_ree(query)
            
            safe_print(f"[UH TOOL] Query recebida: {query}")
            safe_print(f"[UH TOOL] Codigo usina extraido: {codigo_usina}")
            safe_print(f"[UH TOOL] Codigo REE extraido: {codigo_ree}")
            
            # Obter dados das usinas (se houver código, já filtra aqui)
            uh_data = dadger.uh(
                codigo_usina=codigo_usina,
                codigo_ree=codigo_ree,
                df=True  # Retornar como DataFrame
            )
            
            if uh_data is None or (isinstance(uh_data, pd.DataFrame) and uh_data.empty):
                return {
                    "success": False,
                    "error": "Nenhuma usina encontrada com os filtros especificados"
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
            
            # SEMPRE tentar extrair usina da query (código ou nome) - PRIORIDADE MÁXIMA
            # Se encontrar, mostrar APENAS essa usina (sem filtro no frontend)
            if codigo_usina is None:
                safe_print(f"[UH TOOL] Tentando extrair usina da query (código ou nome)...")
                codigo_usina_extraido = self._extract_usina_from_query(query, dadger, data, mapeamento_codigo_nome)
                if codigo_usina_extraido is not None:
                    safe_print(f"[UH TOOL] [OK] Usina encontrada: codigo {codigo_usina_extraido}")
                    codigo_usina = codigo_usina_extraido
                    # Filtrar APENAS essa usina - query específica para uma única usina
                    total_antes = len(data)
                    data = [d for d in data if d.get('codigo_usina') == codigo_usina]
                    safe_print(f"[UH TOOL] Filtro aplicado: {total_antes} -> {len(data)} registros (Usina {codigo_usina})")
            
            # Se ainda não encontrou usina, tentar buscar por REE (apenas se não houver busca por usina)
            if codigo_usina is None and codigo_ree is None:
                termo_busca = self._extract_search_term(query)
                if termo_busca:
                    safe_print(f"[UH TOOL] Buscando REE por nome: {termo_busca}")
                    codigo_ree_por_nome = self._find_ree_by_name(dadger, termo_busca, data)
                    if codigo_ree_por_nome is not None:
                        total_antes = len(data)
                        data = [d for d in data if d.get('codigo_ree') == codigo_ree_por_nome]
                        safe_print(f"[UH TOOL] Filtro aplicado: {total_antes} -> {len(data)} usinas (REE {codigo_ree_por_nome})")
                        codigo_ree = codigo_ree_por_nome
            
            # Filtrar por volume inicial se mencionado na query
            if "volume inicial" in query.lower() or "vini" in query.lower():
                volume_ini = self._extract_volume_inicial(query)
                if volume_ini is not None:
                    data = [d for d in data if abs(d.get('volume_inicial', 0) - volume_ini) < 0.01]
            
            safe_print(f"[UH TOOL] Retornando {len(data)} usinas")
            safe_print(f"[UH TOOL] Filtros aplicados: usina={codigo_usina}, ree={codigo_ree}")
            
            # Preparar filtros com nome da usina (se houver)
            filtros_dict = {
                "codigo_usina": codigo_usina,
                "codigo_ree": codigo_ree,
            }
            if codigo_usina is not None:
                nome_usina = mapeamento_codigo_nome.get(codigo_usina)
                if nome_usina and nome_usina != f"Usina {codigo_usina}":
                    filtros_dict["nome_usina"] = nome_usina
            
            return {
                "success": True,
                "data": data,
                "total_usinas": len(data),
                "filtros": filtros_dict,
                "mapeamento_codigo_nome": mapeamento_codigo_nome,
                "tool": self.get_name()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao consultar Bloco UH: {str(e)}",
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
        Cria mapeamento código -> nome das usinas usando HIDR.DAT do NEWAVE.
        Similar ao mecanismo "de para" do newave_agent.
        
        Args:
            dadger: Instância do Dadger
            data_usinas: Lista de dados das usinas já carregados
            
        Returns:
            Dict com mapeamento {codigo_usina: nome_usina}
        """
        mapeamento = {}
        codigos_usinas = {d.get('codigo_usina') for d in data_usinas if d.get('codigo_usina') is not None}
        
        safe_print(f"[UH TOOL] Criando mapeamento para {len(codigos_usinas)} usinas")
        
        # Estratégia: Buscar HIDR.DAT do NEWAVE (mecanismo "de para")
        # Tentar múltiplos caminhos possíveis
        possible_newave_paths = [
            # Caminho relativo: nw_multi/newave_agent/decks
            os.path.join(os.path.dirname(os.path.dirname(self.deck_path)), "newave_agent", "decks"),
            # Caminho absoluto alternativo
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(self.deck_path))), "newave_agent", "decks"),
        ]
        
        # Também tentar usar o deck_path atual como referência para encontrar NEWAVE
        deck_path_parts = self.deck_path.split(os.sep)
        if "decomp_agent" in deck_path_parts:
            idx = deck_path_parts.index("decomp_agent")
            base_path = os.sep.join(deck_path_parts[:idx])
            possible_newave_paths.append(os.path.join(base_path, "newave_agent", "decks"))
        
        hidr_encontrado = False
        for newave_decks_path in possible_newave_paths:
            if not os.path.exists(newave_decks_path):
                continue
            
            safe_print(f"[UH TOOL] Buscando HIDR.DAT em: {newave_decks_path}")
            
            # Buscar em todos os decks NEWAVE
            try:
                for deck_dir in os.listdir(newave_decks_path):
                    deck_full_path = os.path.join(newave_decks_path, deck_dir)
                    if not os.path.isdir(deck_full_path):
                        continue
                    
                    hidr_path = os.path.join(deck_full_path, "HIDR.DAT")
                    if not os.path.exists(hidr_path):
                        hidr_path = os.path.join(deck_full_path, "hidr.dat")
                    
                    if os.path.exists(hidr_path):
                        try:
                            from inewave.newave import Hidr
                            hidr = Hidr.read(hidr_path)
                            if hidr.cadastro is not None and not hidr.cadastro.empty:
                                safe_print(f"[UH TOOL] [OK] HIDR.DAT encontrado: {hidr_path}")
                                for _, hidr_row in hidr.cadastro.iterrows():
                                    codigo_hidr = int(hidr_row.get('codigo_usina', 0))
                                    if codigo_hidr in codigos_usinas and codigo_hidr not in mapeamento:
                                        nome_hidr = str(hidr_row.get('nome_usina', '')).strip()
                                        if nome_hidr and nome_hidr != 'nan' and nome_hidr != '' and nome_hidr.lower() != 'none':
                                            mapeamento[codigo_hidr] = nome_hidr
                                            safe_print(f"[UH TOOL]   Mapeamento: {codigo_hidr} -> {nome_hidr}")
                                hidr_encontrado = True
                                # Continuar em outros decks para completar mapeamento
                        except Exception as e:
                            safe_print(f"[UH TOOL] [AVISO] Erro ao ler HIDR.DAT {hidr_path}: {e}")
                            continue
            except Exception as e:
                safe_print(f"[UH TOOL] [AVISO] Erro ao listar decks NEWAVE: {e}")
                continue
            
            if hidr_encontrado and len(mapeamento) >= len(codigos_usinas):
                # Mapeamento completo, não precisa continuar
                break
        
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
            safe_print(f"[UH TOOL] [AVISO] Mapeamento vazio, nao e possivel buscar por nome")
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
        return {
            "codigo_usina": getattr(uh_obj, 'codigo_usina', None),
            "codigo_ree": getattr(uh_obj, 'codigo_ree', None),
            "volume_inicial": getattr(uh_obj, 'volume_inicial', None),
            "vazao_minima": getattr(uh_obj, 'vazao_minima', None) or getattr(uh_obj, 'defmin', None),
            "evaporacao": getattr(uh_obj, 'evaporacao', None) or getattr(uh_obj, 'evap', None),
            "operacao": getattr(uh_obj, 'operacao', None) or getattr(uh_obj, 'oper', None),
            "volume_morto_inicial": getattr(uh_obj, 'volume_morto_inicial', None) or getattr(uh_obj, 'vmortoin', None),
            "limite_superior": getattr(uh_obj, 'limite_superior', None) or getattr(uh_obj, 'limsup', None),
        }

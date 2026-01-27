"""
Serviço unificado de matching de usinas térmicas para DECOMP.

Centraliza a lógica de identificação de usinas térmicas,
utilizando de-para via CSV para expandir abreviações antes do matching.
"""
import os
import re
import csv
from typing import Optional, Dict, List, Any, Tuple, Union
from difflib import SequenceMatcher
import pandas as pd
from pathlib import Path

from backend.decomp.config import safe_print
from backend.core.config import debug_print


# Caminho padrão para o CSV de de-para
DEFAULT_CSV_PATH = os.path.join(
    Path(__file__).parent.parent,
    "data",
    "deparatermicas_decomp.csv"
)


class DecompThermalPlantMatcher:
    """
    Serviço unificado de matching de usinas térmicas para DECOMP.
    
    Utiliza um CSV de de-para para expandir abreviações dos nomes das usinas
    antes de fazer o matching, melhorando a taxa de acerto.
    
    Attributes:
        abbrev_to_full: Mapeamento nome_decomp.lower() -> nome_completo.lower()
        full_to_abbrev: Mapeamento nome_completo.lower() -> nome_decomp.lower()
        code_to_names: Mapeamento codigo -> (nome_decomp, nome_completo)
    """
    
    # Palavras comuns a ignorar no matching
    STOPWORDS = {
        'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os',
        'em', 'na', 'no', 'nas', 'nos', 'para', 'por', 'com', 'sem',
        'à', 'ao', 'aos', 'informacoes', 'informações', 'dados',
        'usina', 'térmica', 'termica', 'classe', 'cadastro',
        'características', 'caracteristicas', 'termoeletrica',
        'termeletrica', 'termelétrica', 'termoelétrica'
    }
    
    def __init__(self, csv_path: str = None):
        """
        Inicializa o matcher carregando os mapeamentos do CSV.
        
        Args:
            csv_path: Caminho para o CSV de de-para. Se None, usa o caminho padrão.
        """
        self.csv_path = csv_path or DEFAULT_CSV_PATH
        self.abbrev_to_full: Dict[str, str] = {}
        self.full_to_abbrev: Dict[str, str] = {}
        self.code_to_names: Dict[int, Tuple[str, str]] = {}  # codigo -> (nome_decomp, nome_completo)
        
        self._load_name_mapping_from_csv()
    
    def _load_name_mapping_from_csv(self) -> None:
        """
        Carrega os mapeamentos bidirecionais do CSV de de-para.
        
        O CSV deve ter as colunas:
        - codigo: Código numérico da usina
        - nome_decomp: Nome como aparece no arquivo DECOMP
        - nome_completo: Nome expandido/curado manualmente
        
        Cria três dicionários:
        - abbrev_to_full: nome_decomp.lower() -> nome_completo.lower()
        - full_to_abbrev: nome_completo.lower() -> nome_decomp.lower()
        - code_to_names: codigo -> (nome_decomp, nome_completo)
        """
        if not os.path.exists(self.csv_path):
            debug_print(f"[DECOMP_THERMAL_MATCHER] ⚠️ CSV de de-para não encontrado: {self.csv_path}")
            debug_print("[DECOMP_THERMAL_MATCHER] ⚠️ Matching funcionará sem expansão de abreviações")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        codigo = int(row.get('codigo', 0))
                        nome_decomp = str(
                            row.get('nome_decomp') or row.get('nome_arquivo') or ''
                        ).strip()
                        nome_completo = str(
                            row.get('nome_completo')
                            or row.get('Nome completo ')
                            or row.get('Nome completo')
                            or row.get('usina ')
                            or row.get('usina')
                            or ''
                        ).strip()
                        if not nome_decomp:
                            continue
                        if not nome_completo:
                            nome_completo = nome_decomp
                        
                        # Normalizar para lowercase
                        nome_decomp_lower = nome_decomp.lower()
                        nome_completo_lower = nome_completo.lower()
                        
                        # Só criar mapeamento se forem diferentes
                        if nome_decomp_lower != nome_completo_lower:
                            self.abbrev_to_full[nome_decomp_lower] = nome_completo_lower
                            self.full_to_abbrev[nome_completo_lower] = nome_decomp_lower
                        
                        # Sempre criar mapeamento por código
                        self.code_to_names[codigo] = (nome_decomp, nome_completo)
                        
                    except (ValueError, KeyError) as e:
                        debug_print(f"[DECOMP_THERMAL_MATCHER] ⚠️ Erro ao processar linha do CSV: {e}")
                        continue
            
            debug_print(f"[DECOMP_THERMAL_MATCHER] ✅ CSV carregado: {len(self.abbrev_to_full)} mapeamentos de abreviações")
            debug_print(f"[DECOMP_THERMAL_MATCHER] ✅ Total de usinas mapeadas: {len(self.code_to_names)}")
            
        except Exception as e:
            debug_print(f"[DECOMP_THERMAL_MATCHER] ❌ Erro ao carregar CSV: {e}")
    
    def _expand_abbreviations(self, query: str) -> str:
        """
        Expande abreviações na query usando o de-para.
        
        Busca tokens da query nos mapeamentos e substitui abreviações
        por nomes completos.
        
        Args:
            query: Query original do usuário
            
        Returns:
            Query com abreviações expandidas
        """
        if not self.abbrev_to_full:
            return query
        
        query_lower = query.lower()
        expanded = query_lower
        
        # Ordenar por tamanho (maior primeiro) para evitar substituições parciais
        sorted_abbrevs = sorted(self.abbrev_to_full.keys(), key=len, reverse=True)
        
        for abbrev in sorted_abbrevs:
            full_name = self.abbrev_to_full[abbrev]
            
            # Verificar se a abreviação está na query
            if abbrev in expanded:
                # Usar word boundaries para evitar substituições parciais
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                if re.search(pattern, expanded):
                    expanded = re.sub(pattern, full_name, expanded)
                    debug_print(f"[DECOMP_THERMAL_MATCHER] ✅ Abreviação expandida: '{abbrev}' -> '{full_name}'")
        
        if expanded != query_lower:
            debug_print(f"[DECOMP_THERMAL_MATCHER] Query expandida: '{query_lower}' -> '{expanded}'")
        
        return expanded
    
    def _prepare_plants_list(
        self, 
        plants_data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Normaliza dados de entrada para formato padronizado.
        
        Aceita diferentes formatos de entrada e retorna lista padronizada:
        [{'codigo': int, 'nome': str}, ...]
        
        Args:
            plants_data: Dados das plantas em diferentes formatos:
                - DataFrame com colunas 'codigo_usina' e 'nome_usina'
                - Lista de dicts com 'codigo_usina' e 'nome_usina'
                - Dict mapeando codigo -> nome
                
        Returns:
            Lista de dicts no formato padronizado
        """
        result = []
        
        if isinstance(plants_data, pd.DataFrame):
            # DataFrame: iterar sobre linhas
            for _, row in plants_data.iterrows():
                codigo = row.get('codigo_usina')
                nome = str(row.get('nome_usina', '')).strip()
                if codigo is not None and nome:
                    result.append({'codigo': int(codigo), 'nome': nome})
        
        elif isinstance(plants_data, list):
            # Lista de dicts
            for item in plants_data:
                codigo = item.get('codigo_usina', item.get('codigo'))
                nome = str(item.get('nome_usina', item.get('nome', ''))).strip()
                if codigo is not None and nome:
                    result.append({'codigo': int(codigo), 'nome': nome})
        
        elif isinstance(plants_data, dict):
            # Dict mapeando codigo -> nome
            for codigo, nome in plants_data.items():
                if codigo is not None and nome:
                    result.append({'codigo': int(codigo), 'nome': str(nome).strip()})
        
        return result
    
    def _extract_numeric_code(
        self, 
        query: str, 
        valid_codes: List[int],
        entity_type: str = "usina"
    ) -> Optional[int]:
        """
        Extrai código numérico da query usando padrões regex.
        
        Args:
            query: Query do usuário
            valid_codes: Lista de códigos válidos para validação
            entity_type: "usina" ou "classe" para selecionar padrões apropriados
            
        Returns:
            Código da usina/classe ou None se não encontrado
        """
        query_lower = query.lower()
        
        # Padrões para usinas térmicas
        usina_patterns = [
            r'usina\s*(\d+)',
            r'usina\s*térmica\s*(\d+)',
            r'usina\s*termica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
            r'térmica\s*(\d+)',
            r'termica\s*(\d+)',
            r'ute\s*(\d+)',
        ]
        
        # Padrões para classes térmicas
        classe_patterns = [
            r'classe\s*(\d+)',
            r'classe\s*térmica\s*(\d+)',
            r'classe\s*termica\s*(\d+)',
            r'classe\s*#?\s*(\d+)',
        ]
        
        # Selecionar padrões baseado no tipo de entidade
        patterns = classe_patterns if entity_type == "classe" else usina_patterns
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if codigo in valid_codes:
                        debug_print(f"[DECOMP_THERMAL_MATCHER] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo
                except ValueError:
                    continue
        
        return None
    
    def _create_expanded_list_from_csv(self) -> Tuple[List[str], Dict[str, int]]:
        """
        (Legado) Cria lista expandida de nomes DIRETAMENTE do CSV.
        Evitar usar: códigos do CSV podem não corresponder ao deck em uso.
        """
        available_names = []
        name_to_codigo = {}
        for codigo, (nome_decomp, nome_completo) in self.code_to_names.items():
            if nome_decomp and nome_decomp.strip():
                available_names.append(nome_decomp)
                name_to_codigo[nome_decomp.lower()] = codigo
            if nome_completo and nome_completo.strip():
                nome_completo_lower = nome_completo.lower()
                nome_decomp_lower = (nome_decomp or "").lower()
                if nome_completo_lower != nome_decomp_lower:
                    available_names.append(nome_completo)
                    name_to_codigo[nome_completo_lower] = codigo
        return available_names, name_to_codigo

    def _create_expanded_list_from_deck_and_csv(
        self, plants_list: List[Dict[str, Any]]
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        Cria lista de nomes e mapeamento nome -> código usando o DECK como fonte
        de verdade. O CSV é usado apenas para aliases (nome_completo -> código
        do deck quando nome_decomp bate com nome_usina do deck).

        Evita discrepância entre códigos do CSV (ex. outro deck) e do deck atual:
        o código retornado é sempre o do DataFrame/Bloco CT.
        """
        available_names: List[str] = []
        name_to_codigo: Dict[str, int] = {}

        # 1) Deck: nome_usina -> codigo_usina (fonte de verdade)
        seen = set()
        for p in plants_list:
            codigo = p.get("codigo")
            nome = (p.get("nome") or "").strip()
            if codigo is None or not nome:
                continue
            codigo = int(codigo)
            k = nome.lower()
            if k not in seen:
                seen.add(k)
                name_to_codigo[k] = codigo
                available_names.append(nome)

        # 2) CSV: aliases. Só adiciona nome_completo -> codigo DECK se
        #    nome_decomp do CSV bater com algum nome do deck.
        deck_names_lower = {n.lower() for n in name_to_codigo}
        for _, (nome_decomp, nome_completo) in self.code_to_names.items():
            nome_decomp = (nome_decomp or "").strip()
            nome_completo = (nome_completo or "").strip()
            if not nome_decomp or not nome_completo:
                continue
            nd = nome_decomp.lower()
            nc = nome_completo.lower()
            if nc == nd:
                continue
            if nd not in deck_names_lower:
                continue
            codigo_deck = name_to_codigo.get(nd)
            if codigo_deck is None:
                continue
            if nc not in name_to_codigo:
                name_to_codigo[nc] = codigo_deck
                available_names.append(nome_completo)
                debug_print(
                    f"[DECOMP_THERMAL_MATCHER]   Alias CSV: '{nome_completo}' -> codigo deck {codigo_deck} (nome_decomp '{nome_decomp}')"
                )

        debug_print(
            f"[DECOMP_THERMAL_MATCHER] Lista deck+aliases: {len(available_names)} nomes, {len(name_to_codigo)} -> codigo (deck)"
        )
        return available_names, name_to_codigo
    
    def _extract_by_name(
        self,
        query: str,
        threshold: float = 0.5,
        plants_list: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[int]:
        """
        Extrai código da usina por matching de nome.

        Usa o DECK (plants_list) como fonte de verdade para códigos. O CSV serve
        só para aliases (nome_completo -> código do deck). Assim evitamos
        discrepância quando o CSV foi gerado a partir de outro deck.
        """
        query_lower = query.lower().strip()
        from backend.core.utils.usina_name_matcher import find_usina_match

        if plants_list:
            available_names, name_to_codigo = self._create_expanded_list_from_deck_and_csv(
                plants_list
            )
        else:
            available_names, name_to_codigo = self._create_expanded_list_from_csv()

        if not available_names:
            debug_print(
                "[DECOMP_THERMAL_MATCHER] Nenhum nome disponivel (deck ou CSV) para matching"
            )
            return None

        # ETAPA 1: Match exato (nomes do deck + aliases)
        for nome, codigo in name_to_codigo.items():
            if nome.strip() == query_lower:
                debug_print(
                    f"[DECOMP_THERMAL_MATCHER] Codigo {codigo} encontrado por match exato: '{nome}'"
                )
                return codigo

        # Match exato do nome dentro da query (word boundaries); maior primeiro
        for nome in sorted(name_to_codigo.keys(), key=len, reverse=True):
            if len(nome) >= 4:
                pattern = r"\b" + re.escape(nome) + r"\b"
                if re.search(pattern, query_lower):
                    codigo = name_to_codigo[nome]
                    debug_print(
                        f"[DECOMP_THERMAL_MATCHER] Codigo {codigo} encontrado por nome na query: '{nome}'"
                    )
                    return codigo

        # ETAPA 2: Fuzzy matching
        match_result = find_usina_match(query, available_names, threshold=threshold)
        if match_result:
            matched_name, score = match_result
            matched_lower = matched_name.lower()
            if matched_lower in name_to_codigo:
                codigo = name_to_codigo[matched_lower]
                debug_print(
                    f"[DECOMP_THERMAL_MATCHER] Codigo {codigo} encontrado via matcher: '{matched_name}' (score: {score:.2f})"
                )
                return codigo

        # ETAPA 3: Fallback keyword matching (usando mapa deck+aliases)
        debug_print(
            "[DECOMP_THERMAL_MATCHER] ETAPA 3: Tentando fallback keyword matching..."
        )
        return self._fallback_keyword_matching(
            query_lower, available_names, name_to_codigo
        )
    
    def _fallback_keyword_matching(
        self,
        query_lower: str,
        available_names: List[str],
        name_to_codigo: Dict[str, int],
    ) -> Optional[int]:
        """
        Fallback com palavras-chave e similaridade. Usa o mapa nome -> código
        (deck + aliases), nunca códigos do CSV.
        """
        palavras_query = [
            p for p in query_lower.split()
            if len(p) > 2 and p not in self.STOPWORDS
        ]
        if not palavras_query:
            return None

        candidatos: List[Tuple[int, str, float]] = []
        for nome in available_names:
            nome_lower = nome.lower().strip()
            palavras_nome = [
                p for p in nome_lower.split()
                if len(p) > 2 and p not in self.STOPWORDS
            ]
            palavras_comuns = set(palavras_query) & set(palavras_nome)
            score = float(len(palavras_comuns))
            if palavras_query and all(p in palavras_nome for p in palavras_query):
                score += 10.0
            similarity = SequenceMatcher(None, query_lower, nome_lower).ratio()
            score += similarity * 5.0
            score += len(nome_lower) / 100.0
            if score > 0:
                codigo = name_to_codigo.get(nome_lower)
                if codigo is not None:
                    candidatos.append((codigo, nome, score))

        if candidatos:
            candidatos.sort(key=lambda x: x[2], reverse=True)
            melhor_codigo, melhor_nome, melhor_score = candidatos[0]
            debug_print(
                f"[DECOMP_THERMAL_MATCHER] Codigo {melhor_codigo} encontrado (fallback): '{melhor_nome}' (score: {melhor_score:.2f})"
            )
            return melhor_codigo
        return None
    
    def extract_plant_from_query(
        self,
        query: str,
        available_plants: Union[pd.DataFrame, List[Dict[str, Any]], Dict[int, str]],
        entity_type: str = "usina",
        threshold: float = 0.5
    ) -> Optional[int]:
        """
        Método principal para extrair código de usina/classe da query.
        
        Fluxo:
        1. Expandir abreviações via de-para
        2. Tentar extrair código numérico
        3. Tentar match por nome (exato, fuzzy, fallback)
        
        Args:
            query: Query do usuário
            available_plants: Dados das plantas disponíveis (DataFrame, list, ou dict)
            entity_type: "usina" ou "classe" - tipo de entidade a buscar
            threshold: Score mínimo para fuzzy matching (0.0 a 1.0)
            
        Returns:
            Código da usina/classe ou None se não encontrado
        """
        if not query:
            return None
        
        # ETAPA 1: Preparar lista de plantas (deck = fonte de verdade para códigos)
        plants_list = self._prepare_plants_list(available_plants)

        if not plants_list:
            debug_print(
                "[DECOMP_THERMAL_MATCHER] Nenhuma planta disponivel para matching"
            )
            return None

        valid_codes_deck = list({int(p["codigo"]) for p in plants_list})

        debug_print(
            f"[DECOMP_THERMAL_MATCHER] Iniciando matching para query: '{query[:50]}...'"
        )
        debug_print(f"[DECOMP_THERMAL_MATCHER] Tipo de entidade: {entity_type}")
        debug_print(
            f"[DECOMP_THERMAL_MATCHER] Plantas no DataFrame: {len(plants_list)}"
        )
        debug_print(
            f"[DECOMP_THERMAL_MATCHER] Codigos validos (deck): {len(valid_codes_deck)}"
        )

        expanded_query = self._expand_abbreviations(query)

        # ETAPA 2: Código numérico — validar contra CÓDIGOS DO DECK
        codigo = self._extract_numeric_code(
            expanded_query, valid_codes_deck, entity_type
        )
        if codigo is not None:
            debug_print(
                f"[DECOMP_THERMAL_MATCHER] Codigo {codigo} encontrado por padrao numerico (deck)"
            )
            return codigo

        if expanded_query != query.lower():
            codigo = self._extract_numeric_code(
                query, valid_codes_deck, entity_type
            )
            if codigo is not None:
                debug_print(
                    f"[DECOMP_THERMAL_MATCHER] Codigo {codigo} encontrado por padrao numerico (deck)"
                )
                return codigo

        # ETAPA 3: Match por nome (deck + aliases do CSV)
        codigo = self._extract_by_name(
            expanded_query, threshold, plants_list=plants_list
        )
        if codigo is not None:
            return codigo

        if expanded_query != query.lower():
            codigo = self._extract_by_name(
                query.lower(), threshold, plants_list=plants_list
            )
            if codigo is not None:
                return codigo

        debug_print(
            f"[DECOMP_THERMAL_MATCHER] Nenhuma {entity_type} especifica detectada na query"
        )
        return None


# Instância global para uso conveniente
_default_matcher: Optional[DecompThermalPlantMatcher] = None


def get_decomp_thermal_plant_matcher() -> DecompThermalPlantMatcher:
    """
    Obtém a instância global do DecompThermalPlantMatcher.
    
    Cria uma nova instância na primeira chamada (lazy initialization).
    
    Returns:
        Instância do DecompThermalPlantMatcher
    """
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = DecompThermalPlantMatcher()
    return _default_matcher

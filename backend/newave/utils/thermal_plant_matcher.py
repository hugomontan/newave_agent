"""
Serviço unificado de matching de usinas térmicas para NEWAVE.

Centraliza a lógica de identificação de usinas térmicas e classes térmicas,
utilizando de-para via CSV para expandir abreviações antes do matching.
"""
import os
import re
import csv
from typing import Optional, Dict, List, Any, Tuple, Union
from difflib import SequenceMatcher
import pandas as pd

from backend.newave.config import debug_print, safe_print


# Caminho padrão para o CSV de de-para
DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "deparatermicas.csv"
)


class ThermalPlantMatcher:
    """
    Serviço unificado de matching de usinas térmicas e classes térmicas.
    
    Utiliza um CSV de de-para para expandir abreviações dos nomes das usinas
    antes de fazer o matching, melhorando a taxa de acerto.
    
    Attributes:
        abbrev_to_full: Mapeamento nome_arquivo -> usina (expandido)
        full_to_abbrev: Mapeamento usina (expandido) -> nome_arquivo
        code_to_names: Mapeamento codigo -> (nome_arquivo, usina)
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
        self.code_to_names: Dict[int, Tuple[str, str]] = {}
        
        self._load_name_mapping_from_csv()
    
    def _load_name_mapping_from_csv(self) -> None:
        """
        Carrega os mapeamentos bidirecionais do CSV de de-para.
        
        O CSV deve ter as colunas:
        - codigo: Código numérico da usina
        - nome_arquivo: Nome como aparece no arquivo NEWAVE
        - usina: Nome expandido/curado manualmente
        
        Cria três dicionários:
        - abbrev_to_full: nome_arquivo.lower() -> usina.lower()
        - full_to_abbrev: usina.lower() -> nome_arquivo.lower()
        - code_to_names: codigo -> (nome_arquivo, usina)
        """
        if not os.path.exists(self.csv_path):
            debug_print(f"[THERMAL_MATCHER] ⚠️ CSV de de-para não encontrado: {self.csv_path}")
            debug_print("[THERMAL_MATCHER] ⚠️ Matching funcionará sem expansão de abreviações")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        codigo = int(row.get('codigo', 0))
                        nome_arquivo = str(row.get('nome_arquivo', '')).strip()
                        # A coluna 'usina' pode ter espaço extra no nome
                        usina = str(row.get('usina ', row.get('usina', ''))).strip()
                        
                        if not nome_arquivo or not usina:
                            continue
                        
                        # Normalizar para lowercase
                        nome_arquivo_lower = nome_arquivo.lower()
                        usina_lower = usina.lower()
                        
                        # Só criar mapeamento se forem diferentes
                        if nome_arquivo_lower != usina_lower:
                            self.abbrev_to_full[nome_arquivo_lower] = usina_lower
                            self.full_to_abbrev[usina_lower] = nome_arquivo_lower
                        
                        # Sempre criar mapeamento por código
                        self.code_to_names[codigo] = (nome_arquivo, usina)
                        
                    except (ValueError, KeyError) as e:
                        debug_print(f"[THERMAL_MATCHER] ⚠️ Erro ao processar linha do CSV: {e}")
                        continue
            
            debug_print(f"[THERMAL_MATCHER] ✅ CSV carregado: {len(self.abbrev_to_full)} mapeamentos de abreviações")
            debug_print(f"[THERMAL_MATCHER] ✅ Total de usinas mapeadas: {len(self.code_to_names)}")
            
        except Exception as e:
            debug_print(f"[THERMAL_MATCHER] ❌ Erro ao carregar CSV: {e}")
    
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
                    debug_print(f"[THERMAL_MATCHER] ✅ Abreviação expandida: '{abbrev}' -> '{full_name}'")
        
        if expanded != query_lower:
            debug_print(f"[THERMAL_MATCHER] Query expandida: '{query_lower}' -> '{expanded}'")
        
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
                        debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo
                except ValueError:
                    continue
        
        return None
    
    def _extract_by_name(
        self, 
        query: str, 
        plants_list: List[Dict[str, Any]],
        threshold: float = 0.5
    ) -> Optional[int]:
        """
        Extrai código da usina por matching de nome.
        
        Utiliza o matcher centralizado (find_usina_match) e fallback
        com palavras-chave e similaridade.
        
        Args:
            query: Query do usuário (já com abreviações expandidas)
            plants_list: Lista de plantas no formato [{'codigo': int, 'nome': str}, ...]
            threshold: Score mínimo para fuzzy matching
            
        Returns:
            Código da usina/classe ou None se não encontrado
        """
        if not plants_list:
            return None
        
        query_lower = query.lower()
        
        # Importar matcher centralizado
        from backend.core.utils.usina_name_matcher import find_usina_match, normalize_usina_name
        
        # Criar lista de nomes e mapeamento codigo -> nome
        available_names = []
        codigo_to_nome = {}
        
        for plant in plants_list:
            codigo = plant['codigo']
            nome = plant['nome']
            if nome and nome.lower() != 'nan':
                available_names.append(nome)
                codigo_to_nome[codigo] = nome
        
        if not available_names:
            return None
        
        # ETAPA 1: Match exato do nome completo (ordenado por tamanho, maior primeiro)
        sorted_plants = sorted(plants_list, key=lambda x: len(x['nome']), reverse=True)
        
        for plant in sorted_plants:
            nome = plant['nome']
            nome_lower = nome.lower().strip()
            
            if not nome_lower:
                continue
            
            # Match exato do nome completo
            if nome_lower == query_lower.strip():
                debug_print(f"[THERMAL_MATCHER] ✅ Código {plant['codigo']} encontrado por match exato '{nome}'")
                return plant['codigo']
            
            # Match exato do nome completo dentro da query (com word boundaries)
            if len(nome_lower) >= 4:
                pattern = r'\b' + re.escape(nome_lower) + r'\b'
                if re.search(pattern, query_lower):
                    debug_print(f"[THERMAL_MATCHER] ✅ Código {plant['codigo']} encontrado por nome completo '{nome}' na query")
                    return plant['codigo']
        
        # ETAPA 2: Usar matcher centralizado (fuzzy matching)
        match_result = find_usina_match(query, available_names, threshold=threshold)
        
        if match_result:
            matched_name, score = match_result
            # Encontrar código correspondente ao nome encontrado
            for codigo, nome in codigo_to_nome.items():
                if normalize_usina_name(nome) == normalize_usina_name(matched_name):
                    debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado via matcher centralizado: '{nome}' (score: {score:.2f})")
                    return codigo
        
        # ETAPA 3: Fallback com palavras-chave e similaridade
        return self._fallback_keyword_matching(query_lower, plants_list)
    
    def _fallback_keyword_matching(
        self, 
        query_lower: str, 
        plants_list: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Fallback inteligente usando palavras-chave e similaridade.
        
        Usado quando o matcher centralizado não encontra resultado.
        
        Args:
            query_lower: Query em lowercase
            plants_list: Lista de plantas
            
        Returns:
            Código da usina/classe ou None
        """
        # Extrair palavras significativas da query
        palavras_query = [
            p for p in query_lower.split() 
            if len(p) > 2 and p not in self.STOPWORDS
        ]
        
        if not palavras_query:
            return None
        
        candidatos = []
        
        for plant in plants_list:
            codigo = plant['codigo']
            nome = plant['nome'].lower().strip()
            
            if not nome:
                continue
            
            # Extrair palavras significativas do nome
            palavras_nome = [
                p for p in nome.split() 
                if len(p) > 2 and p not in self.STOPWORDS
            ]
            
            # Calcular score: quantas palavras da query estão no nome
            palavras_comuns = set(palavras_query) & set(palavras_nome)
            score = len(palavras_comuns)
            
            # Bonus se todas as palavras significativas da query estão no nome
            if palavras_query and all(p in palavras_nome for p in palavras_query):
                score += 10  # Bonus grande para match completo
            
            # Bonus por similaridade de strings
            similarity = SequenceMatcher(None, query_lower, nome).ratio()
            score += similarity * 5
            
            # Bonus se o nome é mais longo (mais específico)
            score += len(nome) / 100
            
            if score > 0:
                candidatos.append((codigo, plant['nome'], score))
        
        if candidatos:
            # Ordenar candidatos por score (maior primeiro)
            candidatos.sort(key=lambda x: x[2], reverse=True)
            melhor_codigo, melhor_nome, melhor_score = candidatos[0]
            debug_print(f"[THERMAL_MATCHER] ✅ Código {melhor_codigo} encontrado (fallback): '{melhor_nome}' (score: {melhor_score:.2f})")
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
        
        # ETAPA 1: Preparar lista de plantas
        plants_list = self._prepare_plants_list(available_plants)
        
        if not plants_list:
            debug_print("[THERMAL_MATCHER] ⚠️ Nenhuma planta disponível para matching")
            return None
        
        # Obter lista de códigos válidos
        valid_codes = [p['codigo'] for p in plants_list]
        
        debug_print(f"[THERMAL_MATCHER] Iniciando matching para query: '{query[:50]}...'")
        debug_print(f"[THERMAL_MATCHER] Tipo de entidade: {entity_type}")
        debug_print(f"[THERMAL_MATCHER] Plantas disponíveis: {len(plants_list)}")
        
        # ETAPA 2: Expandir abreviações
        expanded_query = self._expand_abbreviations(query)
        
        # ETAPA 3: Tentar extrair código numérico
        codigo = self._extract_numeric_code(expanded_query, valid_codes, entity_type)
        if codigo is not None:
            return codigo
        
        # Também tentar na query original (caso a expansão tenha alterado algo)
        if expanded_query != query.lower():
            codigo = self._extract_numeric_code(query, valid_codes, entity_type)
            if codigo is not None:
                return codigo
        
        # ETAPA 4: Tentar match por nome
        codigo = self._extract_by_name(expanded_query, plants_list, threshold)
        if codigo is not None:
            return codigo
        
        # Também tentar na query original
        if expanded_query != query.lower():
            codigo = self._extract_by_name(query.lower(), plants_list, threshold)
            if codigo is not None:
                return codigo
        
        debug_print(f"[THERMAL_MATCHER] ⚠️ Nenhuma {entity_type} específica detectada na query")
        return None


# Instância global para uso conveniente
_default_matcher: Optional[ThermalPlantMatcher] = None


def get_thermal_plant_matcher() -> ThermalPlantMatcher:
    """
    Obtém a instância global do ThermalPlantMatcher.
    
    Cria uma nova instância na primeira chamada (lazy initialization).
    
    Returns:
        Instância do ThermalPlantMatcher
    """
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = ThermalPlantMatcher()
    return _default_matcher

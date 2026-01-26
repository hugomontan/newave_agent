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
        abbrev_to_full: Mapeamento nome_arquivo.lower() -> nome_completo.lower()
        full_to_abbrev: Mapeamento nome_completo.lower() -> nome_arquivo.lower()
        code_to_names: Mapeamento codigo -> (nome_arquivo, nome_completo)
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
        self.code_to_names: Dict[int, Tuple[str, str]] = {}  # codigo -> (nome_arquivo, nome_completo)
        
        self._load_name_mapping_from_csv()
    
    def _load_name_mapping_from_csv(self) -> None:
        """
        Carrega os mapeamentos bidirecionais do CSV de de-para.
        
        O CSV deve ter as colunas:
        - codigo: Código numérico da usina (prevalece no deck)
        - nome_arquivo: Nome como aparece no arquivo NEWAVE
        - nome_completo ou usina: Nome expandido/curado manualmente
        
        Cria três dicionários:
        - abbrev_to_full: nome_arquivo.lower() -> nome_completo.lower()
        - full_to_abbrev: nome_completo.lower() -> nome_arquivo.lower()
        - code_to_names: codigo -> (nome_arquivo, nome_completo)
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
                        # Tratar coluna "Nome completo " (com espaço extra) ou "usina "
                        nome_completo = str(row.get('Nome completo ', row.get('Nome completo', row.get('nome_completo', '')))).strip()
                        # Fallback para coluna 'usina' se nome_completo não existir
                        if not nome_completo:
                            nome_completo = str(row.get('usina ', row.get('usina', ''))).strip()
                        
                        if not nome_arquivo:
                            continue
                        
                        # Se não tiver nome_completo, usar nome_arquivo
                        if not nome_completo:
                            nome_completo = nome_arquivo
                        
                        # Normalizar para lowercase
                        nome_arquivo_lower = nome_arquivo.lower()
                        nome_completo_lower = nome_completo.lower()
                        
                        # Só criar mapeamento se forem diferentes
                        if nome_arquivo_lower != nome_completo_lower:
                            self.abbrev_to_full[nome_arquivo_lower] = nome_completo_lower
                            self.full_to_abbrev[nome_completo_lower] = nome_arquivo_lower
                        
                        # Sempre criar mapeamento por código
                        self.code_to_names[codigo] = (nome_arquivo, nome_completo)
                        
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
    
    def _create_expanded_list_from_csv(self) -> Tuple[List[str], Dict[str, int]]:
        """
        Cria lista expandida de nomes DIRETAMENTE do CSV.
        
        O CSV é a fonte de verdade. Cria lista incluindo tanto nome_arquivo
        quanto nome_completo de cada entrada do CSV.
        
        Returns:
            Tupla (available_names, name_to_codigo) onde:
            - available_names: Lista de nomes (nome_arquivo + nome_completo)
            - name_to_codigo: Mapeamento nome.lower() -> codigo (do CSV)
        """
        available_names = []
        name_to_codigo = {}  # Mapeamento nome -> codigo (do CSV)
        
        debug_print(f"[THERMAL_MATCHER] Criando lista expandida de nomes do CSV...")
        for codigo, (nome_arquivo, nome_completo) in self.code_to_names.items():
            # Adicionar nome_arquivo (nome do deck)
            if nome_arquivo and nome_arquivo.strip():
                available_names.append(nome_arquivo)
                name_to_codigo[nome_arquivo.lower()] = codigo
                debug_print(f"[THERMAL_MATCHER]   Código {codigo}: nome_arquivo='{nome_arquivo}'")
            
            # Adicionar nome_completo (se diferente do nome_arquivo)
            if nome_completo and nome_completo.strip():
                nome_completo_lower = nome_completo.lower()
                nome_arquivo_lower = nome_arquivo.lower() if nome_arquivo else ''
                if nome_completo_lower != nome_arquivo_lower:
                    available_names.append(nome_completo)
                    name_to_codigo[nome_completo_lower] = codigo
                    debug_print(f"[THERMAL_MATCHER]   Código {codigo}: nome_completo='{nome_completo}'")
        
        debug_print(f"[THERMAL_MATCHER] Lista expandida criada: {len(available_names)} nomes únicos do CSV")
        return available_names, name_to_codigo
    
    def _extract_by_name(
        self, 
        query: str, 
        threshold: float = 0.5
    ) -> Optional[int]:
        """
        Extrai código da usina por matching de nome usando CSV como fonte primária.
        
        CRÍTICO: Faz matching DIRETAMENTE no CSV (fonte de verdade).
        Cria lista expandida incluindo tanto nome_arquivo quanto nome_completo do CSV.
        
        Utiliza o matcher centralizado (find_usina_match) e fallback
        com palavras-chave e similaridade.
        
        Args:
            query: Query do usuário (já com abreviações expandidas)
            threshold: Score mínimo para fuzzy matching
            
        Returns:
            Código da usina/classe (do CSV) ou None se não encontrado
        """
        query_lower = query.lower()
        
        # Importar matcher centralizado
        from backend.core.utils.usina_name_matcher import find_usina_match
        
        # Criar lista expandida DIRETAMENTE do CSV (fonte de verdade)
        available_names, name_to_codigo = self._create_expanded_list_from_csv()
        
        if not available_names:
            debug_print(f"[THERMAL_MATCHER] ⚠️ Nenhum nome disponível no CSV para matching")
            return None
        
        # ETAPA 1: Match exato (tanto nome_arquivo quanto nome_completo do CSV)
        # Ordenar por tamanho (maior primeiro) para priorizar matches mais específicos
        csv_entries = []
        for codigo, (nome_arquivo, nome_completo) in self.code_to_names.items():
            csv_entries.append({
                'codigo': codigo,
                'nome_arquivo': nome_arquivo,
                'nome_completo': nome_completo
            })
        sorted_entries = sorted(csv_entries, key=lambda x: len(x['nome_arquivo']), reverse=True)
        
        for entry in sorted_entries:
            codigo = entry['codigo']
            nome_arquivo = entry['nome_arquivo']
            nome_completo = entry['nome_completo']
            
            # Match exato contra nome_arquivo do CSV
            if nome_arquivo and nome_arquivo.lower().strip() == query_lower.strip():
                debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por match exato (nome_arquivo CSV): '{nome_arquivo}'")
                return codigo
            
            # Match exato contra nome_completo do CSV
            if nome_completo and nome_completo.lower().strip() == query_lower.strip():
                debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por match exato (nome_completo CSV): '{nome_completo}'")
                return codigo
            
            # Match exato do nome dentro da query (com word boundaries)
            if nome_arquivo and len(nome_arquivo.lower()) >= 4:
                pattern = r'\b' + re.escape(nome_arquivo.lower()) + r'\b'
                if re.search(pattern, query_lower):
                    debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por nome_arquivo '{nome_arquivo}' na query")
                    return codigo
            
            if nome_completo and len(nome_completo.lower()) >= 4:
                pattern = r'\b' + re.escape(nome_completo.lower()) + r'\b'
                if re.search(pattern, query_lower):
                    debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por nome_completo '{nome_completo}' na query")
                    return codigo
        
        # ETAPA 2: Fuzzy matching contra lista expandida do CSV
        match_result = find_usina_match(query, available_names, threshold=threshold)
        if match_result:
            matched_name, score = match_result
            matched_lower = matched_name.lower()
            if matched_lower in name_to_codigo:
                codigo = name_to_codigo[matched_lower]
                debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado via matcher centralizado: '{matched_name}' (score: {score:.2f})")
                return codigo
        
        # ETAPA 3: Fallback com palavras-chave (usando CSV)
        debug_print(f"[THERMAL_MATCHER] ETAPA 3: Tentando fallback keyword matching no CSV...")
        return self._fallback_keyword_matching_csv(query_lower)
    
    def _fallback_keyword_matching_csv(self, query_lower: str) -> Optional[int]:
        """
        Fallback inteligente usando palavras-chave e similaridade no CSV.
        
        Busca tanto em nome_arquivo quanto em nome_completo do CSV.
        
        Usado quando o matcher centralizado não encontra resultado.
        
        Args:
            query_lower: Query em lowercase
            
        Returns:
            Código da usina/classe (do CSV) ou None
        """
        # Extrair palavras significativas da query
        palavras_query = [
            p for p in query_lower.split() 
            if len(p) > 2 and p not in self.STOPWORDS
        ]
        
        if not palavras_query:
            return None
        
        candidatos = []
        
        # Buscar no CSV diretamente
        for codigo, (nome_arquivo, nome_completo) in self.code_to_names.items():
            # Testar tanto nome_arquivo quanto nome_completo
            for nome in [nome_arquivo, nome_completo]:
                if not nome:
                    continue
                
                nome_lower = nome.lower().strip()
                
                # Extrair palavras significativas do nome
                palavras_nome = [
                    p for p in nome_lower.split() 
                    if len(p) > 2 and p not in self.STOPWORDS
                ]
                
                # Calcular score: quantas palavras da query estão no nome
                palavras_comuns = set(palavras_query) & set(palavras_nome)
                score = len(palavras_comuns)
                
                # Bonus se todas as palavras significativas da query estão no nome
                if palavras_query and all(p in palavras_nome for p in palavras_query):
                    score += 10  # Bonus grande para match completo
                
                # Bonus por similaridade de strings
                similarity = SequenceMatcher(None, query_lower, nome_lower).ratio()
                score += similarity * 5
                
                # Bonus se o nome é mais longo (mais específico)
                score += len(nome_lower) / 100
                
                if score > 0:
                    candidatos.append((codigo, nome, score))
        
        if candidatos:
            # Ordenar candidatos por score (maior primeiro)
            candidatos.sort(key=lambda x: x[2], reverse=True)
            melhor_codigo, melhor_nome, melhor_score = candidatos[0]
            debug_print(f"[THERMAL_MATCHER] ✅ Código {melhor_codigo} encontrado (fallback CSV): '{melhor_nome}' (score: {melhor_score:.2f})")
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
        
        # Obter lista de códigos válidos do CSV (fonte de verdade)
        valid_codes_csv = list(self.code_to_names.keys())
        
        debug_print(f"[THERMAL_MATCHER] Iniciando matching para query: '{query[:50]}...'")
        debug_print(f"[THERMAL_MATCHER] Tipo de entidade: {entity_type}")
        debug_print(f"[THERMAL_MATCHER] Plantas no DataFrame: {len(plants_list)}")
        debug_print(f"[THERMAL_MATCHER] Códigos no CSV: {len(valid_codes_csv)}")
        
        # ETAPA 2: Expandir abreviações
        expanded_query = self._expand_abbreviations(query)
        
        # ETAPA 3: Tentar extrair código numérico (validar contra CSV)
        codigo = self._extract_numeric_code(expanded_query, valid_codes_csv, entity_type)
        if codigo is not None:
            debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por padrão numérico (CSV)")
            return codigo
        
        # Também tentar na query original (caso a expansão tenha alterado algo)
        if expanded_query != query.lower():
            codigo = self._extract_numeric_code(query, valid_codes_csv, entity_type)
            if codigo is not None:
                debug_print(f"[THERMAL_MATCHER] ✅ Código {codigo} encontrado por padrão numérico (CSV)")
                return codigo
        
        # ETAPA 4: Tentar match por nome (usando CSV diretamente)
        codigo = self._extract_by_name(expanded_query, threshold)
        if codigo is not None:
            return codigo
        
        # Também tentar na query original
        if expanded_query != query.lower():
            codigo = self._extract_by_name(query.lower(), threshold)
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

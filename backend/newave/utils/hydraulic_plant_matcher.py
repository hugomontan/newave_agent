"""
Serviço unificado de matching de usinas hidrelétricas para NEWAVE.

Centraliza a lógica de identificação de usinas hidrelétricas,
utilizando de-para via CSV para expandir abreviações e fazer matching
tanto por nome oficial (nome_arquivo) quanto por nome decomposto (Nome completo).
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
    "deparahidro.csv"
)


class HydraulicPlantMatcher:
    """
    Serviço unificado de matching de usinas hidrelétricas.
    
    Utiliza um CSV de de-para para expandir abreviações dos nomes das usinas
    e fazer matching tanto por nome oficial (nome_arquivo) quanto por
    nome decomposto (Nome completo curado).
    
    Attributes:
        abbrev_to_full: Mapeamento nome_arquivo.lower() -> Nome completo.lower() (curado)
        full_to_abbrev: Mapeamento Nome completo.lower() -> nome_arquivo.lower()
        code_to_names: Mapeamento codigo -> (nome_arquivo, nome_completo, posto)
    """
    
    # Palavras comuns a ignorar no matching
    STOPWORDS = {
        'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os',
        'em', 'na', 'no', 'nas', 'nos', 'para', 'por', 'com', 'sem',
        'à', 'ao', 'aos', 'informacoes', 'informações', 'dados',
        'usina', 'hidrelétrica', 'hidreletrica', 'cadastro',
        'configuração', 'configuracao', 'confhd', 'modificação',
        'modificacao', 'vazão', 'vazao', 'posto', 'postos'
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
        self.code_to_names: Dict[int, Tuple[str, str, Optional[int]]] = {}
        
        self._load_name_mapping_from_csv()
    
    def _load_name_mapping_from_csv(self) -> None:
        """
        Carrega os mapeamentos bidirecionais do CSV de de-para.
        
        O CSV deve ter as colunas:
        - codigo: Código numérico da usina
        - nome_arquivo: Nome como aparece no arquivo NEWAVE
        - Nome completo : Nome expandido/curado manualmente (com espaço extra)
        - posto: Posto de vazões associado
        
        Cria três dicionários:
        - abbrev_to_full: nome_arquivo.lower() -> Nome completo.lower()
        - full_to_abbrev: Nome completo.lower() -> nome_arquivo.lower()
        - code_to_names: codigo -> (nome_arquivo, nome_completo, posto)
        """
        if not os.path.exists(self.csv_path):
            debug_print(f"[HYDRAULIC_MATCHER] ⚠️ CSV de de-para não encontrado: {self.csv_path}")
            debug_print("[HYDRAULIC_MATCHER] ⚠️ Matching funcionará sem expansão de abreviações")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        codigo = int(row.get('codigo', 0))
                        nome_arquivo = str(row.get('nome_arquivo', '')).strip()
                        # Tratar coluna "Nome completo " (com espaço extra)
                        nome_completo = str(row.get('Nome completo ', row.get('Nome completo', row.get('nome_completo', '')))).strip()
                        posto_str = row.get('posto', '').strip()
                        posto = int(posto_str) if posto_str and posto_str.isdigit() else None
                        
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
                        self.code_to_names[codigo] = (nome_arquivo, nome_completo, posto)
                        
                    except (ValueError, KeyError) as e:
                        debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Erro ao processar linha do CSV: {e}")
                        continue
            
            debug_print(f"[HYDRAULIC_MATCHER] ✅ CSV carregado: {len(self.abbrev_to_full)} mapeamentos de abreviações")
            debug_print(f"[HYDRAULIC_MATCHER] ✅ Total de usinas mapeadas: {len(self.code_to_names)}")
            
        except Exception as e:
            debug_print(f"[HYDRAULIC_MATCHER] ❌ Erro ao carregar CSV: {e}")
    
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
                    debug_print(f"[HYDRAULIC_MATCHER] ✅ Abreviação expandida: '{abbrev}' -> '{full_name}'")
        
        if expanded != query_lower:
            debug_print(f"[HYDRAULIC_MATCHER] Query expandida: '{query_lower}' -> '{expanded}'")
        
        return expanded
    
    def _create_expanded_list_from_csv(self) -> Tuple[List[str], Dict[str, int]]:
        """
        Cria lista expandida de nomes DIRETAMENTE do CSV.
        
        O CSV é a fonte de verdade. Cria lista incluindo tanto nome_arquivo
        quanto Nome completo de cada entrada do CSV.
        
        Returns:
            Tupla (available_names, name_to_codigo) onde:
            - available_names: Lista de nomes (nome_arquivo + nome_completo)
            - name_to_codigo: Mapeamento nome.lower() -> codigo (do CSV)
        """
        available_names = []
        name_to_codigo = {}  # Mapeamento nome -> codigo (do CSV)
        
        safe_print(f"[HYDRAULIC_MATCHER] Criando lista expandida de nomes do CSV...")
        for codigo, (nome_arquivo, nome_completo, _) in self.code_to_names.items():
            # Adicionar nome_arquivo (nome do deck)
            if nome_arquivo and nome_arquivo.strip():
                available_names.append(nome_arquivo)
                name_to_codigo[nome_arquivo.lower()] = codigo
                safe_print(f"[HYDRAULIC_MATCHER]   Código {codigo}: nome_arquivo='{nome_arquivo}'")
            
            # Adicionar nome_completo (se diferente do nome_arquivo)
            if nome_completo and nome_completo.strip():
                nome_completo_lower = nome_completo.lower()
                nome_arquivo_lower = nome_arquivo.lower() if nome_arquivo else ''
                if nome_completo_lower != nome_arquivo_lower:
                    available_names.append(nome_completo)
                    name_to_codigo[nome_completo_lower] = codigo
                    safe_print(f"[HYDRAULIC_MATCHER]   Código {codigo}: nome_completo='{nome_completo}'")
        
        safe_print(f"[HYDRAULIC_MATCHER] Lista expandida criada: {len(available_names)} nomes únicos do CSV")
        return available_names, name_to_codigo
    
    def _find_plant_in_dataframe_by_name(
        self,
        nome_arquivo: str,
        plants_list: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Busca planta no DataFrame pelo nome (nome_arquivo do CSV).
        
        CRÍTICO: Não usar código para buscar no DataFrame, pois os códigos
        podem estar desalinhados. O CSV é a fonte de verdade para o código,
        mas devemos buscar no DataFrame pelo NOME.
        
        Usado após encontrar código no CSV para obter dados do DataFrame
        (idx, posto, etc.) usando o nome_arquivo do CSV.
        
        Args:
            nome_arquivo: Nome da usina como aparece no deck (do CSV)
            plants_list: Lista de plantas do DataFrame
            
        Returns:
            Dict da planta encontrada ou None
        """
        nome_arquivo_upper = nome_arquivo.upper().strip()
        for plant in plants_list:
            nome_usina = str(plant.get('nome', '')).upper().strip()
            if nome_usina == nome_arquivo_upper:
                return plant
        return None
    
    def _prepare_plants_list(
        self, 
        plants_data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[int, str]]
    ) -> List[Dict[str, Any]]:
        """
        Normaliza dados de entrada para formato padronizado.
        
        Aceita diferentes formatos de entrada e retorna lista padronizada:
        [{'codigo': int, 'nome': str, 'idx': Optional[int], 'posto': Optional[int]}, ...]
        
        IMPORTANTE: Não enriquece com dados do CSV. Apenas normaliza os dados do DataFrame.
        O matching será feito DIRETAMENTE no CSV.
        
        Args:
            plants_data: Dados das plantas em diferentes formatos:
                - DataFrame com colunas 'codigo_usina' e 'nome_usina' (pode ter índice preservado)
                - Lista de dicts com 'codigo_usina' e 'nome_usina'
                - Dict mapeando codigo -> nome
                
        Returns:
            Lista de dicts no formato padronizado (sem enriquecimento)
        """
        result = []
        
        if isinstance(plants_data, pd.DataFrame):
            # DataFrame: iterar sobre linhas preservando índice
            for idx, row in plants_data.iterrows():
                codigo = row.get('codigo_usina')
                nome = str(row.get('nome_usina', '')).strip()
                posto = row.get('posto')
                
                if codigo is not None and nome:
                    plant_dict = {
                        'codigo': int(codigo),
                        'nome': nome,
                        'idx': idx if isinstance(idx, int) else None,
                        'posto': int(posto) if posto is not None and str(posto).isdigit() else None
                    }
                    result.append(plant_dict)
        
        elif isinstance(plants_data, list):
            # Lista de dicts
            for item in plants_data:
                codigo = item.get('codigo_usina', item.get('codigo'))
                nome = str(item.get('nome_usina', item.get('nome', ''))).strip()
                idx = item.get('idx', item.get('idx_real'))
                posto = item.get('posto')
                
                if codigo is not None and nome:
                    plant_dict = {
                        'codigo': int(codigo),
                        'nome': nome,
                        'idx': int(idx) if idx is not None else None,
                        'posto': int(posto) if posto is not None and str(posto).isdigit() else None
                    }
                    result.append(plant_dict)
        
        elif isinstance(plants_data, dict):
            # Dict mapeando codigo -> nome
            for codigo, nome in plants_data.items():
                if codigo is not None and nome:
                    plant_dict = {
                        'codigo': int(codigo),
                        'nome': str(nome).strip(),
                        'idx': None,
                        'posto': None
                    }
                    result.append(plant_dict)
        
        return result
    
    def _extract_numeric_code(
        self, 
        query: str, 
        valid_codes: List[int]
    ) -> Optional[int]:
        """
        Extrai código numérico da query usando padrões regex.
        
        Args:
            query: Query do usuário
            valid_codes: Lista de códigos válidos para validação
            
        Returns:
            Código da usina ou None se não encontrado
        """
        query_lower = query.lower()
        
        # Padrões para usinas hidrelétricas
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*hidrelétrica\s*(\d+)',
            r'usina\s*hidreletrica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
            r'hidrelétrica\s*(\d+)',
            r'hidreletrica\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if codigo in valid_codes:
                        debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo
                except ValueError:
                    continue
        
        return None
    
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
            Código da usina (do CSV) ou None se não encontrado
        """
        query_lower = query.lower()
        
        # Importar matcher centralizado
        from backend.core.utils.usina_name_matcher import find_usina_match
        
        # Criar lista expandida DIRETAMENTE do CSV (fonte de verdade)
        available_names, name_to_codigo = self._create_expanded_list_from_csv()
        
        if not available_names:
            safe_print(f"[HYDRAULIC_MATCHER] ⚠️ Nenhum nome disponível no CSV para matching")
            return None
        
        # ETAPA 1: Match exato (tanto nome_arquivo quanto nome_completo do CSV)
        debug_print(f"[HYDRAULIC_MATCHER] ETAPA 1: Tentando match exato e por word boundaries...")
        debug_print(f"[HYDRAULIC_MATCHER]   Query (lowercase): '{query_lower}'")
        # Ordenar por tamanho (maior primeiro) para priorizar matches mais específicos
        csv_entries = []
        for codigo, (nome_arquivo, nome_completo, _) in self.code_to_names.items():
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
                debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por match exato (nome_arquivo CSV): '{nome_arquivo}'")
                return codigo
            
            # Match exato contra nome_completo do CSV
            if nome_completo and nome_completo.lower().strip() == query_lower.strip():
                debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por match exato (nome_completo CSV): '{nome_completo}'")
                return codigo
            
            # Match do nome dentro da query (com word boundaries)
            # Para nomes com múltiplas palavras, verificar se todas as palavras estão presentes
            if nome_arquivo and len(nome_arquivo.lower().strip()) >= 4:
                nome_arquivo_lower = nome_arquivo.lower().strip()
                # Verificar se todas as palavras do nome estão na query
                palavras_nome = nome_arquivo_lower.split()
                if len(palavras_nome) == 1:
                    # Nome de uma palavra: usar word boundary
                    pattern = r'\b' + re.escape(nome_arquivo_lower) + r'\b'
                    if re.search(pattern, query_lower):
                        debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por nome_arquivo '{nome_arquivo}' na query (word boundary)")
                        return codigo
                else:
                    # Nome com múltiplas palavras: verificar se todas estão presentes
                    todas_palavras_presentes = all(
                        re.search(r'\b' + re.escape(palavra) + r'\b', query_lower) 
                        for palavra in palavras_nome if len(palavra) > 2
                    )
                    if todas_palavras_presentes:
                        debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por nome_arquivo '{nome_arquivo}' na query (todas palavras presentes)")
                        return codigo
            
            if nome_completo and len(nome_completo.lower().strip()) >= 4:
                nome_completo_lower = nome_completo.lower().strip()
                # Verificar se todas as palavras do nome estão na query
                palavras_nome = nome_completo_lower.split()
                if len(palavras_nome) == 1:
                    # Nome de uma palavra: usar word boundary
                    pattern = r'\b' + re.escape(nome_completo_lower) + r'\b'
                    if re.search(pattern, query_lower):
                        debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por nome_completo '{nome_completo}' na query (word boundary)")
                        return codigo
                else:
                    # Nome com múltiplas palavras: verificar se todas estão presentes
                    todas_palavras_presentes = all(
                        re.search(r'\b' + re.escape(palavra) + r'\b', query_lower) 
                        for palavra in palavras_nome if len(palavra) > 2
                    )
                    if todas_palavras_presentes:
                        debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por nome_completo '{nome_completo}' na query (todas palavras presentes)")
                        return codigo
        
        # ETAPA 2: Fuzzy matching contra lista expandida do CSV
        debug_print(f"[HYDRAULIC_MATCHER] ETAPA 2: Tentando fuzzy matching com matcher centralizado...")
        match_result = find_usina_match(query, available_names, threshold=threshold)
        if match_result:
            matched_name, score = match_result
            matched_lower = matched_name.lower()
            if matched_lower in name_to_codigo:
                codigo = name_to_codigo[matched_lower]
                debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado via matcher centralizado: '{matched_name}' (score: {score:.2f})")
                return codigo
            else:
                debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Nome '{matched_name}' encontrado mas não está no mapeamento name_to_codigo")
        else:
            debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Matcher centralizado não encontrou match acima do threshold {threshold}")
        
        # ETAPA 3: Fallback com palavras-chave (usando CSV)
        debug_print(f"[HYDRAULIC_MATCHER] ETAPA 3: Tentando fallback keyword matching no CSV...")
        return self._fallback_keyword_matching_csv(query_lower)
    
    def _fallback_keyword_matching_csv(self, query_lower: str) -> Optional[int]:
        """
        Fallback inteligente usando palavras-chave e similaridade no CSV.
        
        Busca tanto em nome_arquivo quanto em nome_completo do CSV.
        
        Usado quando o matcher centralizado não encontra resultado.
        
        Args:
            query_lower: Query em lowercase
            
        Returns:
            Código da usina (do CSV) ou None
        """
        # Extrair palavras significativas da query
        palavras_query = [
            p for p in query_lower.split() 
            if len(p) > 2 and p not in self.STOPWORDS
        ]
        
        safe_print(f"[HYDRAULIC_MATCHER] Palavras significativas da query: {palavras_query}")
        
        if not palavras_query:
            safe_print(f"[HYDRAULIC_MATCHER] Nenhuma palavra significativa encontrada na query")
            return None
        
        candidatos = []
        
        # Buscar no CSV diretamente
        for codigo, (nome_arquivo, nome_completo, _) in self.code_to_names.items():
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
            safe_print(f"[HYDRAULIC_MATCHER] Top 5 candidatos (fallback CSV):")
            for idx, (cod, nome, score) in enumerate(candidatos[:5], 1):
                safe_print(f"[HYDRAULIC_MATCHER]   {idx}. Código {cod}: '{nome}' (score: {score:.2f})")
            
            melhor_codigo, melhor_nome, melhor_score = candidatos[0]
            safe_print(f"[HYDRAULIC_MATCHER] ✅ Código {melhor_codigo} encontrado (fallback CSV): '{melhor_nome}' (score: {melhor_score:.2f})")
            return melhor_codigo
        
        safe_print(f"[HYDRAULIC_MATCHER] Nenhum candidato encontrado no fallback")
        return None
    
    def extract_plant_from_query(
        self,
        query: str,
        available_plants: Union[pd.DataFrame, List[Dict[str, Any]], Dict[int, str]],
        return_format: str = "codigo",  # "codigo" | "tupla" | "posto"
        threshold: float = 0.5
    ) -> Optional[Union[int, Tuple[int, int], Tuple[int, str]]]:
        """
        Método principal para extrair código de usina da query.
        
        Suporta diferentes formatos de retorno:
        - "codigo": Retorna apenas int (código da usina)
        - "tupla": Retorna Tuple[int, int] (código, idx_real)
        - "posto": Retorna Tuple[int, str] (posto, nome_usina)
        
        Fluxo:
        1. Preparar lista de plantas (enriquecida com nome_completo)
        2. Expandir abreviações via de-para
        3. Tentar extrair código numérico
        4. Tentar match por nome (exato, fuzzy, fallback) contra lista expandida
        
        Args:
            query: Query do usuário
            available_plants: Dados das plantas disponíveis (DataFrame, list, ou dict)
            return_format: Formato de retorno desejado ("codigo", "tupla", "posto")
            threshold: Score mínimo para fuzzy matching (0.0 a 1.0)
            
        Returns:
            Código da usina, tupla (código, idx_real), tupla (posto, nome) ou None
        """
        if not query:
            return None
        
        # ETAPA 1: Preparar lista de plantas (enriquecida com nome_completo)
        plants_list = self._prepare_plants_list(available_plants)
        
        if not plants_list:
            debug_print("[HYDRAULIC_MATCHER] ⚠️ Nenhuma planta disponível para matching")
            return None
        
        # Obter lista de códigos válidos do CSV (fonte de verdade)
        valid_codes_csv = list(self.code_to_names.keys())
        
        # Obter lista de códigos do DataFrame (para validação)
        valid_codes_df = [p['codigo'] for p in plants_list] if plants_list else []
        
        safe_print(f"[HYDRAULIC_MATCHER] ===== INÍCIO: Matching de Usina Hidrelétrica =====")
        safe_print(f"[HYDRAULIC_MATCHER] Query original: '{query}'")
        safe_print(f"[HYDRAULIC_MATCHER] Formato de retorno: {return_format}")
        safe_print(f"[HYDRAULIC_MATCHER] Threshold: {threshold}")
        safe_print(f"[HYDRAULIC_MATCHER] Plantas no DataFrame: {len(plants_list)}")
        safe_print(f"[HYDRAULIC_MATCHER] Códigos no CSV: {len(valid_codes_csv)}")
        safe_print(f"[HYDRAULIC_MATCHER] Códigos no DataFrame: {len(valid_codes_df)}")
        
        # ETAPA 2: Expandir abreviações
        expanded_query = self._expand_abbreviations(query)
        if expanded_query != query.lower():
            safe_print(f"[HYDRAULIC_MATCHER] Query expandida: '{query.lower()}' -> '{expanded_query}'")
        else:
            safe_print(f"[HYDRAULIC_MATCHER] Query não foi expandida (sem abreviações detectadas)")
        
        # ETAPA 3: Tentar extrair código numérico (validar contra CSV)
        debug_print(f"[HYDRAULIC_MATCHER] ETAPA 3: Tentando extrair código numérico...")
        codigo = self._extract_numeric_code(expanded_query, valid_codes_csv)
        if codigo is None and expanded_query != query.lower():
            debug_print(f"[HYDRAULIC_MATCHER] Tentando extrair código da query original...")
            codigo = self._extract_numeric_code(query, valid_codes_csv)
        
        if codigo is not None:
            debug_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado por padrão numérico (CSV)")
            # Obter nome_arquivo do CSV para buscar no DataFrame
            if codigo in self.code_to_names:
                nome_arquivo_csv, _, _ = self.code_to_names[codigo]
                debug_print(f"[HYDRAULIC_MATCHER]   Buscando no DataFrame pelo nome: '{nome_arquivo_csv}'")
                # Buscar no DataFrame usando NOME do CSV (não código!)
                plant = self._find_plant_in_dataframe_by_name(nome_arquivo_csv, plants_list)
                if plant:
                    result = self._format_return(plant, return_format)
                    debug_print(f"[HYDRAULIC_MATCHER] ===== FIM: Matching concluído (código numérico) =====")
                    return result
                else:
                    debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Código {codigo} (nome '{nome_arquivo_csv}') encontrado no CSV mas não no DataFrame")
            else:
                debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Código {codigo} não encontrado no code_to_names")
        else:
            debug_print(f"[HYDRAULIC_MATCHER] Nenhum código numérico encontrado")
        
        # ETAPA 4: Tentar match por nome (usando CSV diretamente)
        debug_print(f"[HYDRAULIC_MATCHER] ETAPA 4: Tentando match por nome no CSV...")
        codigo = self._extract_by_name(expanded_query, threshold)
        if codigo is None and expanded_query != query.lower():
            debug_print(f"[HYDRAULIC_MATCHER] Tentando match por nome na query original...")
            codigo = self._extract_by_name(query.lower(), threshold)
        
        if codigo is not None:
            safe_print(f"[HYDRAULIC_MATCHER] ✅ Código {codigo} encontrado no CSV pelo matching")
            # Buscar informações do CSV para debug
            if codigo in self.code_to_names:
                nome_arquivo_csv, nome_completo_csv, _ = self.code_to_names[codigo]
                safe_print(f"[HYDRAULIC_MATCHER]   CSV: código={codigo}, nome_arquivo='{nome_arquivo_csv}', nome_completo='{nome_completo_csv}'")
                
                # Buscar no DataFrame usando NOME do CSV (não código!)
                debug_print(f"[HYDRAULIC_MATCHER]   Buscando no DataFrame pelo nome: '{nome_arquivo_csv}'")
                plant = self._find_plant_in_dataframe_by_name(nome_arquivo_csv, plants_list)
                if plant:
                    safe_print(f"[HYDRAULIC_MATCHER]   DataFrame: código={plant.get('codigo')}, nome='{plant.get('nome')}', idx={plant.get('idx')}, posto={plant.get('posto')}")
                    result = self._format_return(plant, return_format)
                    safe_print(f"[HYDRAULIC_MATCHER] ===== FIM: Matching concluído (match por nome) - Retornando código {codigo} =====")
                    return result
                else:
                    debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Código {codigo} (nome '{nome_arquivo_csv}') encontrado no CSV mas não no DataFrame")
                    # Fallback: retornar baseado no formato mesmo sem encontrar no DataFrame
                    if return_format == "codigo":
                        safe_print(f"[HYDRAULIC_MATCHER] ===== FIM: Matching concluído (código do CSV) - Retornando código {codigo} =====")
                        return codigo
                    elif return_format == "tupla":
                        # Para tupla, usar código como idx_real quando não encontra no DataFrame
                        debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Usando código {codigo} como idx_real (fallback)")
                        safe_print(f"[HYDRAULIC_MATCHER] ===== FIM: Matching concluído (código do CSV) - Retornando tupla ({codigo}, {codigo}) =====")
                        return (codigo, codigo)
                    elif return_format == "posto":
                        # Para posto, não podemos retornar sem dados do DataFrame
                        debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Formato 'posto' requer dados do DataFrame, mas usina não encontrada")
                        return None
            else:
                debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Código {codigo} não encontrado no code_to_names")
        
        safe_print(f"[HYDRAULIC_MATCHER] ⚠️ Nenhuma usina específica detectada na query")
        safe_print(f"[HYDRAULIC_MATCHER]   Query testada: '{query}'")
        safe_print(f"[HYDRAULIC_MATCHER]   Query expandida testada: '{expanded_query}'")
        safe_print(f"[HYDRAULIC_MATCHER] ===== FIM: Matching concluído (sem resultado) =====")
        return None
    
    def _format_return(
        self,
        plant: Dict[str, Any],
        return_format: str
    ) -> Union[int, Tuple[int, int], Tuple[int, str]]:
        """
        Formata o retorno baseado no formato solicitado.
        
        Args:
            plant: Dict da planta encontrada
            return_format: "codigo", "tupla", ou "posto"
            
        Returns:
            Formato apropriado conforme return_format
        """
        codigo = plant['codigo']
        
        if return_format == "codigo":
            return codigo
        
        elif return_format == "tupla":
            idx_real = plant.get('idx')
            if idx_real is None:
                # Se não tem idx, usar o código como fallback
                debug_print(f"[HYDRAULIC_MATCHER] ⚠️ idx_real não disponível, usando código {codigo}")
                idx_real = codigo
            return (codigo, idx_real)
        
        elif return_format == "posto":
            posto = plant.get('posto')
            nome = plant.get('nome', '')
            if posto is None:
                debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Posto não disponível para usina {codigo}")
                posto = 0
            return (posto, nome)
        
        else:
            debug_print(f"[HYDRAULIC_MATCHER] ⚠️ Formato de retorno desconhecido: {return_format}, retornando código")
            return codigo


# Instância global para uso conveniente
_default_matcher: Optional[HydraulicPlantMatcher] = None


def get_hydraulic_plant_matcher() -> HydraulicPlantMatcher:
    """
    Obtém a instância global do HydraulicPlantMatcher.
    
    Cria uma nova instância na primeira chamada (lazy initialization).
    
    Returns:
        Instância do HydraulicPlantMatcher
    """
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = HydraulicPlantMatcher()
    return _default_matcher

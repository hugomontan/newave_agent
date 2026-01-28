"""
Tool para consultar limites de intercâmbio entre subsistemas.
Acessa o arquivo SISTEMA.DAT, propriedade limites_intercambio.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Sistema
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print

class LimitesIntercambioTool(NEWAVETool):
    """
    Tool para consultar limites de intercâmbio entre subsistemas.
    Acessa o arquivo SISTEMA.DAT, propriedade limites_intercambio.
    """
    
    def get_name(self) -> str:
        return "LimitesIntercambioTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre limites de intercâmbio.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "limite de intercambio",
            "limite de intercâmbio",
            "limites de intercambio",
            "limites de intercâmbio",
            "intercambio entre",
            "intercâmbio entre",
            "intercambio de",
            "intercâmbio de",
            "capacidade de intercambio",
            "capacidade de intercâmbio",
            "limite entre subsistemas",
            "limite entre submercados",
            "intercambio minimo",
            "intercâmbio mínimo",
            "intercambio minimo obrigatorio",
            "intercâmbio mínimo obrigatório",
            "limite maximo de intercambio",
            "limite máximo de intercâmbio",
            "capacidade de interligacao",
            "capacidade de interligação",
            "limite de interligacao",
            "limite de interligação",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _detect_query_direction(self, query: str) -> str:
        """
        Detecta se a query é direcionada (um sentido) ou genérica (ambos os sentidos).
        
        Args:
            query: Query do usuário
            
        Returns:
            "direcionada" se a query especifica direção (ex: "X para Y", "X → Y")
            "generica" se a query é genérica (ex: "entre X e Y")
            None se não foi possível determinar
        """
        query_lower = query.lower()
        
        # Padrões que indicam direção específica
        patterns_direcionados = [
            r'\bpara\b',  # Palavra "para" isolada
            r'→',  # Seta Unicode
            r'->',  # Seta ASCII
            r'de\s+[^para]+\s+para',  # "de X para Y" (X pode ter múltiplas palavras)
            r'do\s+[^para]+\s+para',  # "do X para Y"
            r'da\s+[^para]+\s+para',  # "da X para Y"
        ]
        
        # Padrão que indica query genérica (ambos os sentidos)
        pattern_generico = r'entre\s+[^e]+\s+e\s+[^e]+'
        
        # Verificar se é genérica primeiro
        if re.search(pattern_generico, query_lower):
            # Mas verificar se não tem "para" depois de "entre"
            # Ex: "entre X e Y" = genérica, mas "entre X para Y" = direcionada
            if not any(re.search(pattern, query_lower) for pattern in patterns_direcionados):
                return "generica"
        
        # Verificar se é direcionada
        if any(re.search(pattern, query_lower) for pattern in patterns_direcionados):
            return "direcionada"
        
        return None
    
    def _extract_submercados_from_query(self, query: str, sistema: Sistema) -> tuple:
        """
        Extrai códigos dos submercados de origem e destino da query.
        
        Args:
            query: Query do usuário
            sistema: Objeto Sistema já lido
            
        Returns:
            Tupla (submercado_de, submercado_para, query_direcionada) onde:
            - submercado_de: código do submercado de origem ou None
            - submercado_para: código do submercado de destino ou None
            - query_direcionada: True se query especifica direção, False se é genérica
        """
        query_lower = query.lower()
        
        # Normalizar abreviações de submercado para nomes completos
        # NE = nordeste, SE = sudeste, N = norte, S = sul
        def _normalize_submercado_tokens(text: str) -> str:
            # Usar word boundaries para evitar substituir partes de outras palavras
            replacements = [
                (r"\bse\b", "sudeste"),
                (r"\bsudeste\b", "sudeste"),
                (r"\bne\b", "nordeste"),
                (r"\bnordeste\b", "nordeste"),
                (r"\bn\b", "norte"),
                (r"\bnorte\b", "norte"),
                (r"\bs\b", "sul"),
                (r"\bsul\b", "sul"),
            ]
            normalized = text
            for pattern, repl in replacements:
                normalized = re.sub(pattern, repl, normalized)
            return normalized
        
        # Aplicar normalização na query em minúsculas
        query_lower = _normalize_submercado_tokens(query_lower)
        
        # Detectar tipo de query (direcionada ou genérica)
        query_direction = self._detect_query_direction(query)
        # Se não foi possível determinar, assumir como direcionada (padrão mais comum)
        is_direcionada = query_direction == "direcionada" if query_direction is not None else True
        debug_print(f"[TOOL] Tipo de query detectado: {query_direction} (is_direcionada: {is_direcionada})")
        
        # Obter lista de subsistemas disponíveis
        subsistemas_disponiveis = []
        if sistema.custo_deficit is not None:
            df_custo = sistema.custo_deficit
            subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
            for _, row in subsistemas_unicos.iterrows():
                subsistemas_disponiveis.append({
                    'codigo': int(row.get('codigo_submercado')),
                    'nome': str(row.get('nome_submercado', '')).strip()
                })
        
        # ETAPA 1: Tentar extrair números explícitos
        patterns = [
            r'subsistema\s*(\d+)\s*(?:para|->|→)\s*subsistema\s*(\d+)',
            r'submercado\s*(\d+)\s*(?:para|->|→)\s*submercado\s*(\d+)',
            r'(\d+)\s*(?:para|->|→)\s*(\d+)',
            r'entre\s*subsistema\s*(\d+)\s*e\s*subsistema\s*(\d+)',
            r'entre\s*submercado\s*(\d+)\s*e\s*submercado\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    sub_de = int(match.group(1))
                    sub_para = int(match.group(2))
                    codigos_validos = [s['codigo'] for s in subsistemas_disponiveis]
                    if sub_de in codigos_validos and sub_para in codigos_validos:
                        # Verificar se o padrão indica direção ou é genérico
                        pattern_str = pattern.pattern
                        is_pattern_direcionado = 'para' in pattern_str or '->' in pattern_str or '→' in pattern_str
                        is_pattern_generico = 'entre' in pattern_str and 'e' in pattern_str
                        
                        if is_pattern_generico:
                            is_direcionada = False
                        elif is_pattern_direcionado:
                            is_direcionada = True
                        
                        debug_print(f"[TOOL] ✅ Códigos {sub_de} → {sub_para} encontrados por padrão numérico (direcionada: {is_direcionada})")
                        return (sub_de, sub_para, is_direcionada)
                except (ValueError, IndexError):
                    continue
        
        # ETAPA 2: Buscar por nomes de submercados
        # Ordenar por tamanho do nome (mais específico primeiro)
        subsistemas_ordenados = sorted(subsistemas_disponiveis, key=lambda x: len(x['nome']), reverse=True)
        
        # Função auxiliar para extrair palavras-chave do nome do submercado
        def _extract_keywords(nome_completo: str) -> list:
            """Extrai palavras-chave relevantes do nome do submercado."""
            nome_lower = nome_completo.lower().strip()
            # Palavras a ignorar
            stopwords = {'subsistema', 'submercado', 'sistema', 'de', 'do', 'da', 'dos', 'das'}
            # Extrair palavras que não são stopwords
            palavras = re.findall(r'\b\w+\b', nome_lower)
            keywords = [p for p in palavras if p not in stopwords and len(p) > 2]
            # Se não encontrou keywords, usar o nome completo
            return keywords if keywords else [nome_lower]
        
        # Criar mapeamento de keywords para submercados
        keywords_to_subsistemas = {}
        for subsistema in subsistemas_disponiveis:
            nome_sub = subsistema['nome']
            keywords = _extract_keywords(nome_sub)
            for keyword in keywords:
                if keyword not in keywords_to_subsistemas:
                    keywords_to_subsistemas[keyword] = []
                keywords_to_subsistemas[keyword].append(subsistema)
        
        debug_print(f"[TOOL] Submercados disponíveis: {[(s['codigo'], s['nome']) for s in subsistemas_disponiveis]}")
        debug_print(f"[TOOL] Keywords mapeadas: {list(keywords_to_subsistemas.keys())}")
        
        sub_de = None
        sub_para = None
        
        # Padrão especial: "entre X e Y" (ex: "entre sudeste e norte")
        pattern_entre = re.search(r'entre\s+([^e]+?)\s+e\s+([^e]+?)(?:\s|$|,|\.)', query_lower)
        if pattern_entre:
            nome_1 = pattern_entre.group(1).strip()
            nome_2 = pattern_entre.group(2).strip()
            debug_print(f"[TOOL] Padrão 'entre X e Y' detectado: '{nome_1}' e '{nome_2}'")
            
            # Buscar submercados que correspondem aos nomes (usando keywords)
            for keyword, subsistemas_list in keywords_to_subsistemas.items():
                if re.search(rf'\b{re.escape(keyword)}\b', nome_1):
                    if sub_de is None:
                        sub_de = subsistemas_list[0]['codigo']
                        debug_print(f"[TOOL] ✅ Código {sub_de} encontrado como origem (padrão 'entre X e Y'): '{subsistemas_list[0]['nome']}' (keyword: '{keyword}')")
                        break
            
            for keyword, subsistemas_list in keywords_to_subsistemas.items():
                if re.search(rf'\b{re.escape(keyword)}\b', nome_2):
                    for subsistema in subsistemas_list:
                        if subsistema['codigo'] != sub_de:
                            sub_para = subsistema['codigo']
                            debug_print(f"[TOOL] ✅ Código {sub_para} encontrado como destino (padrão 'entre X e Y'): '{subsistema['nome']}' (keyword: '{keyword}')")
                            break
                    if sub_para is not None:
                        break
            
            if sub_de is not None and sub_para is not None:
                # Padrão "entre X e Y" é sempre genérico (ambos os sentidos)
                debug_print(f"[TOOL] ✅ Par encontrado por padrão 'entre X e Y' (genérico): {sub_de} ↔ {sub_para}")
                return (sub_de, sub_para, False)
        
        # Padrão: "X para Y" ou "X → Y" ou "de X para Y" (direcionado)
        # Primeiro, encontrar as posições dos indicadores de direção (busca global)
        pos_para_global = query_lower.find(' para ')
        pos_arrow_global = query_lower.find(' → ')
        pos_arrow_simple_global = query_lower.find('->')
        debug_print(f"[TOOL] Posições dos indicadores: 'para'={pos_para_global}, '→'={pos_arrow_global}, '->'={pos_arrow_simple_global}")
        
        # Buscar primeiro submercado (origem) - deve estar ANTES de "para", "→", etc
        # Usar keywords para fazer match mais flexível
        safe_print(f"[TOOL] Buscando origem (antes de 'para')...")
        for keyword, subsistemas_list in keywords_to_subsistemas.items():
            if sub_de is not None:
                break
            
            # Verificar se a keyword aparece na query
            keyword_match = re.search(rf'\b{re.escape(keyword)}\b', query_lower)
            if keyword_match:
                pos_keyword = keyword_match.start()
                safe_print(f"[TOOL]   Keyword '{keyword}' encontrada na posição {pos_keyword} (subsistema: {subsistemas_list[0]['nome']})")
                
                # Verificar padrão "de X para Y" explicitamente (usando keyword)
                pattern_de_para = re.search(rf'de\s+{re.escape(keyword)}\s+para', query_lower)
                
                # É origem se:
                # 1. Matches "de X para" pattern, OR
                # 2. Aparece ANTES de um indicador de direção (para, →, ->)
                is_origin = False
                
                if pattern_de_para is not None:
                    is_origin = True
                    safe_print(f"[TOOL]     → Matches padrão 'de X para'")
                elif pos_para_global != -1 and pos_keyword < pos_para_global:
                    is_origin = True
                    safe_print(f"[TOOL]     → Está antes de 'para' (pos {pos_keyword} < {pos_para_global})")
                elif pos_arrow_global != -1 and pos_keyword < pos_arrow_global:
                    is_origin = True
                    safe_print(f"[TOOL]     → Está antes de '→'")
                elif pos_arrow_simple_global != -1 and pos_keyword < pos_arrow_simple_global:
                    is_origin = True
                    safe_print(f"[TOOL]     → Está antes de '->'")
                
                if is_origin:
                    # Usar o primeiro subsistema associado à keyword
                    sub_de = subsistemas_list[0]['codigo']
                    safe_print(f"[TOOL] ✅ Código {sub_de} encontrado como origem: '{subsistemas_list[0]['nome']}' (keyword: '{keyword}')")
                    break
        
        # Buscar segundo submercado (destino) - deve estar DEPOIS de "para", "→", etc
        safe_print(f"[TOOL] Buscando destino (depois de 'para')...")
        for keyword, subsistemas_list in keywords_to_subsistemas.items():
            if sub_para is not None:
                break
            
            # Verificar se a keyword aparece na query
            keyword_match = re.search(rf'\b{re.escape(keyword)}\b', query_lower)
            if keyword_match:
                pos_keyword = keyword_match.start()
                safe_print(f"[TOOL]   Keyword '{keyword}' encontrada na posição {pos_keyword} (subsistema: {subsistemas_list[0]['nome']})")
                
                # É destino se aparece DEPOIS de um indicador de direção
                is_destination = False
                
                if pos_para_global != -1 and pos_keyword > pos_para_global:
                    is_destination = True
                    safe_print(f"[TOOL]     → Está depois de 'para' (pos {pos_keyword} > {pos_para_global})")
                elif pos_arrow_global != -1 and pos_keyword > pos_arrow_global:
                    is_destination = True
                    safe_print(f"[TOOL]     → Está depois de '→'")
                elif pos_arrow_simple_global != -1 and pos_keyword > pos_arrow_simple_global:
                    is_destination = True
                    safe_print(f"[TOOL]     → Está depois de '->'")
                
                if is_destination:
                    # Usar o primeiro subsistema associado à keyword que não seja o de origem
                    for subsistema in subsistemas_list:
                        if subsistema['codigo'] != sub_de:
                            sub_para = subsistema['codigo']
                            safe_print(f"[TOOL] ✅ Código {sub_para} encontrado como destino: '{subsistema['nome']}' (keyword: '{keyword}')")
                            break
                    if sub_para is not None:
                        break
        
        if sub_de is not None and sub_para is not None:
            # Se chegou aqui, é uma query direcionada (não foi padrão "entre X e Y")
            safe_print(f"[TOOL] ✅ Par direcionado encontrado: {sub_de} → {sub_para}")
            return (sub_de, sub_para, True)
        
        # Se encontrou apenas um, retornar None (precisa de par)
        if sub_de is not None or sub_para is not None:
            safe_print(f"[TOOL] ⚠️ Apenas um submercado identificado: de={sub_de}, para={sub_para} (intercâmbio requer par)")
        
        safe_print(f"[TOOL] ⚠️ Nenhum par de submercados específico detectado na query")
        safe_print(f"[TOOL]   Query processada: '{query_lower}'")
        safe_print(f"[TOOL]   Submercados disponíveis: {[(s['codigo'], s['nome']) for s in subsistemas_disponiveis]}")
        return (None, None, None)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de limites de intercâmbio.
        
        Fluxo:
        1. Verifica se SISTEMA.DAT existe
        2. Lê o arquivo usando inewave
        3. Acessa propriedade limites_intercambio
        4. Processa e retorna dados
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo SISTEMA.DAT...")
            sistema_path = os.path.join(self.deck_path, "SISTEMA.DAT")
            
            if not os.path.exists(sistema_path):
                sistema_path_lower = os.path.join(self.deck_path, "sistema.dat")
                if os.path.exists(sistema_path_lower):
                    sistema_path = sistema_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo SISTEMA.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo SISTEMA.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {sistema_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            sistema = Sistema.read(sistema_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Acessar propriedade limites_intercambio
            debug_print("[TOOL] ETAPA 3: Acessando propriedade limites_intercambio...")
            df_limites = sistema.limites_intercambio
            
            if df_limites is None or df_limites.empty:
                safe_print(f"[TOOL] ❌ DataFrame vazio ou None")
                return {
                    "success": False,
                    "error": "Dados de limites de intercâmbio não encontrados no arquivo",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ DataFrame obtido: {len(df_limites)} registros")
            debug_print(f"[TOOL] Colunas: {list(df_limites.columns)}")
            
            # ETAPA 4: Identificar filtros da query
            debug_print("[TOOL] ETAPA 4: Identificando filtros...")
            submercado_de, submercado_para, query_direcionada = self._extract_submercados_from_query(query, sistema)
            
            # Log importante usando safe_print para garantir visibilidade
            safe_print(f"[TOOL] Submercados extraídos: de={submercado_de}, para={submercado_para}, direcionada={query_direcionada}")
            
            # Detectar tipo de limite solicitado
            query_lower = query.lower()
            filtro_sentido = None
            if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                filtro_sentido = 1  # Intercâmbio mínimo obrigatório
                debug_print("[TOOL] ✅ Filtro: Intercâmbio mínimo obrigatório")
            elif any(kw in query_lower for kw in ["maximo", "máximo", "limite"]):
                filtro_sentido = 0  # Limite de intercâmbio
                debug_print("[TOOL] ✅ Filtro: Limite máximo de intercâmbio")
            
            # Aplicar filtros
            df_filtrado = df_limites.copy()
            safe_print(f"[TOOL] DataFrame antes dos filtros: {len(df_filtrado)} registros")
            if len(df_filtrado) > 0:
                safe_print(f"[TOOL] Colunas disponíveis: {list(df_filtrado.columns)}")
                if 'submercado_de' in df_filtrado.columns and 'submercado_para' in df_filtrado.columns:
                    pares_unicos = df_filtrado[['submercado_de', 'submercado_para']].drop_duplicates()
                    safe_print(f"[TOOL] Pares únicos no DataFrame: {pares_unicos.values.tolist()}")
            
            if submercado_de is not None and submercado_para is not None:
                # Se query é genérica ("entre X e Y"), incluir ambos os sentidos
                if query_direcionada is False:
                    # Query genérica: incluir ambos os sentidos (X→Y e Y→X)
                    mask = (
                        ((df_filtrado['submercado_de'] == submercado_de) & 
                         (df_filtrado['submercado_para'] == submercado_para)) |
                        ((df_filtrado['submercado_de'] == submercado_para) & 
                         (df_filtrado['submercado_para'] == submercado_de))
                    )
                    df_filtrado = df_filtrado[mask]
                    debug_print(f"[TOOL] ✅ Filtrado por par genérico (ambos os sentidos): {submercado_de} ↔ {submercado_para}")
                else:
                    # Query direcionada: apenas um sentido (X→Y)
                    mask = (
                        (df_filtrado['submercado_de'] == submercado_de) & 
                        (df_filtrado['submercado_para'] == submercado_para)
                    )
                    df_filtrado = df_filtrado[mask]
                    debug_print(f"[TOOL] ✅ Filtrado por par direcionado: {submercado_de} → {submercado_para}")
            elif submercado_de is not None:
                # Apenas origem especificada
                df_filtrado = df_filtrado[df_filtrado['submercado_de'] == submercado_de]
                debug_print(f"[TOOL] ✅ Filtrado por submercado de origem: {submercado_de}")
            elif submercado_para is not None:
                # Apenas destino especificado
                df_filtrado = df_filtrado[df_filtrado['submercado_para'] == submercado_para]
                debug_print(f"[TOOL] ✅ Filtrado por submercado de destino: {submercado_para}")
            
            if filtro_sentido is not None:
                df_filtrado = df_filtrado[df_filtrado['sentido'] == filtro_sentido]
                debug_print(f"[TOOL] ✅ Filtrado por sentido: {filtro_sentido}")
            
            safe_print(f"[TOOL] DataFrame após filtros: {len(df_filtrado)} registros")
            
            # Fallback: Se query é direcionada e não encontrou dados, verificar sentido inverso
            # Os limites são armazenados em blocos que representam ambos os sentidos (A->B e B->A)
            # Se não encontrou no sentido solicitado, buscar no sentido inverso mantendo o par e invertendo o sentido (0 ↔ 1)
            if df_filtrado.empty and query_direcionada is True and submercado_de is not None and submercado_para is not None:
                safe_print(f"[TOOL] ⚠️ Par {submercado_de}→{submercado_para} não encontrado, verificando sentido inverso...")
                
                # Buscar no sentido inverso (par invertido no arquivo)
                mask_inverso = (
                    (df_limites['submercado_de'] == submercado_para) & 
                    (df_limites['submercado_para'] == submercado_de)
                )
                df_inverso = df_limites[mask_inverso].copy()
                
                if not df_inverso.empty:
                    # Se há filtro de sentido, buscar o sentido invertido (0 ↔ 1)
                    # Pois quando você inverte a direção, o sentido também é invertido
                    if filtro_sentido is not None:
                        sentido_invertido = 1 - filtro_sentido  # Inverte 0 ↔ 1
                        df_inverso = df_inverso[df_inverso['sentido'] == sentido_invertido].copy()
                        safe_print(f"[TOOL] ✅ Aplicando filtro de sentido invertido: {sentido_invertido} (solicitado: {filtro_sentido})")
                    
                    if not df_inverso.empty:
                        # Manter o par original do arquivo durante a busca, mas ao final atualizar para refletir a direção solicitada
                        # Inverter o sentido (0 ↔ 1) pois ao inverter a direção, o sentido também é invertido
                        df_inverso = df_inverso.copy()
                        df_inverso['sentido'] = 1 - df_inverso['sentido']  # Inverte 0 ↔ 1
                        # Atualizar submercado_de e submercado_para para refletir a direção solicitada pelo usuário
                        df_inverso['submercado_de'] = submercado_de
                        df_inverso['submercado_para'] = submercado_para
                        df_filtrado = df_inverso
                        safe_print(f"[TOOL] ✅ Dados encontrados no sentido inverso {submercado_para}→{submercado_de}, mantendo par e invertendo sentido para {submercado_de}→{submercado_para}")
            
            if df_filtrado.empty:
                # Log detalhado do erro
                safe_print(f"[TOOL] ❌ Nenhum resultado encontrado após filtros")
                safe_print(f"[TOOL]   Filtros aplicados: de={submercado_de}, para={submercado_para}, direcionada={query_direcionada}, sentido={filtro_sentido}")
                if submercado_de is not None and submercado_para is not None:
                    # Verificar se o par existe no DataFrame original
                    mask_de_para = (df_limites['submercado_de'] == submercado_de) & (df_limites['submercado_para'] == submercado_para)
                    mask_para_de = (df_limites['submercado_de'] == submercado_para) & (df_limites['submercado_para'] == submercado_de)
                    if mask_de_para.any() or mask_para_de.any():
                        safe_print(f"[TOOL]   ⚠️ Par {submercado_de}→{submercado_para} existe no DataFrame, mas foi filtrado por outros critérios")
                    else:
                        safe_print(f"[TOOL]   ⚠️ Par {submercado_de}→{submercado_para} não existe no DataFrame")
                return {
                    "success": False,
                    "error": "Nenhum limite de intercâmbio encontrado com os filtros especificados",
                    "tool": self.get_name()
                }
            
            # ETAPA 5: Processar dados
            debug_print("[TOOL] ETAPA 5: Processando dados...")
            
            # Adicionar colunas auxiliares
            if 'data' in df_filtrado.columns:
                if not pd.api.types.is_datetime64_any_dtype(df_filtrado['data']):
                    try:
                        df_filtrado['data'] = pd.to_datetime(df_filtrado['data'], errors='coerce')
                    except Exception as e:
                        debug_print(f"[TOOL] ⚠️ Erro ao converter data: {e}")
                
                if pd.api.types.is_datetime64_any_dtype(df_filtrado['data']):
                    df_filtrado['ano'] = df_filtrado['data'].dt.year
                    df_filtrado['mes'] = df_filtrado['data'].dt.month
                    df_filtrado['ano_mes'] = df_filtrado['data'].dt.strftime('%Y-%m')
            
            # Obter nomes dos submercados
            nomes_submercados = {}
            if sistema.custo_deficit is not None:
                df_custo = sistema.custo_deficit
                subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
                for _, row in subsistemas_unicos.iterrows():
                    codigo = int(row.get('codigo_submercado'))
                    nome = str(row.get('nome_submercado', '')).strip()
                    nomes_submercados[codigo] = nome
            
            # Adicionar nomes ao DataFrame
            df_filtrado['nome_submercado_de'] = df_filtrado['submercado_de'].map(nomes_submercados)
            df_filtrado['nome_submercado_para'] = df_filtrado['submercado_para'].map(nomes_submercados)
            
            # Estatísticas
            total_registros = len(df_filtrado)
            pares_submercados = df_filtrado[['submercado_de', 'submercado_para']].drop_duplicates()
            anos = sorted(df_filtrado['ano'].unique().tolist()) if 'ano' in df_filtrado.columns else []
            
            # Estatísticas por par de submercados e sentido
            stats_por_par = []
            # Agrupar por par E sentido para separar mínimo e máximo
            if 'sentido' in df_filtrado.columns:
                pares_com_sentido = df_filtrado[['submercado_de', 'submercado_para', 'sentido']].drop_duplicates()
            else:
                # Se não tem coluna sentido, agrupar apenas por par
                pares_com_sentido = df_filtrado[['submercado_de', 'submercado_para']].drop_duplicates()
                pares_com_sentido['sentido'] = None
            
            for _, row in pares_com_sentido.iterrows():
                sub_de = int(row['submercado_de'])
                sub_para = int(row['submercado_para'])
                sentido = row.get('sentido')
                
                # Filtrar por par e sentido
                mask = (
                    (df_filtrado['submercado_de'] == sub_de) & 
                    (df_filtrado['submercado_para'] == sub_para)
                )
                if sentido is not None and pd.notna(sentido):
                    mask = mask & (df_filtrado['sentido'] == sentido)
                
                df_par = df_filtrado[mask]
                
                if len(df_par) > 0:
                    sentido_desc = None
                    if sentido is not None and pd.notna(sentido):
                        sentido_desc = 'Intercâmbio mínimo obrigatório' if sentido == 1 else 'Limite máximo de intercâmbio'
                    
                    stats_por_par.append({
                        'submercado_de': sub_de,
                        'submercado_para': sub_para,
                        'nome_de': nomes_submercados.get(sub_de, f'Subsistema {sub_de}'),
                        'nome_para': nomes_submercados.get(sub_para, f'Subsistema {sub_para}'),
                        'sentido': int(sentido) if sentido is not None and pd.notna(sentido) else None,
                        'sentido_descricao': sentido_desc,
                        'total_registros': len(df_par),
                        'valor_medio': float(df_par['valor'].mean()) if 'valor' in df_par.columns else 0,
                        'valor_min': float(df_par['valor'].min()) if 'valor' in df_par.columns else 0,
                        'valor_max': float(df_par['valor'].max()) if 'valor' in df_par.columns else 0,
                    })
            
            # ETAPA 6: Formatar resultado
            debug_print("[TOOL] ETAPA 6: Formatando resultado...")
            
            # Converter DataFrame para lista de dicts
            result_data = df_filtrado.to_dict(orient="records")
            
            # Converter tipos para JSON-serializable
            for record in result_data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if submercado_de is not None:
                filtro_info['submercado_de'] = {
                    'codigo': submercado_de,
                    'nome': nomes_submercados.get(submercado_de, f'Subsistema {submercado_de}')
                }
            if submercado_para is not None:
                filtro_info['submercado_para'] = {
                    'codigo': submercado_para,
                    'nome': nomes_submercados.get(submercado_para, f'Subsistema {submercado_para}')
                }
            if filtro_sentido is not None:
                filtro_info['sentido'] = {
                    'codigo': filtro_sentido,
                    'descricao': 'Intercâmbio mínimo obrigatório' if filtro_sentido == 1 else 'Limite máximo de intercâmbio'
                }
            
            return {
                "success": True,
                "data": result_data,
                "summary": {
                    "total_registros": total_registros,
                    "registros_retornados": len(result_data),
                    "pares_submercados": len(pares_submercados),
                    "anos": anos,
                    "periodo": f"{min(anos)} - {max(anos)}" if anos else "N/A",
                    "filtro_aplicado": filtro_info if filtro_info else None
                },
                "stats_por_par": stats_por_par,
                "columns": list(df_filtrado.columns),
                "description": "Limites de intercâmbio entre subsistemas/submercados",
                "tool": self.get_name()
            }
            
        except FileNotFoundError as e:
            safe_print(f"[TOOL] ❌ Erro FileNotFoundError: {e}")
            return {
                "success": False,
                "error": f"Arquivo não encontrado: {str(e)}",
                "tool": self.get_name()
            }
        except Exception as e:
            safe_print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao processar SISTEMA.DAT: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """Limites intercâmbio subsistemas limites_intercambio SISTEMA.DAT par-a-par interligação capacidade."""


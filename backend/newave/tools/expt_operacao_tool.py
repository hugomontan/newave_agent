"""
Tool para consultar dados de operação térmica do EXPT.DAT.
Acessa expansões e modificações temporárias das usinas termoelétricas.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Expt
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print

class ExptOperacaoTool(NEWAVETool):
    """
    Tool para consultar dados de operação térmica do EXPT.DAT.
    
    Dados disponíveis:
    - Expansões de potência (POTEF)
    - Geração mínima (GTMIN)
    - Fator de capacidade (FCMAX)
    - Indisponibilidades (IPTER, TEIFT)
    - Desativações e repotenciações
    """
    
    def get_name(self) -> str:
        return "ExptOperacaoTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre operação térmica do EXPT.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "expt",
            "modificações",
            "expansão térmica",
            "expansao termica",
            "expansão termelétrica",
            "expansao termoeletrica",
            "operação térmica",
            "operacao termica",
            "dados operação térmica",
            "dados operacao termica",
            "potência efetiva",
            "potencia efetiva",
            "geração mínima",
            "geracao minima",
            "fator capacidade",
            "indisponibilidade",
            "desativação térmica",
            "desativacao termica",
            "repotenciação",
            "repotenciacao",
            "modificação térmica",
            "modificacao termica",
            "expansões térmicas",
            "expansoes termicas"
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_tipo_modificacao(self, query: str) -> Optional[str]:
        """
        Extrai tipo de modificação da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            "POTEF", "GTMIN", "FCMAX", "IPTER", "TEIFT", ou None (todos)
        """
        query_lower = query.lower()
        
        # Lista ordenada: mais específicas primeiro, mais genéricas depois
        # Ordem: TEIFT > IPTER > FCMAX > GTMIN > POTEF
        # Isso garante que termos mais específicos sejam detectados antes dos genéricos
        tipos_ordenados = [
            # TEIFT - mais específicas primeiro
            ("taxa equivalente de indisponibilidade forçada", "TEIFT"),
            ("taxa equivalente de indisponibilidade forcada", "TEIFT"),
            ("taxa equivalente indisponibilidade forçada", "TEIFT"),
            ("taxa equivalente indisponibilidade forcada", "TEIFT"),
            ("taxa indisponibilidade forçada", "TEIFT"),
            ("taxa indisponibilidade forcada", "TEIFT"),
            ("indisponibilidade forçada", "TEIFT"),
            ("indisponibilidade forcada", "TEIFT"),
            ("taxa indisponibilidade", "TEIFT"),
            ("teift", "TEIFT"),
            
            # IPTER
            ("indisponibilidades programadas", "IPTER"),
            ("indisponibilidade programada", "IPTER"),
            ("ipter", "IPTER"),
            
            # FCMAX
            ("fator de capacidade máximo", "FCMAX"),
            ("fator capacidade maximo", "FCMAX"),
            ("fator de capacidade", "FCMAX"),
            ("fator capacidade", "FCMAX"),
            ("fcmax", "FCMAX"),
            
            # GTMIN
            ("geração térmica mínima", "GTMIN"),
            ("geracao termica minima", "GTMIN"),
            ("geração mínima", "GTMIN"),
            ("geracao minima", "GTMIN"),
            ("gtmin", "GTMIN"),
            
            # POTEF
            ("potência efetiva", "POTEF"),
            ("potencia efetiva", "POTEF"),
            ("potef", "POTEF"),
            ("potencia", "POTEF"),
        ]
        
        # Buscar do mais específico para o mais genérico
        for key, value in tipos_ordenados:
            if key in query_lower:
                debug_print(f"[TOOL] ✅ Tipo detectado: {value} (palavra-chave: '{key}')")
                return value
        
        debug_print("[TOOL] ⚠️ Nenhum tipo de modificação detectado na query")
        return None
    
    def _extract_usina_from_query(self, query: str, expt: Expt) -> Optional[int]:
        """
        Extrai código da usina da query.
        Busca por número ou nome da usina.
        
        Args:
            query: Query do usuário
            expt: Objeto Expt já lido
            
        Returns:
            Código da usina ou None se não encontrado
        """
        query_lower = query.lower()
        
        # ETAPA 1: Tentar extrair número explícito
        patterns = [
            r'usina\s*(\d+)',
            r'usina\s*térmica\s*(\d+)',
            r'usina\s*termica\s*(\d+)',
            r'usina\s*#?\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    if expt.expansoes is not None:
                        codigos_validos = expt.expansoes['codigo_usina'].unique()
                        if codigo in codigos_validos:
                            debug_print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                            return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina
        if expt.expansoes is not None:
            usinas_unicas = expt.expansoes[['codigo_usina', 'nome_usina']].drop_duplicates()
            usinas_unicas = usinas_unicas.sort_values('codigo_usina')
            
            debug_print(f"[TOOL] Usinas disponíveis no arquivo:")
            for _, row in usinas_unicas.iterrows():
                codigo = int(row.get('codigo_usina'))
                nome = str(row.get('nome_usina', '')).strip()
                print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
            
            # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
            # Isso garante que "Maranhão III" seja encontrado antes de "Maranhão V"
            usinas_sorted = sorted(
                usinas_unicas.iterrows(),
                key=lambda x: len(str(x[1].get('nome_usina', '')).strip()),
                reverse=True
            )
            
            # ETAPA 2.1: Buscar match exato do nome completo (prioridade máxima)
            for _, row in usinas_sorted:
                codigo_usina = int(row.get('codigo_usina'))
                nome_usina = str(row.get('nome_usina', '')).strip()
                nome_usina_lower = nome_usina.lower().strip()
                
                if not nome_usina_lower:
                    continue
                
                # Match exato do nome completo
                if nome_usina_lower == query_lower.strip():
                    debug_print(f"[TOOL] ✅ Código {codigo_usina} encontrado por match exato '{nome_usina}'")
                    return codigo_usina
                
                # Match exato do nome completo dentro da query (com word boundaries)
                # Isso evita que "Maranhão III" seja confundido com "Maranhão V"
                if nome_usina_lower in query_lower:
                    # Verificar se não é apenas uma palavra parcial muito curta
                    if len(nome_usina_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                        # Verificar se está como palavra completa (não parte de outra palavra)
                        # Usar word boundaries para evitar matches parciais
                        pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                        if re.search(pattern, query_lower):
                            debug_print(f"[TOOL] ✅ Código {codigo_usina} encontrado por nome completo '{nome_usina}' na query")
                            return codigo_usina
            
            # ETAPA 2.2: Buscar por palavras-chave do nome (apenas se match exato não encontrou)
            # Mas com verificação mais rigorosa para evitar matches incorretos
            palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos'}
            palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            
            # Lista de candidatos com pontuação
            candidatos = []
            
            for _, row in usinas_sorted:
                codigo_usina = int(row.get('codigo_usina'))
                nome_usina = str(row.get('nome_usina', '')).strip()
                nome_usina_lower = nome_usina.lower().strip()
                
                if not nome_usina_lower:
                    continue
                
                # Extrair palavras significativas do nome da usina
                palavras_nome = [p for p in nome_usina_lower.split() if len(p) > 2 and p not in palavras_ignorar]
                
                # Calcular score: quantas palavras da query estão no nome
                palavras_comuns = set(palavras_query) & set(palavras_nome)
                score = len(palavras_comuns)
                
                # Bonus se todas as palavras significativas da query estão no nome
                if palavras_query and all(p in palavras_nome for p in palavras_query):
                    score += 10  # Bonus grande para match completo
                
                # Bonus se o nome é mais longo (mais específico)
                score += len(nome_usina_lower) / 100
                
                if score > 0:
                    candidatos.append((codigo_usina, nome_usina, score))
            
            # Ordenar candidatos por score (maior primeiro)
            candidatos.sort(key=lambda x: x[2], reverse=True)
            
            if candidatos:
                melhor_codigo, melhor_nome, melhor_score = candidatos[0]
                debug_print(f"[TOOL] ✅ Código {melhor_codigo} encontrado por palavras-chave '{melhor_nome}' (score: {melhor_score:.2f})")
                return melhor_codigo
        
        debug_print("[TOOL] ⚠️ Nenhuma usina específica detectada na query")
        return None
    
    def _extract_operacao_especifica(self, query: str) -> Optional[str]:
        """
        Identifica se a query pede algo específico.
        
        Args:
            query: Query do usuário
            
        Returns:
            "desativacao", "repotenciacao", "expansao", ou None
        """
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["desativação", "desativacao", "desativar", "desativa"]):
            return "desativacao"
        elif any(kw in query_lower for kw in ["repotenciação", "repotenciacao", "repotenciar", "repotencia"]):
            return "repotenciacao"
        elif any(kw in query_lower for kw in ["expansão", "expansao"]):
            return "expansao"
        
        return None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de dados de operação térmica.
        
        Fluxo:
        1. Verifica se EXPT.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica filtros (usina, tipo de modificação, operação específica)
        4. Processa e retorna dados
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo EXPT.DAT...")
            expt_path = os.path.join(self.deck_path, "EXPT.DAT")
            
            if not os.path.exists(expt_path):
                expt_path_lower = os.path.join(self.deck_path, "expt.dat")
                if os.path.exists(expt_path_lower):
                    expt_path = expt_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo EXPT.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo EXPT.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {expt_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            expt = Expt.read(expt_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            if expt.expansoes is None or expt.expansoes.empty:
                debug_print("[TOOL] ⚠️ Nenhum dado de expansão disponível")
                return {
                    "success": False,
                    "error": "Nenhuma expansão ou modificação encontrada no arquivo EXPT.DAT",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ DataFrame obtido: {len(expt.expansoes)} registros")
            debug_print(f"[TOOL] Colunas: {list(expt.expansoes.columns)}")
            
            # ETAPA 4: Identificar filtros
            debug_print("[TOOL] ETAPA 4: Identificando filtros...")
            codigo_usina = self._extract_usina_from_query(query, expt)
            tipo_modificacao = self._extract_tipo_modificacao(query)
            operacao_especifica = self._extract_operacao_especifica(query)
            
            if codigo_usina is not None:
                debug_print(f"[TOOL] ✅ Filtro por usina: {codigo_usina}")
            if tipo_modificacao is not None:
                debug_print(f"[TOOL] ✅ Filtro por tipo de modificação: {tipo_modificacao}")
            if operacao_especifica is not None:
                debug_print(f"[TOOL] ✅ Filtro por operação específica: {operacao_especifica}")
            
            # ETAPA 5: Processar dados
            debug_print("[TOOL] ETAPA 5: Processando dados...")
            df_expansoes = expt.expansoes.copy()
            
            # Aplicar filtros
            if codigo_usina is not None:
                df_expansoes = df_expansoes[df_expansoes['codigo_usina'] == codigo_usina]
                debug_print(f"[TOOL] ✅ Dados filtrados por usina {codigo_usina}: {len(df_expansoes)} registros")
            
            if tipo_modificacao is not None:
                df_expansoes = df_expansoes[df_expansoes['tipo'] == tipo_modificacao]
                debug_print(f"[TOOL] ✅ Dados filtrados por tipo {tipo_modificacao}: {len(df_expansoes)} registros")
            
            # Processar operações específicas
            desativacoes = None
            repotenciacoes = None
            expansoes = None
            
            if operacao_especifica == "desativacao" or operacao_especifica is None:
                # Desativações: POTEF=0 ou FCMAX=0
                desativacoes_df = df_expansoes[
                    ((df_expansoes['tipo'] == 'POTEF') & (df_expansoes['modificacao'] == 0)) |
                    ((df_expansoes['tipo'] == 'FCMAX') & (df_expansoes['modificacao'] == 0))
                ]
                if not desativacoes_df.empty:
                    desativacoes = desativacoes_df.to_dict(orient="records")
                    debug_print(f"[TOOL] ✅ {len(desativacoes)} desativações encontradas")
            
            if operacao_especifica == "repotenciacao" or operacao_especifica is None:
                # Repotenciações: POTEF > 0
                repotenciacoes_df = df_expansoes[
                    (df_expansoes['tipo'] == 'POTEF') &
                    (df_expansoes['modificacao'] > 0)
                ]
                if not repotenciacoes_df.empty:
                    repotenciacoes = repotenciacoes_df.to_dict(orient="records")
                    debug_print(f"[TOOL] ✅ {len(repotenciacoes)} repotenciações encontradas")
            
            if operacao_especifica == "expansao" or operacao_especifica is None:
                # Expansões: todas as modificações de POTEF
                expansoes_df = df_expansoes[df_expansoes['tipo'] == 'POTEF']
                if not expansoes_df.empty:
                    expansoes = expansoes_df.to_dict(orient="records")
                    debug_print(f"[TOOL] ✅ {len(expansoes)} expansões encontradas")
            
            # Converter DataFrame para lista de dicts
            dados_expansoes = df_expansoes.to_dict(orient="records")
            
            # Converter tipos para JSON-serializable
            for record in dados_expansoes:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            # Converter também desativacoes, repotenciacoes e expansoes
            if desativacoes:
                for record in desativacoes:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            if repotenciacoes:
                for record in repotenciacoes:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            if expansoes:
                for record in expansoes:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            # ETAPA 6: Calcular estatísticas
            debug_print("[TOOL] ETAPA 6: Calculando estatísticas...")
            
            stats_geral = {
                'total_registros': len(df_expansoes),
                'total_usinas': df_expansoes['codigo_usina'].nunique() if 'codigo_usina' in df_expansoes.columns else 0,
                'tipos_modificacao': df_expansoes['tipo'].unique().tolist() if 'tipo' in df_expansoes.columns else [],
            }
            
            # Estatísticas por tipo de modificação
            stats_por_tipo = []
            if 'tipo' in df_expansoes.columns and 'modificacao' in df_expansoes.columns:
                for tipo in df_expansoes['tipo'].unique():
                    df_tipo = df_expansoes[df_expansoes['tipo'] == tipo]
                    stats_por_tipo.append({
                        'tipo': tipo,
                        'total_registros': len(df_tipo),
                        'usinas_afetadas': df_tipo['codigo_usina'].nunique(),
                        'valor_medio': float(df_tipo['modificacao'].mean()) if len(df_tipo) > 0 else 0,
                        'valor_min': float(df_tipo['modificacao'].min()) if len(df_tipo) > 0 else 0,
                        'valor_max': float(df_tipo['modificacao'].max()) if len(df_tipo) > 0 else 0,
                    })
            
            # Estatísticas por usina
            stats_por_usina = []
            if 'codigo_usina' in df_expansoes.columns:
                for codigo in df_expansoes['codigo_usina'].unique():
                    df_usina = df_expansoes[df_expansoes['codigo_usina'] == codigo]
                    nome_usina = df_usina.iloc[0].get('nome_usina', f'Usina {codigo}') if not df_usina.empty else f'Usina {codigo}'
                    
                    tipos_usina = df_usina['tipo'].unique().tolist()
                    stats_por_usina.append({
                        'codigo_usina': int(codigo),
                        'nome_usina': nome_usina,
                        'total_modificacoes': len(df_usina),
                        'tipos_modificacao': tipos_usina,
                    })
            
            # Estatísticas de indisponibilidades
            indisponibilidades = None
            if 'tipo' in df_expansoes.columns:
                indisponibilidades_df = df_expansoes[df_expansoes['tipo'].isin(['IPTER', 'TEIFT'])]
                if not indisponibilidades_df.empty:
                    indisponibilidades = indisponibilidades_df.to_dict(orient="records")
                    for record in indisponibilidades:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            # ETAPA 7: Formatar resultado
            debug_print("[TOOL] ETAPA 7: Formatando resultado...")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if codigo_usina is not None:
                if expt.expansoes is not None:
                    usina_info = expt.expansoes[expt.expansoes['codigo_usina'] == codigo_usina]
                    if not usina_info.empty:
                        filtro_info['usina'] = {
                            'codigo': codigo_usina,
                            'nome': usina_info.iloc[0].get('nome_usina', f'Usina {codigo_usina}'),
                        }
            if tipo_modificacao is not None:
                filtro_info['tipo_modificacao'] = tipo_modificacao
            if operacao_especifica is not None:
                filtro_info['operacao_especifica'] = operacao_especifica
            
            return {
                "success": True,
                "dados_expansoes": dados_expansoes,
                "desativacoes": desativacoes,
                "repotenciacoes": repotenciacoes,
                "expansoes": expansoes,
                "indisponibilidades": indisponibilidades,
                "filtros": filtro_info if filtro_info else None,
                "stats_geral": stats_geral,
                "stats_por_tipo": stats_por_tipo,
                "stats_por_usina": stats_por_usina,
                "description": "Dados de operação térmica do EXPT.DAT (expansões, modificações, desativações, repotenciações)",
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
                "error": f"Erro ao processar EXPT.DAT: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """
        Operação térmica. Expansões térmicas. Modificações temporárias das características operacionais das usinas termoelétricas.
        
        Queries que ativam esta tool:
        - "quais são as modificações térmicas do EXPT"
        - "modificações térmicas"
        - "expansão térmica"
        - "expansões térmicas"
        - "operação térmica"
        - "modificação termelétrica"
        - "expansões da usina 1"
        - "expansões da usina ANGRA 1"
        - "potência efetiva das térmicas"
        - "potência efetiva térmica"
        - "geração mínima das térmicas"
        - "geração mínima térmica"
        - "fator de capacidade"
        - "fator de capacidade máximo"
        - "indisponibilidades programadas das térmicas"
        - "indisponibilidade programada térmica"
        - "desativações de usinas térmicas"
        - "desativações térmicas"
        - "repotenciações no EXPT"
        - "repotenciações térmicas"
        - "modificações da usina ANGRA 1"
        - "modificações da usina CUBATÃO"
        - "ajustes operacionais das usinas térmicas"
        - "alterações de capacidade das termelétricas"
        - "quais térmicas foram desativadas"
        - "usinas térmicas com repotenciação"
        - "dados de operação térmica do EXPT"
        
        Termos-chave: expt, modificações térmicas, expansão térmica, expansões térmicas, operação térmica, modificação termelétrica, potência efetiva, geração mínima, fator de capacidade, indisponibilidade programada, desativações, repotenciações.
        """

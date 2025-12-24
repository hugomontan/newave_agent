"""
Tool para consultar geração de usinas não simuladas do SISTEMA.DAT.
Acessa o arquivo SISTEMA.DAT, propriedade geracao_usinas_nao_simuladas.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Sistema
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from datetime import datetime


class UsinasNaoSimuladasTool(NEWAVETool):
    """
    Tool para consultar geração de usinas não simuladas do SISTEMA.DAT.
    
    Dados disponíveis:
    - Código do submercado
    - Índice do bloco
    - Fonte/tecnologia
    - Data/período
    - Valor (geração em MWmédio)
    """
    
    def get_name(self) -> str:
        return "UsinasNaoSimuladasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre usinas não simuladas.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "usinas não simuladas",
            "usinas nao simuladas",
            "geração não simulada",
            "geracao nao simulada",
            "pequenas usinas",
            "geracao usinas nao simuladas",
            "geração usinas não simuladas",
            "bloco usinas",
            "fonte geração",
            "fonte geracao",
            "tecnologia geração",
            "tecnologia geracao",
            "usinas nao simuladas subsistema",
            "geracao nao simulada subsistema",
            "valores mensais",
            "valores mensais de",
            "carga de",
            "geração de",
            "geracao de",
        ]
        # Verificar também por siglas de fontes comuns
        fontes_siglas = ["pch", "pct", "eol", "ufv", "mmgd"]
        tem_fonte = any(sigla in query_lower for sigla in fontes_siglas)
        
        # Se tem fonte e menciona "carga de", "geração de", "valores mensais de", etc.
        # Priorizar esta tool sobre CargaMensalTool
        if tem_fonte and ("carga de" in query_lower or "geração de" in query_lower or "geracao de" in query_lower or "valores mensais de" in query_lower):
            return True
        
        return any(kw in query_lower for kw in keywords) or (tem_fonte and ("mensal" in query_lower or "valores" in query_lower))
    
    def _extract_submercado_from_query(self, query: str, sistema: Sistema, subsistemas_disponiveis: list = None) -> Optional[int]:
        """
        Extrai código do submercado da query.
        Similar ao método da CargaMensalTool.
        
        Args:
            query: Query do usuário
            sistema: Objeto Sistema já lido
            subsistemas_disponiveis: Lista de dicts com {'codigo': int, 'nome': str}
            
        Returns:
            Código do submercado ou None
        """
        query_lower = query.lower()
        
        # Se não foi passada a lista, obter do sistema
        if subsistemas_disponiveis is None:
            subsistemas_disponiveis = []
            if sistema.custo_deficit is not None:
                df_custo = sistema.custo_deficit
                subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
                for _, row in subsistemas_unicos.iterrows():
                    subsistemas_disponiveis.append({
                        'codigo': int(row.get('codigo_submercado')),
                        'nome': str(row.get('nome_submercado', '')).strip()
                    })
        
        # ETAPA 1: Tentar extrair número explícito
        patterns = [
            r'subsistema\s*(\d+)',
            r'submercado\s*(\d+)',
            r'subsistema\s*n[úu]mero\s*(\d+)',
            r'submercado\s*n[úu]mero\s*(\d+)',
            r'subsistema\s*#?\s*(\d+)',
            r'submercado\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    codigos_validos = [s['codigo'] for s in subsistemas_disponiveis]
                    if codigo in codigos_validos:
                        nome_sub = next((s['nome'] for s in subsistemas_disponiveis if s['codigo'] == codigo), f"Subsistema {codigo}")
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico: '{nome_sub}'")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome do submercado
        if not subsistemas_disponiveis:
            return None
        
        subsistemas_ordenados = sorted(subsistemas_disponiveis, key=lambda x: len(x['nome']), reverse=True)
        
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                print(f"[TOOL] ✅ Código {codigo_sub} encontrado por nome: '{nome_sub}'")
                return codigo_sub
        
        return None
    
    def _extract_bloco_from_query(self, query: str) -> Optional[int]:
        """
        Extrai índice do bloco da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Índice do bloco ou None
        """
        patterns = [
            r'bloco\s*(\d+)',
            r'índice\s*bloco\s*(\d+)',
            r'indice\s*bloco\s*(\d+)',
            r'bloco\s*#?\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_fonte_from_query(self, query: str, df: pd.DataFrame) -> Optional[str]:
        """
        Extrai fonte/tecnologia da query.
        Busca por nome da fonte nas fontes disponíveis.
        Suporta siglas comuns: PCH, PCT, EOL, UFV, MMGD.
        
        Para queries genéricas (ex: "carga de EOL"), retorna a sigla base
        para que o filtro seja aplicado de forma flexível.
        
        Args:
            query: Query do usuário
            df: DataFrame com dados de geração
            
        Returns:
            Nome da fonte específica ou sigla base (para filtro flexível)
        """
        query_lower = query.lower()
        
        if 'fonte' not in df.columns:
            return None
        
        fontes_disponiveis = df['fonte'].unique()
        
        # Mapeamento de siglas comuns para padrões de busca
        siglas_mapeamento = {
            'pch': ['pch'],
            'pct': ['pct'],
            'eol': ['eol', 'eólica', 'eolica', 'vento'],
            'ufv': ['ufv', 'fotovoltaica', 'solar'],
            'mmgd': ['mmgd', 'microgeração', 'micro geração'],
        }
        
        # ETAPA 1: Verificar se a query menciona MMGD explicitamente
        # Se mencionar, buscar fonte específica com MMGD
        tem_mmgd = any(var in query_lower for var in siglas_mapeamento['mmgd'])
        
        # ETAPA 2: Identificar sigla base mencionada na query
        sigla_base_encontrada = None
        for sigla, variacoes in siglas_mapeamento.items():
            if sigla == 'mmgd':
                continue  # MMGD é tratado separadamente
            if any(var in query_lower for var in variacoes):
                sigla_base_encontrada = sigla
                break
        
        # ETAPA 3: Se encontrou sigla base e mencionou MMGD, buscar fonte específica
        if sigla_base_encontrada and tem_mmgd:
            # Buscar fonte que contenha ambas as siglas (ex: "PCH MMGD")
            for fonte in fontes_disponiveis:
                fonte_str = str(fonte).lower().strip()
                if sigla_base_encontrada in fonte_str and 'mmgd' in fonte_str:
                    print(f"[TOOL] ✅ Fonte específica encontrada: '{fonte}'")
                    return fonte
        
        # ETAPA 4: Se encontrou sigla base mas NÃO mencionou MMGD, retornar sigla base
        # (será usado para filtro flexível que pega todas as variações)
        if sigla_base_encontrada and not tem_mmgd:
            print(f"[TOOL] ✅ Sigla base encontrada para filtro genérico: '{sigla_base_encontrada.upper()}'")
            print(f"[TOOL] 🔍 Buscando todas as fontes que contêm '{sigla_base_encontrada.upper()}'...")
            # Verificar se existem fontes com essa sigla
            fontes_com_sigla = [f for f in fontes_disponiveis if sigla_base_encontrada in str(f).lower()]
            if fontes_com_sigla:
                print(f"[TOOL] ✅ Encontradas {len(fontes_com_sigla)} fonte(s) com '{sigla_base_encontrada.upper()}': {[str(f) for f in fontes_com_sigla]}")
            else:
                print(f"[TOOL] ⚠️ Nenhuma fonte encontrada com '{sigla_base_encontrada.upper()}'")
            # Retornar a sigla base com prefixo especial para indicar filtro flexível
            return f"__GEN_{sigla_base_encontrada.upper()}__"
        
        # ETAPA 5: Buscar match exato ou parcial nas fontes disponíveis
        # Ordenar por tamanho (maior primeiro) para priorizar matches mais específicos
        fontes_ordenadas = sorted(fontes_disponiveis, key=lambda x: len(str(x)), reverse=True)
        
        for fonte in fontes_ordenadas:
            fonte_str = str(fonte).lower().strip()
            if not fonte_str:
                continue
            
            # Match exato
            if fonte_str == query_lower.strip():
                print(f"[TOOL] ✅ Fonte encontrada (match exato): '{fonte}'")
                return fonte
            
            # Match parcial - fonte contida na query ou query contida na fonte
            if fonte_str in query_lower or query_lower in fonte_str:
                print(f"[TOOL] ✅ Fonte encontrada (match parcial): '{fonte}'")
                return fonte
            
            # Match por palavras-chave da fonte na query
            palavras_fonte = fonte_str.split()
            if len(palavras_fonte) > 0:
                # Se todas as palavras principais da fonte estão na query
                palavras_principais = [p for p in palavras_fonte if len(p) > 2]
                if palavras_principais and all(p in query_lower for p in palavras_principais):
                    print(f"[TOOL] ✅ Fonte encontrada (match por palavras): '{fonte}'")
                    return fonte
        
        return None
    
    def _extract_periodo_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Extrai período (ano/mês) da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Dict com 'ano' e/ou 'mes' ou None
        """
        query_lower = query.lower()
        periodo = {}
        
        # Extrair ano
        ano_match = re.search(r'ano\s*(\d{4})', query_lower)
        if ano_match:
            periodo['ano'] = int(ano_match.group(1))
        
        # Extrair mês
        meses = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        for mes_nome, mes_num in meses.items():
            if mes_nome in query_lower:
                periodo['mes'] = mes_num
                break
        
        # Extrair mês numérico
        mes_match = re.search(r'mês\s*(\d{1,2})|mes\s*(\d{1,2})', query_lower)
        if mes_match:
            mes_num = int(mes_match.group(1) or mes_match.group(2))
            if 1 <= mes_num <= 12:
                periodo['mes'] = mes_num
        
        return periodo if periodo else None
    
    def _format_geracao_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Formata os dados de geração de usinas não simuladas.
        
        Args:
            row: Linha do DataFrame
            
        Returns:
            Dicionário formatado
        """
        dados = {
            'codigo_submercado': int(row.get('codigo_submercado', 0)) if pd.notna(row.get('codigo_submercado')) else None,
            'indice_bloco': int(row.get('indice_bloco', 0)) if pd.notna(row.get('indice_bloco')) else None,
            'fonte': str(row.get('fonte', '')).strip() if pd.notna(row.get('fonte')) else None,
            'valor': float(row.get('valor', 0)) if pd.notna(row.get('valor')) else None,
        }
        
        # Formatar data
        data_val = row.get('data')
        if pd.notna(data_val):
            if isinstance(data_val, pd.Timestamp):
                dados['data'] = data_val.isoformat()
                dados['ano'] = data_val.year
                dados['mes'] = data_val.month
                dados['dia'] = data_val.day
            elif isinstance(data_val, (int, float)):
                dados['data'] = int(data_val)
                # Se data for um período numérico, tentar extrair ano
                # (depende do formato específico do arquivo)
            elif hasattr(data_val, 'isoformat'):
                dados['data'] = data_val.isoformat()
            else:
                dados['data'] = str(data_val)
        else:
            dados['data'] = None
        
        return dados
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de geração de usinas não simuladas.
        
        Fluxo:
        1. Verifica se SISTEMA.DAT existe
        2. Lê o arquivo usando inewave
        3. Acessa propriedade geracao_usinas_nao_simuladas
        4. Identifica filtros (submercado, bloco, fonte, período)
        5. Retorna dados filtrados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo SISTEMA.DAT...")
            sistema_path = os.path.join(self.deck_path, "SISTEMA.DAT")
            
            if not os.path.exists(sistema_path):
                sistema_path = os.path.join(self.deck_path, "sistema.dat")
                if not os.path.exists(sistema_path):
                    print(f"[TOOL] ❌ Arquivo SISTEMA.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo SISTEMA.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {sistema_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            sistema = Sistema.read(sistema_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Acessar propriedade geracao_usinas_nao_simuladas
            print("[TOOL] ETAPA 3: Acessando propriedade geracao_usinas_nao_simuladas...")
            df_geracao = sistema.geracao_usinas_nao_simuladas
            
            if df_geracao is None or df_geracao.empty:
                print("[TOOL] ⚠️ Nenhuma geração de usinas não simuladas encontrada")
                return {
                    "success": False,
                    "error": "Nenhuma geração de usinas não simuladas encontrada no arquivo SISTEMA.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ {len(df_geracao)} registro(s) de geração encontrado(s)")
            print(f"[TOOL] Colunas: {list(df_geracao.columns)}")
            
            # ETAPA 4: Listar subsistemas disponíveis
            print("[TOOL] ETAPA 4: Listando subsistemas disponíveis...")
            subsistemas_disponiveis = []
            if sistema.custo_deficit is not None:
                df_custo = sistema.custo_deficit
                subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
                subsistemas_unicos = subsistemas_unicos.sort_values('codigo_submercado')
                
                print("[TOOL] ===== SUBSISTEMAS DISPONÍVEIS =====")
                for _, row in subsistemas_unicos.iterrows():
                    codigo = int(row.get('codigo_submercado'))
                    nome = str(row.get('nome_submercado', '')).strip()
                    subsistemas_disponiveis.append({'codigo': codigo, 'nome': nome})
                    print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
                print("[TOOL] =====================================")
            
            # ETAPA 5: Identificar filtros
            print("[TOOL] ETAPA 5: Identificando filtros...")
            codigo_submercado = self._extract_submercado_from_query(query, sistema, subsistemas_disponiveis)
            indice_bloco = self._extract_bloco_from_query(query)
            fonte = self._extract_fonte_from_query(query, df_geracao)
            periodo = self._extract_periodo_from_query(query)
            
            if codigo_submercado is not None:
                print(f"[TOOL] ✅ Filtro por submercado: {codigo_submercado}")
            
            if indice_bloco is not None:
                print(f"[TOOL] ✅ Filtro por bloco: {indice_bloco}")
            
            if fonte is not None:
                print(f"[TOOL] ✅ Filtro por fonte: {fonte}")
            
            if periodo is not None:
                print(f"[TOOL] ✅ Filtro por período: {periodo}")
            
            # ETAPA 6: Aplicar filtros
            print("[TOOL] ETAPA 6: Aplicando filtros...")
            resultado_df = df_geracao.copy()
            
            if codigo_submercado is not None:
                resultado_df = resultado_df[resultado_df['codigo_submercado'] == codigo_submercado]
            
            if indice_bloco is not None:
                resultado_df = resultado_df[resultado_df['indice_bloco'] == indice_bloco]
            
            if fonte is not None:
                # Verificar se é um filtro genérico (sigla base)
                if fonte.startswith("__GEN_") and fonte.endswith("__"):
                    # Filtro genérico: pegar todas as fontes que contêm a sigla base
                    sigla_base = fonte.replace("__GEN_", "").replace("__", "").lower()
                    print(f"[TOOL] 🔍 Aplicando filtro genérico para '{sigla_base.upper()}' (retorna todas as variações)")
                    print(f"[TOOL] 📊 Total de registros antes do filtro de fonte: {len(resultado_df)}")
                    resultado_df = resultado_df[resultado_df['fonte'].str.lower().str.contains(sigla_base, na=False)]
                    fontes_encontradas = resultado_df['fonte'].unique().tolist() if not resultado_df.empty else []
                    print(f"[TOOL] ✅ {len(resultado_df)} registro(s) após filtro genérico")
                    print(f"[TOOL] ✅ Fontes encontradas: {fontes_encontradas}")
                    if len(resultado_df) == 0:
                        print(f"[TOOL] ⚠️ Nenhum registro encontrado com fonte contendo '{sigla_base.upper()}'")
                        print(f"[TOOL] 📋 Fontes disponíveis no DataFrame: {df_geracao['fonte'].unique().tolist()}")
                else:
                    # Filtro específico: match exato
                    print(f"[TOOL] 🔍 Aplicando filtro específico para fonte: '{fonte}'")
                    print(f"[TOOL] 📊 Total de registros antes do filtro de fonte: {len(resultado_df)}")
                    resultado_df = resultado_df[resultado_df['fonte'] == fonte]
                    print(f"[TOOL] ✅ {len(resultado_df)} registro(s) após filtro específico")
                    if len(resultado_df) == 0:
                        print(f"[TOOL] ⚠️ Nenhum registro encontrado com fonte exata '{fonte}'")
                        print(f"[TOOL] 📋 Fontes disponíveis no DataFrame: {df_geracao['fonte'].unique().tolist()}")
            
            if periodo is not None:
                # Processar filtro de período baseado no tipo de data
                if 'data' in resultado_df.columns:
                    if 'ano' in periodo:
                        if pd.api.types.is_datetime64_any_dtype(resultado_df['data']):
                            resultado_df = resultado_df[resultado_df['data'].dt.year == periodo['ano']]
                        elif pd.api.types.is_integer_dtype(resultado_df['data']):
                            # Se data é int, pode ser período/ano
                            # Tentar filtrar (pode precisar de ajuste baseado no formato real)
                            pass
                    
                    if 'mes' in periodo:
                        if pd.api.types.is_datetime64_any_dtype(resultado_df['data']):
                            resultado_df = resultado_df[resultado_df['data'].dt.month == periodo['mes']]
            
            print(f"[TOOL] ✅ {len(resultado_df)} registro(s) após filtros")
            
            # Verificar se há resultados após filtros
            if len(resultado_df) == 0:
                print("[TOOL] ⚠️ Nenhum registro encontrado após aplicar filtros")
                print(f"[TOOL] 📋 Informações de debug:")
                print(f"[TOOL]   - Total de registros no arquivo: {len(df_geracao)}")
                print(f"[TOOL]   - Fontes disponíveis: {df_geracao['fonte'].unique().tolist() if not df_geracao.empty else 'N/A'}")
                print(f"[TOOL]   - Submercados disponíveis: {df_geracao['codigo_submercado'].unique().tolist() if not df_geracao.empty else 'N/A'}")
                print(f"[TOOL]   - Blocos disponíveis: {df_geracao['indice_bloco'].unique().tolist() if not df_geracao.empty else 'N/A'}")
            
            # ETAPA 7: Formatar resultados
            print("[TOOL] ETAPA 7: Formatando resultados...")
            dados_lista = []
            for _, row in resultado_df.iterrows():
                dados_lista.append(self._format_geracao_data(row))
            
            # ETAPA 8: Estatísticas
            stats = {
                'total_registros': len(df_geracao),
                'registros_filtrados': len(resultado_df),
            }
            
            # Geração por submercado
            if 'codigo_submercado' in df_geracao.columns:
                stats['geracao_por_submercado'] = df_geracao.groupby('codigo_submercado').size().to_dict()
            
            # Geração por bloco
            if 'indice_bloco' in df_geracao.columns:
                stats['geracao_por_bloco'] = df_geracao.groupby('indice_bloco').size().to_dict()
            
            # Geração por fonte
            if 'fonte' in df_geracao.columns:
                stats['geracao_por_fonte'] = df_geracao.groupby('fonte').size().to_dict()
            
            # Total de geração por submercado
            if 'codigo_submercado' in df_geracao.columns and 'valor' in df_geracao.columns:
                total_por_submercado = df_geracao.groupby('codigo_submercado')['valor'].sum().to_dict()
                stats['total_geracao_por_submercado'] = {k: round(v, 2) for k, v in total_por_submercado.items()}
            
            # Total de geração por bloco
            if 'indice_bloco' in df_geracao.columns and 'valor' in df_geracao.columns:
                total_por_bloco = df_geracao.groupby('indice_bloco')['valor'].sum().to_dict()
                stats['total_geracao_por_bloco'] = {k: round(v, 2) for k, v in total_por_bloco.items()}
            
            # Geração por ano (se data for datetime)
            if 'data' in df_geracao.columns and pd.api.types.is_datetime64_any_dtype(df_geracao['data']):
                df_copy = df_geracao.copy()
                df_copy['ano'] = df_copy['data'].dt.year
                stats['geracao_por_ano'] = df_copy.groupby('ano').size().to_dict()
            
            # ETAPA 9: Formatar resultado final
            print("[TOOL] ETAPA 9: Formatando resultado final...")
            
            filtros_aplicados = {}
            if codigo_submercado is not None:
                nome_sub = next((s['nome'] for s in subsistemas_disponiveis if s['codigo'] == codigo_submercado), f"Subsistema {codigo_submercado}")
                filtros_aplicados['submercado'] = {
                    'codigo': codigo_submercado,
                    'nome': nome_sub
                }
            if indice_bloco is not None:
                filtros_aplicados['bloco'] = indice_bloco
            if fonte is not None:
                filtros_aplicados['fonte'] = fonte
            if periodo is not None:
                filtros_aplicados['periodo'] = periodo
            
            return {
                "success": True,
                "dados": dados_lista,
                "stats": stats,
                "filtros_aplicados": filtros_aplicados if filtros_aplicados else None,
                "description": f"Geração de usinas não simuladas: {len(resultado_df)} registro(s) do SISTEMA.DAT",
                "tool": self.get_name()
            }
            
        except FileNotFoundError as e:
            print(f"[TOOL] ❌ Erro FileNotFoundError: {e}")
            return {
                "success": False,
                "error": f"Arquivo não encontrado: {str(e)}",
                "tool": self.get_name()
            }
        except Exception as e:
            print(f"[TOOL] ❌ Erro ao processar: {type(e).__name__}: {e}")
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
        return """
        Geração de usinas não simuladas. Dados de geração de pequenas usinas não simuladas por fonte e período do arquivo SISTEMA.DAT.
        
        Queries que ativam esta tool:
        - "usinas não simuladas"
        - "geração de usinas não simuladas"
        - "usinas não simuladas do subsistema 1"
        - "geração não simulada do bloco 2"
        - "usinas não simuladas da fonte eólica"
        - "geração não simulada em 2023"
        - "pequenas usinas"
        - "bloco de usinas não simuladas"
        - "valores mensais de UFV MMGD"
        - "valores mensais de PCH"
        - "valores mensais de PCT"
        - "carga de EOL MMGD"
        - "geração mensal de UFV"
        - "valores mensais de PCH MMGD do subsistema 1"
        
        Esta tool consulta o arquivo SISTEMA.DAT e retorna informações sobre geração de usinas não simuladas, incluindo:
        - Código do submercado
        - Índice do bloco de usinas
        - Fonte/tecnologia (descrição do bloco)
        - Data/período (mensal)
        - Valor (geração em MWmédio)
        
        A tool permite filtrar por:
        - Submercado específico (código ou nome)
        - Bloco específico (índice)
        - Fonte/tecnologia (PCH, PCT, EOL, UFV, MMGD, PCH MMGD, PCT MMGD, EOL MMGD, UFV MMGD)
        - Período (ano e/ou mês)
        
        Fontes suportadas:
        - PCH (Pequenas Centrais Hidrelétricas)
        - PCT (Pequenas Centrais Termelétricas)
        - EOL (Eólica)
        - UFV (Usinas Fotovoltaicas)
        - MMGD (Micro e Minigeração Distribuída)
        - Combinações: PCH MMGD, PCT MMGD, EOL MMGD, UFV MMGD
        
        A tool retorna valores mensais para cada fonte, permitindo consultas como:
        - "valores mensais de UFV MMGD" → retorna todos os meses de todos os anos para UFV MMGD
        - "valores mensais de PCH em 2026" → retorna os 12 meses de 2026 para PCH
        - "valores mensais de PCT do subsistema 1" → retorna todos os meses de PCT do subsistema 1
        
        Comportamento de queries genéricas:
        - "carga de EOL" → retorna TODOS os registros de EOL (incluindo "EOL" e "EOL MMGD") de todos os submercados e blocos
        - "geração de PCH" → retorna TODOS os registros de PCH (incluindo "PCH" e "PCH MMGD") de todos os submercados e blocos
        - "valores mensais de UFV" → retorna TODOS os registros de UFV (incluindo "UFV" e "UFV MMGD") de todos os submercados e blocos
        
        Para buscar uma fonte específica com MMGD, mencione explicitamente:
        - "carga de EOL MMGD" → retorna apenas registros de "EOL MMGD"
        - "valores mensais de PCH MMGD" → retorna apenas registros de "PCH MMGD"
        
        A geração das usinas não simuladas é subtraída do mercado antes do cálculo da operação.
        Pode haver múltiplos blocos de usinas não simuladas por subsistema.
        
        Termos-chave: usinas não simuladas, geração não simulada, pequenas usinas, bloco usinas, fonte geração, tecnologia geração, valores mensais, carga mensal, geração mensal, PCH, PCT, EOL, UFV, MMGD.
        """


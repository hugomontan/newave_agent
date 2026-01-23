"""
Tool para consultar cargas e ofertas adicionais do C_ADIC.DAT.
Valores positivos = cargas adicionais (aumentam demanda)
Valores negativos = ofertas adicionais (reduzem demanda)
"""
from newave_agent.app.tools.base import NEWAVETool
from inewave.newave import Cadic, Sistema
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from newave_agent.app.config import debug_print, safe_print

class CadicTool(NEWAVETool):
    """
    Tool para consultar cargas e ofertas adicionais por subsistema.
    """
    
    def get_name(self) -> str:
        return "CadicTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre cargas/ofertas adicionais.
        Usa termos distintivos para evitar conflito com CargaMensalTool.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        
        # Termos que indicam que NÃO é sobre Cadic (evitar conflito com CargaMensalTool)
        termos_exclusivos_carga_principal = [
            "mercado energia",  # Específico de SISTEMA.DAT
            "demanda principal",  # Específico de demanda base
            "demanda base",
        ]
        if any(t in query_lower for t in termos_exclusivos_carga_principal):
            return False  # Deixa para CargaMensalTool
        
        # Keywords distintivos para Cadic
        keywords = [
            "cadic", "c_adic",  # Nome do arquivo (mais específico)
            "carga adicional", "cargas adicionais",
            "oferta adicional", "ofertas adicionais",
            "carga extra", "cargas extras",
            "oferta extra", "ofertas extras",
            "demanda adicional",  # Com "adicional" é distintivo
            "demandas adicionais",
            "carga adicional submercado",
            "oferta adicional subsistema",
            "cargas extras submercado",
            "ofertas extras subsistema",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_subsistema_from_query(self, query: str, cadic: Cadic, sistema: Sistema = None) -> Optional[int]:
        """
        Extrai código do subsistema da query.
        Similar ao método de CargaMensalTool.
        
        Args:
            query: Query do usuário
            cadic: Objeto Cadic já lido
            sistema: Objeto Sistema (opcional, para obter lista de subsistemas)
            
        Returns:
            Código do subsistema ou None se não encontrado
        """
        query_lower = query.lower()
        
        # Obter lista de subsistemas disponíveis
        subsistemas_disponiveis = []
        
        # Tentar obter do cadic primeiro
        if cadic.cargas is not None and len(cadic.cargas) > 0:
            subsistemas_unicos = cadic.cargas[['codigo_submercado', 'nome_submercado']].drop_duplicates()
            for _, row in subsistemas_unicos.iterrows():
                subsistemas_disponiveis.append({
                    'codigo': int(row.get('codigo_submercado')),
                    'nome': str(row.get('nome_submercado', '')).strip()
                })
        
        # Se não encontrou ou lista vazia, tentar do Sistema
        if not subsistemas_disponiveis and sistema is not None:
            if sistema.custo_deficit is not None:
                df_custo = sistema.custo_deficit
                subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
                for _, row in subsistemas_unicos.iterrows():
                    subsistemas_disponiveis.append({
                        'codigo': int(row.get('codigo_submercado')),
                        'nome': str(row.get('nome_submercado', '')).strip()
                    })
        
        if not subsistemas_disponiveis:
            debug_print("[TOOL] ⚠️ Nenhum subsistema disponível para busca")
            return None
        
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
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico: \"{nome_sub}\"")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome
        subsistemas_ordenados = sorted(subsistemas_disponiveis, key=lambda x: len(x['nome']), reverse=True)
        
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                debug_print(f"[TOOL] ✅ Código {codigo_sub} encontrado por nome completo '{nome_sub}'")
                return codigo_sub
            
            # Verificar palavras-chave
            palavras_nome = nome_sub_lower.split()
            palavras_comuns = ['do', 'da', 'de', 'para', 'por', 'com', 'sem', 'em', 'na', 'no']
            for palavra in palavras_nome:
                if len(palavra) >= 3 and palavra not in palavras_comuns and palavra in query_lower:
                    debug_print(f"[TOOL] ✅ Código {codigo_sub} encontrado por palavra '{palavra}' do nome '{nome_sub}'")
                    return codigo_sub
        
        debug_print("[TOOL] ⚠️ Nenhum subsistema específico detectado na query")
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
        
        # Extrair ano (4 dígitos)
        ano_match = re.search(r'\b(19|20)\d{2}\b', query)
        if ano_match:
            periodo['ano'] = int(ano_match.group())
        
        # Extrair mês (nome ou número)
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
        
        # Tentar extrair número de mês (1-12)
        if 'mes' not in periodo:
            mes_num_match = re.search(r'\b(0?[1-9]|1[0-2])\b', query)
            if mes_num_match and 'ano' in periodo:  # Só considerar se já tem ano
                periodo['mes'] = int(mes_num_match.group())
        
        return periodo if periodo else None
    
    def _extract_razao_from_query(self, query: str, cadic: Cadic) -> Optional[str]:
        """
        Extrai razão (ANDE, CONS.ITAIPU, MMGD SE, etc.) da query.
        
        Args:
            query: Query do usuário
            cadic: Objeto Cadic já lido
            
        Returns:
            Razão encontrada ou None
        """
        query_lower = query.lower()
        
        # Obter lista de razões disponíveis no DataFrame
        razoes_disponiveis = []
        if cadic.cargas is not None and len(cadic.cargas) > 0:
            if 'razao' in cadic.cargas.columns:
                razoes_unicas = cadic.cargas['razao'].dropna().unique()
                for razao in razoes_unicas:
                    razao_str = str(razao).strip()
                    if razao_str:
                        razoes_disponiveis.append(razao_str)
        
        if not razoes_disponiveis:
            debug_print("[TOOL] ⚠️ Nenhuma razão disponível para busca")
            return None
        
        debug_print(f"[TOOL] Razões disponíveis no arquivo: {razoes_disponiveis}")
        
        # Buscar por match exato ou parcial
        for razao in razoes_disponiveis:
            razao_lower = razao.lower()
            
            # Match exato (case-insensitive)
            if razao_lower in query_lower:
                debug_print(f"[TOOL] ✅ Razão '{razao}' encontrada na query (match exato)")
                return razao
            
            # Match parcial (para "ande" encontrar "ANDE", "cons.itaipu" encontrar "CONS.ITAIPU", etc.)
            # Remover pontuação e split por espaços/pontos
            palavras_razao = razao_lower.replace('.', ' ').replace('-', ' ').replace('_', ' ').split()
            for palavra in palavras_razao:
                if len(palavra) >= 3 and palavra in query_lower:
                    # Verificar se não é palavra muito comum
                    palavras_comuns = ['de', 'da', 'do', 'para', 'por', 'com', 'sem', 'em', 'na', 'no', 'se']
                    if palavra not in palavras_comuns:
                        debug_print(f"[TOOL] ✅ Razão '{razao}' encontrada por palavra '{palavra}' na query")
                        return razao
        
        debug_print("[TOOL] ⚠️ Nenhuma razão específica detectada na query")
        return None
    
    def _extract_tipo_carga(self, query: str) -> Optional[str]:
        """
        Identifica se pede cargas (positivas) ou ofertas (negativas).
        
        Args:
            query: Query do usuário
            
        Returns:
            "carga", "oferta", ou None (ambos)
        """
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["carga adicional", "cargas adicionais", "carga extra", "demanda adicional"]):
            return "carga"
        elif any(kw in query_lower for kw in ["oferta adicional", "ofertas adicionais", "oferta extra", "ofertas extras"]):
            return "oferta"
        
        return None  # Ambos
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de cargas/ofertas adicionais.
        
        Fluxo:
        1. Verifica existência do C_ADIC.DAT
        2. Lê com inewave (Cadic.read())
        3. Acessa propriedade cargas (DataFrame)
        4. Aplica filtros (subsistema, período, tipo)
        5. Processa e retorna dados
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo C_ADIC.DAT...")
            cadic_path = os.path.join(self.deck_path, "C_ADIC.DAT")
            
            if not os.path.exists(cadic_path):
                cadic_path = os.path.join(self.deck_path, "c_adic.dat")
            
            if not os.path.exists(cadic_path):
                safe_print(f"[TOOL] ❌ Arquivo C_ADIC.DAT não encontrado")
                return {
                    "success": False,
                    "error": f"Arquivo C_ADIC.DAT não encontrado em {self.deck_path}",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {cadic_path}")
            
            # ETAPA 2: Ler arquivo
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            cadic = Cadic.read(cadic_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            if cadic.cargas is None or len(cadic.cargas) == 0:
                debug_print("[TOOL] ⚠️ DataFrame de cargas vazio ou None")
                return {
                    "success": False,
                    "error": "Nenhuma carga adicional encontrada no arquivo C_ADIC.DAT",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ DataFrame obtido: {len(cadic.cargas)} registros")
            debug_print(f"[TOOL] Colunas: {list(cadic.cargas.columns)}")
            
            # ETAPA 4: Ler Sistema.DAT para obter lista de subsistemas (para busca por nome)
            sistema = None
            try:
                sistema_path = os.path.join(self.deck_path, "SISTEMA.DAT")
                if not os.path.exists(sistema_path):
                    sistema_path = os.path.join(self.deck_path, "sistema.dat")
                if os.path.exists(sistema_path):
                    sistema = Sistema.read(sistema_path)
                    debug_print("[TOOL] ✅ SISTEMA.DAT lido para auxiliar busca de subsistemas")
            except Exception as e:
                debug_print(f"[TOOL] ⚠️ Não foi possível ler SISTEMA.DAT: {e}")
            
            # ETAPA 5: Extrair filtros da query
            debug_print("[TOOL] ETAPA 5: Extraindo filtros da query...")
            df = cadic.cargas.copy()
            
            # Extrair todos os filtros
            razao = self._extract_razao_from_query(query, cadic)
            codigo_subsistema = self._extract_subsistema_from_query(query, cadic, sistema)
            periodo = self._extract_periodo_from_query(query)
            tipo_carga = self._extract_tipo_carga(query)
            
            # Aplicar filtro de razão primeiro (mais específico)
            if razao is not None:
                debug_print(f"[TOOL] ✅ Filtro por razão: {razao}")
                df = df[df['razao'] == razao]
            
            if codigo_subsistema is not None:
                debug_print(f"[TOOL] ✅ Filtro por subsistema: {codigo_subsistema}")
                df = df[df['codigo_submercado'] == codigo_subsistema]
            
            if periodo:
                debug_print(f"[TOOL] ✅ Filtro por período: {periodo}")
                if 'ano' in periodo:
                    # Extrair ano da coluna data
                    if 'data' in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df['data']):
                            df = df[df['data'].dt.year == periodo['ano']]
                        else:
                            df['data'] = pd.to_datetime(df['data'], errors='coerce')
                            df = df[df['data'].dt.year == periodo['ano']]
                    elif 'ano' in df.columns:
                        df = df[df['ano'] == periodo['ano']]
                
                if 'mes' in periodo:
                    if 'data' in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df['data']):
                            df = df[df['data'].dt.month == periodo['mes']]
                    elif 'mes' in df.columns:
                        df = df[df['mes'] == periodo['mes']]
            
            if tipo_carga == "carga":
                debug_print("[TOOL] ✅ Filtro: apenas cargas adicionais (valores positivos)")
                df = df[df['valor'] > 0]
            elif tipo_carga == "oferta":
                debug_print("[TOOL] ✅ Filtro: apenas ofertas adicionais (valores negativos)")
                df = df[df['valor'] < 0]
            
            if df.empty:
                return {
                    "success": False,
                    "error": "Nenhum dado encontrado após aplicar os filtros",
                    "tool": self.get_name()
                }
            
            debug_print(f"[TOOL] ✅ {len(df)} registros após aplicar filtros")
            
            # ETAPA 6: Processar dados
            debug_print("[TOOL] ETAPA 6: Processando dados...")
            
            # Criar colunas auxiliares se necessário
            # PRIMEIRO: Verificar se data é datetime, se não, converter (igual CargaMensalTool)
            if 'data' in df.columns:
                if not pd.api.types.is_datetime64_any_dtype(df['data']):
                    debug_print("[TOOL] ⚠️ Coluna 'data' não é datetime, tentando converter...")
                    try:
                        df['data'] = pd.to_datetime(df['data'], errors='coerce')
                        debug_print("[TOOL] ✅ Coluna 'data' convertida para datetime")
                    except Exception as e:
                        debug_print(f"[TOOL] ⚠️ Não foi possível converter 'data' para datetime: {e}")
                
                # Agora criar ano e mes se data for datetime
                if pd.api.types.is_datetime64_any_dtype(df['data']):
                    df['ano'] = df['data'].dt.year
                    df['mes'] = df['data'].dt.month
                    debug_print("[TOOL] ✅ Colunas auxiliares criadas a partir de 'data'")
            
            # Converter para lista de dicts
            dados = df.to_dict(orient="records")
            
            # Limpar NaN values e converter tipos
            for record in dados:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    # Converter numpy.int64 para int Python nativo (importante para JSON)
                    elif hasattr(value, 'item'):  # numpy types têm método item()
                        try:
                            record[key] = value.item()
                        except (ValueError, AttributeError):
                            pass
            
            # ETAPA 7: Calcular estatísticas
            debug_print("[TOOL] ETAPA 7: Calculando estatísticas...")
            
            summary = {
                'total_registros': len(df),
                'subsistemas': df['codigo_submercado'].nunique() if 'codigo_submercado' in df.columns else 0,
                'total_cargas_positivas': float(df[df['valor'] > 0]['valor'].sum()) if len(df[df['valor'] > 0]) > 0 else 0.0,
                'total_ofertas_negativas': float(df[df['valor'] < 0]['valor'].sum()) if len(df[df['valor'] < 0]) > 0 else 0.0,
                'carga_media': float(df[df['valor'] > 0]['valor'].mean()) if len(df[df['valor'] > 0]) > 0 else None,
                'oferta_media': float(df[df['valor'] < 0]['valor'].mean()) if len(df[df['valor'] < 0]) > 0 else None,
            }
            
            # Período coberto
            if 'ano' in df.columns:
                anos = sorted(df['ano'].unique().tolist())
                summary['periodo_coberto'] = {
                    'ano_inicio': int(min(anos)) if anos else None,
                    'ano_fim': int(max(anos)) if anos else None,
                    'anos': anos
                }
            elif 'data' in df.columns and pd.api.types.is_datetime64_any_dtype(df['data']):
                anos = sorted(df['data'].dt.year.unique().tolist())
                summary['periodo_coberto'] = {
                    'ano_inicio': int(min(anos)) if anos else None,
                    'ano_fim': int(max(anos)) if anos else None,
                    'anos': anos
                }
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if razao is not None:
                filtro_info['razao'] = razao
            if codigo_subsistema is not None:
                nome_sub = None
                if cadic.cargas is not None:
                    subsistema_info = cadic.cargas[cadic.cargas['codigo_submercado'] == codigo_subsistema]
                    if not subsistema_info.empty:
                        nome_sub = subsistema_info.iloc[0].get('nome_submercado', f'Subsistema {codigo_subsistema}')
                filtro_info['subsistema'] = {
                    'codigo': codigo_subsistema,
                    'nome': nome_sub
                }
            if periodo:
                filtro_info['periodo'] = periodo
            if tipo_carga:
                filtro_info['tipo'] = tipo_carga
            
            debug_print(f"[TOOL] ✅ Processamento concluído: {len(dados)} registros formatados")
            
            return {
                "success": True,
                "data": dados,
                "summary": summary,
                "filtros": filtro_info if filtro_info else None,
                "description": "Cargas e ofertas adicionais (valores extras somados/subtraídos da demanda principal) em MWmédio",
                "columns": list(df.columns),
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
                "error": f"Erro ao processar C_ADIC.DAT: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """
        Retorna descrição para semantic matching.
        """
        return """
        Cargas e ofertas adicionais do arquivo C_ADIC.DAT. Valores extras somados ou subtraídos da demanda principal do sistema.
        
        IMPORTANTE: NÃO confundir com carga mensal principal (demanda base do sistema do SISTEMA.DAT).
        
        Cargas adicionais são valores POSITIVOS que AUMENTAM a demanda (somadas ao mercado).
        Ofertas adicionais são valores NEGATIVOS que REDUZEM a demanda (abatidas do mercado).
        
        Queries específicas:
        - "cargas adicionais por submercado"
        - "ofertas adicionais do subsistema"
        - "carga adicional do Sudeste"
        - "oferta adicional do Sul"
        - "cargas extras do submercado"
        - "ofertas extras"
        - "demanda adicional do subsistema"
        - "carga adicional do subsistema 1"
        - "oferta adicional do subsistema 2"
        - "cargas adicionais de 2023"
        - "ofertas adicionais em janeiro de 2024"
        - "valores extras de carga"
        - "dados do C_ADIC"
        - "cadic"
        - "carga adicional de ANDE"
        - "carga adicional de CONS.ITAIPU"
        - "carga adicional de MMGD SE"
        - "qual a carga adicional de ande"
        - "cargas adicionais de itaipu"
        - "ofertas adicionais por razão"
        - "ANDE"
        
        Termos-chave: cadic, c_adic, carga adicional, cargas adicionais, oferta adicional, ofertas adicionais, carga extra, ofertas extras, demanda adicional, valores extras, razão, ANDE, CONS.ITAIPU, MMGD.
        
        Unidade: MWmédio (megawatts médios).
        """


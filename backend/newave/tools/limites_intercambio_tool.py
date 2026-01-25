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
    
    def _extract_submercados_from_query(self, query: str, sistema: Sistema) -> tuple:
        """
        Extrai códigos dos submercados de origem e destino da query.
        
        Args:
            query: Query do usuário
            sistema: Objeto Sistema já lido
            
        Returns:
            Tupla (submercado_de, submercado_para) ou (None, None) se não encontrado
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
                        debug_print(f"[TOOL] ✅ Códigos {sub_de} → {sub_para} encontrados por padrão numérico")
                        return (sub_de, sub_para)
                except (ValueError, IndexError):
                    continue
        
        # ETAPA 2: Buscar por nomes de submercados
        # Ordenar por tamanho do nome (mais específico primeiro)
        subsistemas_ordenados = sorted(subsistemas_disponiveis, key=lambda x: len(x['nome']), reverse=True)
        
        sub_de = None
        sub_para = None
        
        # Padrão especial: "entre X e Y" (ex: "entre sudeste e norte")
        pattern_entre = re.search(r'entre\s+([^e]+?)\s+e\s+([^e]+?)(?:\s|$|,|\.)', query_lower)
        if pattern_entre:
            nome_1 = pattern_entre.group(1).strip()
            nome_2 = pattern_entre.group(2).strip()
            
            # Buscar submercados que correspondem aos nomes
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_1:
                    sub_de = subsistema['codigo']
                    debug_print(f"[TOOL] ✅ Código {sub_de} encontrado como origem (padrão 'entre X e Y'): '{subsistema['nome']}'")
                    break
            
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_2:
                    if subsistema['codigo'] != sub_de:
                        sub_para = subsistema['codigo']
                        debug_print(f"[TOOL] ✅ Código {sub_para} encontrado como destino (padrão 'entre X e Y'): '{subsistema['nome']}'")
                        break
            
            if sub_de is not None and sub_para is not None:
                return (sub_de, sub_para)
        
        # Padrão: "X para Y" ou "X → Y"
        # Buscar primeiro submercado (origem)
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                # Verificar se não é o segundo submercado (depois de "para", "→", etc)
                pos_nome = query_lower.find(nome_sub_lower)
                pos_para = query_lower.find(' para ', pos_nome)
                pos_arrow = query_lower.find(' → ', pos_nome)
                
                if pos_para == -1 and pos_arrow == -1:
                    sub_de = codigo_sub
                    debug_print(f"[TOOL] ✅ Código {codigo_sub} encontrado como origem: '{nome_sub}'")
                    break
        
        # Buscar segundo submercado (destino)
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                # Verificar se está depois de "para", "→", etc
                pos_para = query_lower.find(' para ')
                pos_arrow = query_lower.find(' → ')
                pos_nome = query_lower.find(nome_sub_lower)
                
                if (pos_para != -1 and pos_nome > pos_para) or (pos_arrow != -1 and pos_nome > pos_arrow):
                    if codigo_sub != sub_de:  # Não pode ser o mesmo
                        sub_para = codigo_sub
                        debug_print(f"[TOOL] ✅ Código {codigo_sub} encontrado como destino: '{nome_sub}'")
                        break
        
        if sub_de is not None and sub_para is not None:
            return (sub_de, sub_para)
        
        # Se encontrou apenas um, retornar None (precisa de par)
        if sub_de is not None or sub_para is not None:
            debug_print("[TOOL] ⚠️ Apenas um submercado identificado, mas intercâmbio requer par")
        
        debug_print("[TOOL] ⚠️ Nenhum par de submercados específico detectado na query")
        return (None, None)
    
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
            submercado_de, submercado_para = self._extract_submercados_from_query(query, sistema)
            
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
            
            if submercado_de is not None:
                df_filtrado = df_filtrado[df_filtrado['submercado_de'] == submercado_de]
                debug_print(f"[TOOL] ✅ Filtrado por submercado de origem: {submercado_de}")
            
            if submercado_para is not None:
                df_filtrado = df_filtrado[df_filtrado['submercado_para'] == submercado_para]
                debug_print(f"[TOOL] ✅ Filtrado por submercado de destino: {submercado_para}")
            
            if filtro_sentido is not None:
                df_filtrado = df_filtrado[df_filtrado['sentido'] == filtro_sentido]
                debug_print(f"[TOOL] ✅ Filtrado por sentido: {filtro_sentido}")
            
            if df_filtrado.empty:
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
            
            # Estatísticas por par de submercados
            stats_por_par = []
            for _, row in pares_submercados.iterrows():
                sub_de = int(row['submercado_de'])
                sub_para = int(row['submercado_para'])
                df_par = df_filtrado[
                    (df_filtrado['submercado_de'] == sub_de) & 
                    (df_filtrado['submercado_para'] == sub_para)
                ]
                
                if len(df_par) > 0:
                    stats_por_par.append({
                        'submercado_de': sub_de,
                        'submercado_para': sub_para,
                        'nome_de': nomes_submercados.get(sub_de, f'Subsistema {sub_de}'),
                        'nome_para': nomes_submercados.get(sub_para, f'Subsistema {sub_para}'),
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
        return """
        Limites de intercâmbio entre subsistemas. Capacidade de interligação entre submercados. Intercâmbio mínimo obrigatório. Limites máximos de intercâmbio.
        
        Queries que ativam esta tool:
        - "quais são os limites de intercâmbio entre subsistemas"
        - "limites de intercâmbio"
        - "limite de intercâmbio entre Sudeste e Sul"
        - "limite de intercâmbio entre subsistema 1 e subsistema 2"
        - "capacidade de intercâmbio"
        - "intercâmbio mínimo obrigatório"
        - "limite máximo de intercâmbio"
        - "limites entre submercados"
        - "capacidade de interligação"
        - "intercâmbio de 1 para 2"
        - "intercâmbio entre Nordeste e Sudeste"
        - "limites de intercâmbio do Sudeste para o Sul"
        - "capacidade de intercâmbio entre sistemas"
        - "limite de interligação"
        - "intercâmbio entre subsistemas"
        
        Termos-chave: limite de intercâmbio, limites de intercâmbio, intercâmbio entre, capacidade de intercâmbio, intercâmbio mínimo, intercâmbio máximo, capacidade de interligação, limite de interligação, intercâmbio entre subsistemas, intercâmbio entre submercados.
        """


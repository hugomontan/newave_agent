"""
Tool para consultar desvios de água para usos consuntivos do DSVAGUA.DAT.
Acessa dados de desvios de água por usina e estágio.
"""
from app.tools.base import NEWAVETool
from inewave.newave import Dsvagua, Confhd
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from datetime import datetime
from difflib import SequenceMatcher


class DsvaguaTool(NEWAVETool):
    """
    Tool para consultar desvios de água para usos consuntivos do DSVAGUA.DAT.
    
    Dados disponíveis:
    - Código da usina
    - Data (estágio)
    - Valor do desvio
    - Considera desvio de usina NC (não considerada)
    - Comentários
    """
    
    def __init__(self, deck_path: str):
        super().__init__(deck_path)
        
        # Cache do mapeamento (carregado lazy)
        self._mapeamento_codigo_nome: Optional[Dict[int, str]] = None
        self._mapeamento_nome_codigo: Optional[Dict[str, int]] = None
    
    def get_name(self) -> str:
        return "DsvaguaTool"
    
    def _carregar_mapeamento_usinas(self) -> Dict[int, str]:
        """
        Carrega o mapeamento código_usina → nome_usina do CONFHD.DAT.
        
        Returns:
            Dicionário {codigo_usina: nome_usina}
        """
        # Se já foi carregado, retornar cache
        if self._mapeamento_codigo_nome is not None:
            return self._mapeamento_codigo_nome
        
        print("[TOOL] Carregando mapeamento código → nome do CONFHD.DAT...")
        
        # Tentar encontrar CONFHD.DAT
        confhd_path = os.path.join(self.deck_path, "CONFHD.DAT")
        if not os.path.exists(confhd_path):
            confhd_path = os.path.join(self.deck_path, "confhd.dat")
        
        if not os.path.exists(confhd_path):
            print("[TOOL] ⚠️ CONFHD.DAT não encontrado - consultas por nome de usina não funcionarão")
            self._mapeamento_codigo_nome = {}
            self._mapeamento_nome_codigo = {}
            return self._mapeamento_codigo_nome
        
        try:
            confhd = Confhd.read(confhd_path)
            
            if confhd.usinas is None or confhd.usinas.empty:
                print("[TOOL] ⚠️ Nenhuma usina encontrada no CONFHD.DAT")
                self._mapeamento_codigo_nome = {}
                self._mapeamento_nome_codigo = {}
                return self._mapeamento_codigo_nome
            
            # Criar mapeamento
            mapeamento_codigo_nome = {}
            mapeamento_nome_codigo = {}
            
            for _, row in confhd.usinas.iterrows():
                codigo = int(row.get('codigo_usina', 0))
                nome = str(row.get('nome_usina', '')).strip()
                
                if nome and codigo > 0:
                    mapeamento_codigo_nome[codigo] = nome
                    nome_upper = nome.upper()
                    mapeamento_nome_codigo[nome_upper] = codigo
            
            self._mapeamento_codigo_nome = mapeamento_codigo_nome
            self._mapeamento_nome_codigo = mapeamento_nome_codigo
            
            print(f"[TOOL] ✅ Mapeamento carregado: {len(mapeamento_codigo_nome)} usinas mapeadas")
            
            return mapeamento_codigo_nome
            
        except Exception as e:
            print(f"[TOOL] ⚠️ Erro ao carregar mapeamento: {e}")
            self._mapeamento_codigo_nome = {}
            self._mapeamento_nome_codigo = {}
            return self._mapeamento_codigo_nome
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre desvios de água.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "dsvagua",
            "dsvagua.dat",
            "desvio de água",
            "desvio de agua",
            "desvios de água",
            "desvios de agua",
            "uso consuntivo",
            "usos consuntivos",
            "desvio água usina",
            "desvio agua usina",
            "água consuntiva",
            "agua consuntiva",
            "diversão de água",
            "diversao de agua",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_usina_from_query(self, query: str, dsvagua: Dsvagua) -> Optional[int]:
        """
        Extrai código da usina da query.
        Busca por código numérico ou nome da usina.
        
        Args:
            query: Query do usuário
            dsvagua: Objeto Dsvagua já lido
            
        Returns:
            Código da usina ou None
        """
        query_lower = query.lower()
        
        # Verificar se há desvios
        desvios_df = dsvagua.desvios
        if desvios_df is None or desvios_df.empty:
            return None
        
        # ETAPA 1: Tentar extrair número explícito
        patterns = [
            r'usina\s*(\d+)',
            r'código\s*(\d+)',
            r'codigo\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    codigo = int(match.group(1))
                    # Verificar se código existe nos desvios
                    if codigo in desvios_df['codigo_usina'].values:
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico")
                        return codigo
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome da usina usando mapeamento do CONFHD
        print(f"[TOOL] Buscando usina por nome na query: '{query}'")
        
        # Carregar mapeamento
        mapeamento_codigo_nome = self._carregar_mapeamento_usinas()
        mapeamento_nome_codigo = self._mapeamento_nome_codigo
        
        if not mapeamento_nome_codigo:
            print("[TOOL] ⚠️ Mapeamento de nomes não disponível")
            return None
        
        # Palavras comuns a ignorar
        palavras_ignorar = {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'na', 'no', 'nas', 'nos', 'a', 'à', 'ao', 'aos', 'desvios', 'desvio', 'água', 'agua', 'consuntivo', 'consuntivos'}
        
        # Extrair palavras significativas da query
        palavras_query = [p for p in query_lower.split() if len(p) > 2 and p not in palavras_ignorar]
        print(f"[TOOL] Palavras significativas extraídas da query: {palavras_query}")
        
        # Lista todas as usinas disponíveis (que têm desvios)
        codigos_com_desvios = set(desvios_df['codigo_usina'].unique())
        usinas_list = []
        
        for codigo, nome in mapeamento_codigo_nome.items():
            if codigo in codigos_com_desvios:
                usinas_list.append({'codigo': codigo, 'nome': nome})
                print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
        
        if not usinas_list:
            print("[TOOL] ⚠️ Nenhuma usina com nome encontrada")
            return None
        
        # Ordenar por tamanho do nome (maior primeiro) para priorizar matches mais específicos
        usinas_sorted = sorted(usinas_list, key=lambda x: len(x['nome']), reverse=True)
        
        # ETAPA 2.1: Buscar match exato do nome completo (prioridade máxima)
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Match exato do nome completo
            if nome_usina_lower == query_lower.strip():
                print(f"[TOOL] ✅ Código {codigo_usina} encontrado por match exato '{nome_usina}'")
                return codigo_usina
            
            # Match exato do nome completo dentro da query (como palavra completa)
            if len(nome_usina_lower) >= 4:  # Nomes com pelo menos 4 caracteres
                pattern = r'\b' + re.escape(nome_usina_lower) + r'\b'
                if re.search(pattern, query_lower):
                    print(f"[TOOL] ✅ Código {codigo_usina} encontrado por nome completo '{nome_usina}' na query")
                    return codigo_usina
        
        # ETAPA 2.2: Buscar por similaridade e palavras-chave
        candidatos = []
        
        for usina in usinas_sorted:
            codigo_usina = usina['codigo']
            nome_usina = usina['nome']
            nome_usina_lower = nome_usina.lower().strip()
            
            if not nome_usina_lower:
                continue
            
            # Extrair palavras significativas do nome da usina
            palavras_nome = [p for p in nome_usina_lower.split() if len(p) > 2 and p not in palavras_ignorar]
            
            # PRIORIDADE 3: Match exato de todas as palavras significativas
            if palavras_nome and all(palavra in query_lower for palavra in palavras_nome):
                print(f"[TOOL] ✅ Código {codigo_usina} encontrado: todas as palavras significativas de '{nome_usina}' estão na query")
                return codigo_usina
            
            # PRIORIDADE 4: Similaridade de string
            similarity = SequenceMatcher(None, query_lower, nome_usina_lower).ratio()
            if similarity > 0.6:  # 60% de similaridade
                candidatos.append({
                    'codigo': codigo_usina,
                    'nome': nome_usina,
                    'score': similarity,
                    'tipo': 'similarity'
                })
            
            # PRIORIDADE 5: Contagem de palavras significativas em comum
            palavras_comuns = set(palavras_query) & set(palavras_nome)
            if palavras_comuns:
                # Requer pelo menos 2 palavras em comum OU uma palavra longa (>= 5 chars)
                palavras_longas = [p for p in palavras_comuns if len(p) >= 5]
                if len(palavras_comuns) >= 2 or (len(palavras_longas) >= 1 and len(palavras_comuns) >= 1):
                    score = len(palavras_comuns) / max(len(palavras_nome), 1)
                    candidatos.append({
                        'codigo': codigo_usina,
                        'nome': nome_usina,
                        'score': score,
                        'tipo': 'palavras_comuns'
                    })
        
        # Se encontrou candidatos, retornar o melhor
        if candidatos:
            # Ordenar por tipo (similarity primeiro) e depois por score
            candidatos.sort(key=lambda x: (x['tipo'] == 'similarity', x['score']), reverse=True)
            melhor = candidatos[0]
            print(f"[TOOL] ✅ Código {melhor['codigo']} encontrado por {melhor['tipo']} (score: {melhor['score']:.2f}): '{melhor['nome']}'")
            return melhor['codigo']
        
        print("[TOOL] ⚠️ Nenhuma usina específica detectada na query")
        return None
    
    def _extract_periodo_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Extrai período (data) da query.
        
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
    
    def _format_desvio_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Formata os dados de um desvio.
        
        Args:
            row: Linha do DataFrame
            
        Returns:
            Dicionário formatado
        """
        dados = {
            'codigo_usina': int(row.get('codigo_usina', 0)) if pd.notna(row.get('codigo_usina')) else None,
            'valor': float(row.get('valor', 0)) if pd.notna(row.get('valor')) else None,
            'considera_desvio_usina_NC': int(row.get('considera_desvio_usina_NC', 0)) if pd.notna(row.get('considera_desvio_usina_NC')) else None,
            'comentario': str(row.get('comentario', '')).strip() if pd.notna(row.get('comentario')) else None,
        }
        
        # Formatar data
        data_val = row.get('data')
        if pd.notna(data_val):
            if isinstance(data_val, pd.Timestamp):
                dados['data'] = data_val.isoformat()
                dados['ano'] = data_val.year
                dados['mes'] = data_val.month
                dados['dia'] = data_val.day
            elif hasattr(data_val, 'isoformat'):
                dados['data'] = data_val.isoformat()
            else:
                dados['data'] = str(data_val)
        else:
            dados['data'] = None
        
        return dados
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de desvios de água.
        
        Fluxo:
        1. Verifica se DSVAGUA.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica filtros (usina, período)
        4. Retorna dados filtrados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo DSVAGUA.DAT...")
            dsvagua_path = os.path.join(self.deck_path, "DSVAGUA.DAT")
            
            if not os.path.exists(dsvagua_path):
                dsvagua_path = os.path.join(self.deck_path, "dsvagua.dat")
                if not os.path.exists(dsvagua_path):
                    print(f"[TOOL] ❌ Arquivo DSVAGUA.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo DSVAGUA.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {dsvagua_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            dsvagua = Dsvagua.read(dsvagua_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se há dados
            desvios_df = dsvagua.desvios
            if desvios_df is None or desvios_df.empty:
                print("[TOOL] ⚠️ Nenhum desvio encontrado")
                return {
                    "success": False,
                    "error": "Nenhum desvio de água encontrado no arquivo DSVAGUA.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ {len(desvios_df)} registro(s) de desvio encontrado(s)")
            
            # ETAPA 4: Identificar filtros
            print("[TOOL] ETAPA 4: Identificando filtros...")
            codigo_usina = self._extract_usina_from_query(query, dsvagua)
            periodo = self._extract_periodo_from_query(query)
            
            if codigo_usina is not None:
                print(f"[TOOL] ✅ Filtro por usina: {codigo_usina}")
            
            if periodo is not None:
                print(f"[TOOL] ✅ Filtro por período: {periodo}")
            
            # ETAPA 5: Aplicar filtros
            print("[TOOL] ETAPA 5: Aplicando filtros...")
            resultado_df = desvios_df.copy()
            
            if codigo_usina is not None:
                resultado_df = resultado_df[resultado_df['codigo_usina'] == codigo_usina]
            
            if periodo is not None:
                if 'data' in resultado_df.columns:
                    if 'ano' in periodo:
                        if pd.api.types.is_datetime64_any_dtype(resultado_df['data']):
                            resultado_df = resultado_df[resultado_df['data'].dt.year == periodo['ano']]
                    
                    if 'mes' in periodo:
                        if pd.api.types.is_datetime64_any_dtype(resultado_df['data']):
                            resultado_df = resultado_df[resultado_df['data'].dt.month == periodo['mes']]
            
            print(f"[TOOL] ✅ {len(resultado_df)} registro(s) após filtros")
            
            # ETAPA 6: Formatar resultados
            print("[TOOL] ETAPA 6: Formatando resultados...")
            dados_lista = []
            for _, row in resultado_df.iterrows():
                dados_lista.append(self._format_desvio_data(row))
            
            # ETAPA 7: Estatísticas
            stats = {
                'total_registros': len(desvios_df),
                'registros_filtrados': len(resultado_df),
            }
            
            # Desvios por usina
            if 'codigo_usina' in desvios_df.columns:
                stats['desvios_por_usina'] = desvios_df.groupby('codigo_usina').size().to_dict()
            
            # Total de desvio por usina
            if 'codigo_usina' in desvios_df.columns and 'valor' in desvios_df.columns:
                total_por_usina = desvios_df.groupby('codigo_usina')['valor'].sum().to_dict()
                stats['total_desvio_por_usina'] = {k: round(v, 2) for k, v in total_por_usina.items()}
            
            # Desvios por ano
            if 'data' in desvios_df.columns and pd.api.types.is_datetime64_any_dtype(desvios_df['data']):
                desvios_df_copy = desvios_df.copy()
                desvios_df_copy['ano'] = desvios_df_copy['data'].dt.year
                stats['desvios_por_ano'] = desvios_df_copy.groupby('ano').size().to_dict()
            
            # ETAPA 8: Formatar resultado final
            print("[TOOL] ETAPA 8: Formatando resultado final...")
            
            filtros_aplicados = {}
            if codigo_usina is not None:
                filtros_aplicados['codigo_usina'] = codigo_usina
            if periodo is not None:
                filtros_aplicados['periodo'] = periodo
            
            return {
                "success": True,
                "dados": dados_lista,
                "stats": stats,
                "filtros_aplicados": filtros_aplicados if filtros_aplicados else None,
                "description": f"Desvios de água: {len(resultado_df)} registro(s) do DSVAGUA.DAT",
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
                "error": f"Erro ao processar DSVAGUA.DAT: {str(e)}",
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
        Desvios de água para usos consuntivos. Dados de desvios de água por usina e estágio do arquivo DSVAGUA.DAT.
        
        Queries que ativam esta tool:
        - "desvios de água do dsvagua"
        - "desvios de água da usina X"
        - "desvios de água da usina Itaipu"
        - "desvio de água consuntivo"
        - "usos consuntivos de água"
        - "desvios de água em 2023"
        - "desvios de água da usina 10 em janeiro"
        - "desvios de água da usina Furnas"
        - "desvios de água consuntivos"
        
        Esta tool consulta o arquivo DSVAGUA.DAT e retorna informações sobre desvios de água para usos consuntivos, incluindo:
        - Código da usina
        - Data (estágio) do desvio
        - Valor do desvio
        - Considera desvio de usina NC (não considerada)
        - Comentários
        
        A tool permite filtrar por:
        - Usina específica (código numérico ou nome da usina)
        - Período (ano e/ou mês)
        
        A tool identifica automaticamente a usina mencionada na query através de matching inteligente:
        - Busca por código numérico explícito (ex: "usina 10")
        - Busca por nome completo da usina (ex: "usina Itaipu")
        - Busca por similaridade de strings
        - Busca por palavras-chave do nome
        
        Termos-chave: DSVAGUA, desvio de água, desvios de água, uso consuntivo, usos consuntivos, água consuntiva, diversão de água.
        """


"""
Tool para consultar dados de carga mensais por submercado.
Acessa o arquivo SISTEMA.DAT, propriedade mercado_energia.
"""
from newave_agent.app.tools.base import NEWAVETool
from inewave.newave import Sistema
import os
import pandas as pd
import re
from typing import Dict, Any, Optional

class CargaMensalTool(NEWAVETool):
    """
    Tool para consultar dados de carga mensais por submercado.
    Acessa o arquivo SISTEMA.DAT, propriedade mercado_energia.
    """
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga mensal por submercado.
        Suporta queries genéricas e com subsistema específico.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "carga mensal",
            "demanda mensal",
            "mercado energia",
            "carga por submercado",
            "demanda por submercado",
            "carga mensal submercado",
            "demanda mensal submercado",
            "carga mensal para cada submercado",
            "demanda mensal para cada submercado",
            "dados de carga mensais",
            "dados de demanda mensais",
            "carga do",  # "carga do norte", "carga do sudeste"
            "demanda do",  # "demanda do sul"
            "carga subsistema",  # "carga subsistema 1"
            "demanda subsistema",  # "demanda subsistema 2"
            "carga submercado",  # "carga submercado 3"
            "demanda submercado"  # "demanda submercado 4"
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_submercado_from_query(self, query: str, sistema: Sistema, subsistemas_disponiveis: list = None) -> Optional[int]:
        """
        Extrai código do submercado da query.
        
        IMPORTANTE: Não assume mapeamento hardcoded de nomes para códigos.
        Busca diretamente no arquivo SISTEMA.DAT para encontrar o código correto.
        
        Tenta identificar por:
        1. Número explícito (ex: "subsistema 1", "submercado 2")
        2. Nome do submercado buscando na lista de subsistemas disponíveis
        
        Args:
            query: Query do usuário
            sistema: Objeto Sistema já lido
            subsistemas_disponiveis: Lista de dicts com {'codigo': int, 'nome': str} dos subsistemas
            
        Returns:
            Código do submercado ou None se não encontrado
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
                    # Verificar se código existe na lista de subsistemas disponíveis
                    codigos_validos = [s['codigo'] for s in subsistemas_disponiveis]
                    if codigo in codigos_validos:
                        # Encontrar o nome do subsistema
                        nome_sub = next((s['nome'] for s in subsistemas_disponiveis if s['codigo'] == codigo), f"Subsistema {codigo}")
                        print(f"[TOOL] ✅ Código {codigo} encontrado por padrão numérico: \"{nome_sub}\"")
                        return codigo
                    else:
                        print(f"[TOOL] ⚠️ Código {codigo} mencionado mas não existe no arquivo")
                        print(f"[TOOL] Códigos disponíveis: {codigos_validos}")
                except ValueError:
                    continue
        
        # ETAPA 2: Buscar por nome na lista de subsistemas disponíveis
        print(f"[TOOL] Buscando correspondência por nome na query: '{query_lower}'")
        
        # Ordenar por tamanho do nome (mais específico primeiro) para evitar matches incorretos
        subsistemas_ordenados = sorted(subsistemas_disponiveis, key=lambda x: len(x['nome']), reverse=True)
        
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            # Verificar se o nome completo do subsistema está na query
            if nome_sub_lower and nome_sub_lower in query_lower:
                print(f"[TOOL] ✅ Código {codigo_sub} encontrado por nome completo '{nome_sub}' na query")
                return codigo_sub
            
            # Verificar palavras-chave do nome (para nomes compostos ou abreviações)
            palavras_nome = nome_sub_lower.split()
            for palavra in palavras_nome:
                # Ignorar palavras muito curtas ou comuns, mas aceitar palavras importantes
                if len(palavra) >= 3 and palavra in query_lower:
                    # Verificar se não é uma palavra muito comum que poderia dar falso positivo
                    palavras_comuns = ['do', 'da', 'de', 'para', 'por', 'com', 'sem', 'em', 'na', 'no']
                    if palavra not in palavras_comuns:
                        print(f"[TOOL] ✅ Código {codigo_sub} encontrado por palavra-chave '{palavra}' do nome '{nome_sub}'")
                        return codigo_sub
            
            # Verificar também padrões como "do norte", "do sudeste", etc
            padroes = [
                f"do {nome_sub_lower}",
                f"da {nome_sub_lower}",
                f"de {nome_sub_lower}",
                f"subsistema {nome_sub_lower}",
                f"submercado {nome_sub_lower}",
            ]
            for padrao in padroes:
                if padrao in query_lower:
                    print(f"[TOOL] ✅ Código {codigo_sub} encontrado por padrão '{padrao}' do nome '{nome_sub}'")
                    return codigo_sub
        
        print("[TOOL] ⚠️ Nenhum subsistema específico detectado na query")
        print(f"[TOOL] Subsistemas disponíveis para referência:")
        for s in subsistemas_disponiveis:
            print(f"[TOOL]   - Código {s['codigo']}: \"{s['nome']}\"")
        return None
    
    def _should_group_by_submercado(self, query: str) -> bool:
        """
        Detecta se a query pede dados agrupados por submercado.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se deve agrupar por submercado
        """
        query_lower = query.lower()
        
        # Palavras-chave que indicam agrupamento separado
        keywords_separado = [
            "separadamente",
            "separado",
            "por submercado",
            "por subsistema",
            "cada submercado",
            "cada subsistema",
            "todos os submercados",
            "todos os subsistemas",
            "todos os subsistema",  # sem plural
            "de todos os submercados",
            "de todos os subsistemas",
            "de todos os subsistema",
        ]
        
        return any(kw in query_lower for kw in keywords_separado)
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de carga mensal.
        
        Fluxo:
        1. Verifica se SISTEMA.DAT existe
        2. Lê o arquivo usando inewave
        3. Acessa propriedade mercado_energia
        4. Processa e formata os dados
        5. Retorna resultado estruturado
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com resultado da execução
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo SISTEMA.DAT...")
            sistema_path = os.path.join(self.deck_path, "SISTEMA.DAT")
            
            if not os.path.exists(sistema_path):
                # Tentar variações de nome
                sistema_path_upper = os.path.join(self.deck_path, "SISTEMA.DAT")
                sistema_path_lower = os.path.join(self.deck_path, "sistema.dat")
                
                if os.path.exists(sistema_path_upper):
                    sistema_path = sistema_path_upper
                elif os.path.exists(sistema_path_lower):
                    sistema_path = sistema_path_lower
                else:
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
            
            # ETAPA 3: Acessar propriedade mercado_energia
            print("[TOOL] ETAPA 3: Acessando propriedade mercado_energia...")
            df_mercado = sistema.mercado_energia
            
            if df_mercado is None or df_mercado.empty:
                print("[TOOL] ❌ DataFrame vazio ou None")
                return {
                    "success": False,
                    "error": "Dados de mercado de energia não encontrados no arquivo",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ DataFrame obtido: {len(df_mercado)} registros")
            print(f"[TOOL] Colunas: {list(df_mercado.columns)}")
            
            # ETAPA 3.5: Listar subsistemas disponíveis e extrair filtro se especificado
            print("[TOOL] ETAPA 3.5: Listando subsistemas disponíveis no arquivo...")
            
            # Listar todos os subsistemas disponíveis
            subsistemas_disponiveis = []
            if sistema.custo_deficit is not None:
                df_custo = sistema.custo_deficit
                subsistemas_unicos = df_custo[['codigo_submercado', 'nome_submercado']].drop_duplicates()
                subsistemas_unicos = subsistemas_unicos.sort_values('codigo_submercado')
                
                print("[TOOL] ===== SUBSISTEMAS DISPONÍVEIS NO ARQUIVO =====")
                for _, row in subsistemas_unicos.iterrows():
                    codigo = int(row.get('codigo_submercado'))
                    nome = str(row.get('nome_submercado', '')).strip()
                    subsistemas_disponiveis.append({'codigo': codigo, 'nome': nome})
                    print(f"[TOOL]   - Código {codigo}: \"{nome}\"")
                print("[TOOL] ==============================================")
            
            # Extrair filtro da query - A TOOL É RESPONSÁVEL POR IDENTIFICAR O CÓDIGO CORRETO
            print(f"[TOOL] Analisando query do usuário para identificar subsistema: '{query}'")
            codigo_submercado = None  # Inicializar variável
            codigo_submercado = self._extract_submercado_from_query(query, sistema, subsistemas_disponiveis)
            
            if codigo_submercado is not None:
                # Encontrar nome do subsistema para log
                nome_sub = next((s['nome'] for s in subsistemas_disponiveis if s['codigo'] == codigo_submercado), f"Subsistema {codigo_submercado}")
                print(f"[TOOL] ✅ TOOL IDENTIFICOU: Query do usuário refere-se ao subsistema '{nome_sub}' (Código: {codigo_submercado})")
            else:
                print("[TOOL] ⚠️ Nenhum subsistema específico identificado na query - retornando todos os submercados")
            
            if codigo_submercado is not None:
                print(f"[TOOL] ✅ Filtro detectado: subsistema {codigo_submercado}")
                
                # Obter nome do subsistema para exibição
                nome_submercado = None
                if sistema.custo_deficit is not None:
                    df_custo = sistema.custo_deficit
                    subsistema_info = df_custo[df_custo['codigo_submercado'] == codigo_submercado]
                    if not subsistema_info.empty:
                        nome_submercado = subsistema_info.iloc[0].get('nome_submercado', f'Subsistema {codigo_submercado}')
                
                # Filtrar DataFrame
                df_mercado = df_mercado[df_mercado['codigo_submercado'] == codigo_submercado].copy()
                print(f"[TOOL] ✅ Dados filtrados: {len(df_mercado)} registros para subsistema {codigo_submercado} ({nome_submercado})")
                
                if df_mercado.empty:
                    return {
                        "success": False,
                        "error": f"Nenhum dado encontrado para o subsistema {codigo_submercado} ({nome_submercado})",
                        "tool": self.get_name()
                    }
            else:
                print("[TOOL] ⚠️ Nenhum filtro por subsistema detectado, retornando todos os submercados")
            
            # ETAPA 4: Processar dados
            print("[TOOL] ETAPA 4: Processando dados...")
            print(f"[TOOL] Colunas disponíveis: {list(df_mercado.columns)}")
            print(f"[TOOL] Tipos de dados: {df_mercado.dtypes.to_dict()}")
            
            # Adicionar colunas auxiliares para facilitar consultas
            df_mercado = df_mercado.copy()
            
            # Verificar se existe coluna 'data' e processar
            if 'data' in df_mercado.columns:
                print(f"[TOOL] Coluna 'data' encontrada. Tipo: {df_mercado['data'].dtype}")
                
                # Verificar se a coluna 'data' é datetime, se não, converter
                if not pd.api.types.is_datetime64_any_dtype(df_mercado['data']):
                    print("[TOOL] ⚠️ Coluna 'data' não é datetime, tentando converter...")
                    try:
                        df_mercado['data'] = pd.to_datetime(df_mercado['data'], errors='coerce')
                        print("[TOOL] ✅ Coluna 'data' convertida para datetime")
                    except Exception as e:
                        print(f"[TOOL] ⚠️ Não foi possível converter 'data' para datetime: {e}")
                
                # Agora podemos usar .dt se a coluna for datetime
                if pd.api.types.is_datetime64_any_dtype(df_mercado['data']):
                    try:
                        df_mercado['ano'] = df_mercado['data'].dt.year
                        df_mercado['mes'] = df_mercado['data'].dt.month
                        df_mercado['mes_nome'] = df_mercado['data'].dt.strftime('%B')
                        df_mercado['ano_mes'] = df_mercado['data'].dt.strftime('%Y-%m')
                        print("[TOOL] ✅ Colunas auxiliares criadas a partir de 'data'")
                    except Exception as e:
                        print(f"[TOOL] ⚠️ Erro ao extrair ano/mês de 'data': {e}")
                        # Tentar usar colunas existentes se disponíveis
                        if 'ano' in df_mercado.columns and 'mes' in df_mercado.columns:
                            print("[TOOL] ✅ Usando colunas 'ano' e 'mes' existentes")
                elif 'ano' in df_mercado.columns and 'mes' in df_mercado.columns:
                    # Se não é datetime mas tem ano/mês, usar diretamente
                    print("[TOOL] ✅ Usando colunas 'ano' e 'mes' existentes")
                else:
                    print("[TOOL] ⚠️ Não foi possível criar colunas auxiliares de data")
            
            # Se não tem 'data' mas tem 'ano' e 'mes', usar diretamente
            elif 'ano' in df_mercado.columns and 'mes' in df_mercado.columns:
                print("[TOOL] ✅ Colunas 'ano' e 'mes' encontradas, usando diretamente")
                if 'mes_nome' not in df_mercado.columns:
                    # Criar mês nome a partir do número
                    meses = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                            5: 'May', 6: 'June', 7: 'July', 8: 'August',
                            9: 'September', 10: 'October', 11: 'November', 12: 'December'}
                    df_mercado['mes_nome'] = df_mercado['mes'].map(meses)
                if 'ano_mes' not in df_mercado.columns:
                    df_mercado['ano_mes'] = df_mercado['ano'].astype(str) + '-' + df_mercado['mes'].astype(str).str.zfill(2)
            else:
                print("[TOOL] ⚠️ Nenhuma coluna de data/ano/mês encontrada, continuando sem colunas auxiliares")
            
            # ETAPA 5: Calcular estatísticas e agregações
            print("[TOOL] ETAPA 5: Calculando estatísticas...")
            
            total_registros = len(df_mercado)
            submercados = sorted(df_mercado['codigo_submercado'].unique().tolist()) if 'codigo_submercado' in df_mercado.columns else []
            
            # Estatísticas por submercado (com detecção de redundância)
            stats_por_submercado = []
            if 'codigo_submercado' in df_mercado.columns and 'valor' in df_mercado.columns:
                for sub in submercados:
                    df_sub = df_mercado[df_mercado['codigo_submercado'] == sub]
                    
                    if len(df_sub) > 0:
                        min_val = df_sub['valor'].min()
                        max_val = df_sub['valor'].max()
                        mean_val = df_sub['valor'].mean()
                        total_val = df_sub['valor'].sum()
                        
                        # Detectar redundância: se todos os valores são iguais (ou muito próximos)
                        is_redundant = abs(min_val - max_val) < 0.01 and abs(min_val - mean_val) < 0.01
                        
                        if is_redundant:
                            # Consolidar: mostrar apenas um valor
                            stats_por_submercado.append({
                                'codigo_submercado': sub,
                                'total_registros': len(df_sub),
                                'carga_mensal_mwmed': round(mean_val, 2),  # Valor único
                                'redundante': True
                            })
                        else:
                            # Manter todos os campos quando há variação
                            stats_por_submercado.append({
                                'codigo_submercado': sub,
                                'total_registros': len(df_sub),
                                'carga_media_mwmed': round(mean_val, 2),
                                'carga_min_mwmed': round(min_val, 2),
                                'carga_max_mwmed': round(max_val, 2),
                                'carga_total_mwmed': round(total_val, 2),
                                'redundante': False
                            })
            
            # Agregação por submercado e ano
            aggregated = []
            if 'codigo_submercado' in df_mercado.columns and 'ano' in df_mercado.columns and 'valor' in df_mercado.columns:
                df_agregado = df_mercado.groupby(['codigo_submercado', 'ano'])['valor'].agg([
                    'sum', 'mean', 'min', 'max', 'count'
                ]).reset_index()
                df_agregado.columns = ['codigo_submercado', 'ano', 'carga_anual_total', 
                                      'carga_media_mensal', 'carga_min_mensal', 
                                      'carga_max_mensal', 'numero_meses']
                
                # Filtrar redundâncias: se min == max == média, consolidar
                aggregated_clean = []
                for _, row in df_agregado.iterrows():
                    record = row.to_dict()
                    
                    # Verificar se há redundância (todos os valores são iguais)
                    min_val = record.get('carga_min_mensal', 0)
                    max_val = record.get('carga_max_mensal', 0)
                    mean_val = record.get('carga_media_mensal', 0)
                    count = record.get('numero_meses', 0)
                    
                    # Se há apenas 1 registro ou todos os valores são iguais, consolidar
                    if count == 1 or (abs(min_val - max_val) < 0.01 and abs(min_val - mean_val) < 0.01):
                        # Consolidar: usar apenas um valor (carga mensal)
                        record_clean = {
                            'codigo_submercado': record.get('codigo_submercado'),
                            'ano': record.get('ano'),
                            'carga_mensal_mwmed': round(mean_val, 2),  # Valor único
                            'numero_meses': count,
                            'redundante': True  # Flag para indicar que foi consolidado
                        }
                        aggregated_clean.append(record_clean)
                    else:
                        # Manter todos os campos quando há variação
                        record_clean = {
                            'codigo_submercado': record.get('codigo_submercado'),
                            'ano': record.get('ano'),
                            'carga_anual_total': round(record.get('carga_anual_total', 0), 2),
                            'carga_media_mensal': round(mean_val, 2),
                            'carga_min_mensal': round(min_val, 2),
                            'carga_max_mensal': round(max_val, 2),
                            'numero_meses': count,
                            'redundante': False
                        }
                        aggregated_clean.append(record_clean)
                
                aggregated = aggregated_clean
            
            # Anos disponíveis
            anos = sorted(df_mercado['ano'].unique().tolist()) if 'ano' in df_mercado.columns else []
            
            # ETAPA 6: Formatar resultado
            print("[TOOL] ETAPA 6: Formatando resultado...")
            
            # Converter DataFrame para lista de dicts - RETORNAR TODOS OS DADOS
            print(f"[TOOL] Convertendo {len(df_mercado)} registros para formato JSON...")
            result_data = df_mercado.to_dict(orient="records")
            print(f"[TOOL] ✅ {len(result_data)} registros convertidos")
            
            # Converter tipos para JSON-serializable
            for record in result_data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            
            print(f"[TOOL] ✅ Processamento concluído: {len(result_data)} registros formatados")
            
            # Adicionar informação sobre filtro aplicado
            filtro_info = None
            if codigo_submercado is not None:
                nome_sub = None
                if sistema.custo_deficit is not None:
                    df_custo = sistema.custo_deficit
                    subsistema_info = df_custo[df_custo['codigo_submercado'] == codigo_submercado]
                    if not subsistema_info.empty:
                        nome_sub = subsistema_info.iloc[0].get('nome_submercado', f'Subsistema {codigo_submercado}')
                filtro_info = {
                    "codigo_submercado": codigo_submercado,
                    "nome_submercado": nome_sub,
                    "filtrado": True
                }
            
            # ETAPA 6.5: Organizar dados por submercado se solicitado
            dados_por_submercado = None
            organizado_por_submercado = False
            
            if self._should_group_by_submercado(query) and codigo_submercado is None:
                print("[TOOL] ETAPA 6.5: Organizando dados por submercado (separadamente)...")
                
                dados_por_submercado = {}
                if 'codigo_submercado' in df_mercado.columns:
                    # Usar o DataFrame original antes da conversão para manter tipos
                    for sub in submercados:
                        df_sub = df_mercado[df_mercado['codigo_submercado'] == sub].copy()
                        
                        # Obter nome do submercado
                        nome_sub = f"Subsistema {sub}"
                        if sistema.custo_deficit is not None:
                            df_custo = sistema.custo_deficit
                            subsistema_info = df_custo[df_custo['codigo_submercado'] == sub]
                            if not subsistema_info.empty:
                                nome_sub = subsistema_info.iloc[0].get('nome_submercado', nome_sub)
                        
                        # Converter para lista de dicts
                        dados_sub = df_sub.to_dict(orient="records")
                        
                        # Converter tipos para JSON-serializable
                        for record in dados_sub:
                            for key, value in record.items():
                                if pd.isna(value):
                                    record[key] = None
                                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                                    record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                        
                        dados_por_submercado[sub] = {
                            'codigo': sub,
                            'nome': nome_sub,
                            'dados': dados_sub,
                            'total_registros': len(dados_sub)
                        }
                    
                    organizado_por_submercado = True
                    print(f"[TOOL] ✅ Dados organizados por {len(dados_por_submercado)} submercado(s)")
            
            return {
                "success": True,
                "data": result_data,
                "dados_por_submercado": dados_por_submercado,  # NOVO: dados organizados por submercado
                "summary": {
                    "total_registros": total_registros,
                    "registros_retornados": len(result_data),
                    "submercados": submercados,
                    "anos": anos,
                    "periodo": f"{min(anos)} - {max(anos)}" if anos else "N/A",
                    "filtro_aplicado": filtro_info,
                    "organizado_por_submercado": organizado_por_submercado  # Flag indicando organização
                },
                "stats_por_submercado": stats_por_submercado,
                "aggregated": aggregated,
                "columns": list(df_mercado.columns),
                "description": "Dados de carga mensal (MWmédio) por submercado e período",
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
        Carga mensal por submercado. Demanda mensal por submercado. Consumo mensal de energia por submercado.
        
        Queries que ativam esta tool:
        - "me dê as cargas mensais por submercado"
        - "me de as cargas mensais por submercado"
        - "mostre as cargas mensais por submercado"
        - "quais são as cargas mensais por submercado"
        - "cargas mensais por submercado"
        - "demanda mensal por submercado"
        - "demandas mensais por submercado"
        - "carga mensal do subsistema"
        - "demanda mensal do subsistema"
        - "carga do Sudeste"
        - "demanda do Sudeste"
        - "carga do Sul"
        - "demanda do Sul"
        - "carga do Norte"
        - "demanda do Norte"
        - "carga do Nordeste"
        - "demanda do Nordeste"
        - "cargas do submercado"
        - "demandas do submercado"
        - "consumo mensal por região"
        - "carga total anual por submercado"
        - "demanda total anual por submercado"
        - "evolução da demanda mensal"
        - "mercado energia"
        - "submercado energia"
        - "subsistema energia"
        - "carga mensal subsistema 1"
        - "demanda mensal subsistema 2"
        - "carga do subsistema número 3"
        - "demanda do subsistema número 4"
        
        Termos-chave: carga mensal, cargas mensais, demanda mensal, demandas mensais, consumo mensal, carga por submercado, demanda por submercado, carga subsistema, demanda subsistema, mercado energia, submercado energia, subsistema energia, Sudeste, Sul, Norte, Nordeste.
        """


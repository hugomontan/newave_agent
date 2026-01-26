"""
Tool para consultar valores estruturais e conjunturais do CLAST.DAT.
Valores estruturais: custos base das classes térmicas (propriedade usinas)
Valores conjunturais: modificações sazonais dos custos (propriedade modificacoes)
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Clast
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print
from backend.newave.utils.thermal_plant_matcher import get_thermal_plant_matcher

class ClastValoresTool(NEWAVETool):
    """
    Tool para consultar valores estruturais e conjunturais do CLAST.DAT.
    
    Valores estruturais: Custos base das classes térmicas por ano
    Valores conjunturais: Modificações sazonais dos custos
    """
    
    def get_name(self) -> str:
        return "ClastValoresTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre valores estruturais/conjunturais do CLAST.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "clast",
            "classe térmica",
            "classe termica",
            "classe termelétrica",
            "custo térmico",
            "custo termico",
            "valor estrutural",
            "valor conjuntural",
            "valores estruturais",
            "valores conjunturais",
            "custo operação",
            "custo de operação",
            "custo operacional",
            "modificação sazonal",
            "modificacao sazonal",
            "custo classe",
            "classes térmicas",
            "classes termicas", 
            "CVU de curto prazo"
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _is_cvu_query(self, query: str) -> bool:
        """
        Verifica se a query é sobre CVU (Custo Variável Unitário).
        Quando for CVU, sempre retornar TODOS OS ANOS.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se for uma query de CVU
        """
        query_lower = query.lower()
        cvu_keywords = [
            "cvu",
            "custo variável unitário",
            "custo variavel unitario",
            "custo variável unitario",
            "custo variavel unitário",
        ]
        return any(kw in query_lower for kw in cvu_keywords)
    
    def _extract_tipo_valor(self, query: str) -> Optional[str]:
        """
        Extrai se a query pede valores estruturais ou conjunturais.
        
        Args:
            query: Query do usuário
            
        Returns:
            "estrutural", "conjuntural", ou None (ambos)
        """
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["estrutural", "custo base", "base"]):
            return "estrutural"
        elif any(kw in query_lower for kw in ["conjuntural", "modificação", "modificacao", "sazonal", "modificações", "modificacoes"]):
            return "conjuntural"
        
        return None  # Ambos
    
    def _extract_classe_from_query(self, query: str, clast: Clast) -> Optional[int]:
        """
        Extrai código da classe térmica da query usando o ThermalPlantMatcher unificado.
        
        Args:
            query: Query do usuário
            clast: Objeto Clast já lido
            
        Returns:
            Código da classe ou None se não encontrado
        """
        if clast.usinas is None:
            return None
        
        # Usar o matcher unificado com entity_type="classe"
        matcher = get_thermal_plant_matcher()
        return matcher.extract_plant_from_query(
            query=query,
            available_plants=clast.usinas,
            entity_type="classe",
            threshold=0.5
        )
    
    def _extract_tipo_combustivel(self, query: str) -> Optional[str]:
        """
        Extrai tipo de combustível da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Tipo de combustível ou None
        """
        query_lower = query.lower()
        
        tipos_combustivel = {
            'nuclear': 'Nuclear',
            'gas': 'Gas',
            'gnl': 'GNL',
            'diesel': 'Diesel',
            'biomassa': 'Biomassa',
            'gas proces': 'Gas Proces',
            'gas processado': 'Gas Proces',
        }
        
        for key, value in tipos_combustivel.items():
            if key in query_lower:
                return value
        
        return None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de valores estruturais e/ou conjunturais.
        
        Fluxo:
        1. Verifica se CLAST.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica tipo de valor solicitado (estrutural/conjuntural)
        4. Identifica filtros (classe, tipo de combustível)
        5. Processa e retorna dados
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo CLAST.DAT...")
            clast_path = os.path.join(self.deck_path, "CLAST.DAT")
            
            if not os.path.exists(clast_path):
                clast_path_lower = os.path.join(self.deck_path, "clast.dat")
                if os.path.exists(clast_path_lower):
                    clast_path = clast_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo CLAST.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo CLAST.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {clast_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            clast = Clast.read(clast_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Verificar se é query de CVU (sempre retornar todos os anos)
            is_cvu = self._is_cvu_query(query)
            if is_cvu:
                debug_print("[TOOL] ✅ Query de CVU detectada - retornando TODOS OS ANOS (sem filtro por ano)")
            
            # ETAPA 4: Identificar tipo de valor solicitado
            debug_print("[TOOL] ETAPA 4: Identificando tipo de valor solicitado...")
            tipo_valor = self._extract_tipo_valor(query)
            debug_print(f"[TOOL] Tipo de valor identificado: {tipo_valor or 'ambos (estrutural e conjuntural)'}")
            
            # ETAPA 5: Identificar filtros
            debug_print("[TOOL] ETAPA 5: Identificando filtros...")
            codigo_classe = self._extract_classe_from_query(query, clast)
            tipo_combustivel = self._extract_tipo_combustivel(query)
            
            if codigo_classe is not None:
                debug_print(f"[TOOL] ✅ Filtro por classe: {codigo_classe}")
            if tipo_combustivel is not None:
                debug_print(f"[TOOL] ✅ Filtro por tipo de combustível: {tipo_combustivel}")
            
            # IMPORTANTE: Para CVU, NUNCA filtrar por ano, mesmo que a query mencione um ano
            # Isso garante que todos os anos sejam sempre retornados para consultas de CVU
            
            # ETAPA 6: Processar dados estruturais
            dados_estruturais = None
            stats_estrutural = None
            
            if tipo_valor is None or tipo_valor == "estrutural":
                debug_print("[TOOL] ETAPA 6: Processando valores estruturais...")
                
                if clast.usinas is not None:
                    df_estrutural = clast.usinas.copy()
                    
                    # Aplicar filtros (classe e tipo de combustível)
                    if codigo_classe is not None:
                        df_estrutural = df_estrutural[df_estrutural['codigo_usina'] == codigo_classe]
                        debug_print(f"[TOOL] ✅ Dados filtrados por classe {codigo_classe}: {len(df_estrutural)} registros")
                    
                    if tipo_combustivel is not None:
                        df_estrutural = df_estrutural[df_estrutural['tipo_combustivel'] == tipo_combustivel]
                        debug_print(f"[TOOL] ✅ Dados filtrados por tipo {tipo_combustivel}: {len(df_estrutural)} registros")
                    
                    # IMPORTANTE: Para CVU, garantir que TODOS OS ANOS sejam retornados
                    # Não aplicar nenhum filtro por ano, mesmo que mencionado na query
                    if is_cvu:
                        # Garantir que não há filtro por ano aplicado
                        if 'indice_ano_estudo' in df_estrutural.columns:
                            anos_disponiveis = sorted(df_estrutural['indice_ano_estudo'].unique().tolist())
                            debug_print(f"[TOOL] ✅ CVU: Retornando dados de TODOS OS ANOS disponíveis: {anos_disponiveis}")
                            debug_print(f"[TOOL] ✅ CVU: Total de registros (todos os anos): {len(df_estrutural)}")
                            debug_print(f"[TOOL] ✅ CVU: Garantindo que nenhum filtro por ano foi aplicado")
                        else:
                            debug_print(f"[TOOL] ⚠️ CVU: Coluna 'indice_ano_estudo' não encontrada no DataFrame")
                    
                    # Converter para lista de dicts
                    dados_estruturais = df_estrutural.to_dict(orient="records")
                    
                    # Converter tipos para JSON-serializable
                    for record in dados_estruturais:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                    
                    # Calcular estatísticas
                    if len(df_estrutural) > 0:
                        stats_estrutural = {
                            'total_classes': df_estrutural['codigo_usina'].nunique() if 'codigo_usina' in df_estrutural.columns else 0,
                            'total_registros': len(df_estrutural),
                            'anos_cobertos': sorted(df_estrutural['indice_ano_estudo'].unique().tolist()) if 'indice_ano_estudo' in df_estrutural.columns else [],
                            'custo_medio': float(df_estrutural['valor'].mean()) if 'valor' in df_estrutural.columns else 0,
                            'custo_min': float(df_estrutural['valor'].min()) if 'valor' in df_estrutural.columns else 0,
                            'custo_max': float(df_estrutural['valor'].max()) if 'valor' in df_estrutural.columns else 0,
                            'tipos_combustivel': df_estrutural['tipo_combustivel'].unique().tolist() if 'tipo_combustivel' in df_estrutural.columns else [],
                        }
                        
                        # Estatísticas por tipo de combustível
                        if 'tipo_combustivel' in df_estrutural.columns and 'valor' in df_estrutural.columns:
                            stats_por_tipo = []
                            for tipo in df_estrutural['tipo_combustivel'].unique():
                                df_tipo = df_estrutural[df_estrutural['tipo_combustivel'] == tipo]
                                stats_por_tipo.append({
                                    'tipo_combustivel': tipo,
                                    'total_classes': df_tipo['codigo_usina'].nunique(),
                                    'custo_medio': float(df_tipo['valor'].mean()),
                                    'custo_min': float(df_tipo['valor'].min()),
                                    'custo_max': float(df_tipo['valor'].max()),
                                })
                            stats_estrutural['stats_por_tipo'] = stats_por_tipo
                    
                    debug_print(f"[TOOL] ✅ {len(dados_estruturais)} registros estruturais processados")
                else:
                    debug_print("[TOOL] ⚠️ Nenhum dado estrutural disponível (clast.usinas é None)")
            
            # ETAPA 7: Processar dados conjunturais
            dados_conjunturais = None
            stats_conjuntural = None
            
            if tipo_valor is None or tipo_valor == "conjuntural":
                debug_print("[TOOL] ETAPA 7: Processando valores conjunturais...")
                
                if clast.modificacoes is not None:
                    df_conjuntural = clast.modificacoes.copy()
                    
                    # Adicionar/preencher nome_usina fazendo join com clast.usinas
                    if clast.usinas is not None and 'codigo_usina' in df_conjuntural.columns:
                        # Verificar se nome_usina não existe ou está vazio
                        precisa_preencher = (
                            'nome_usina' not in df_conjuntural.columns or
                            df_conjuntural['nome_usina'].isna().all() or
                            (df_conjuntural['nome_usina'].astype(str).str.strip() == '').all()
                        )
                        
                        if precisa_preencher and 'nome_usina' in clast.usinas.columns:
                            # Criar mapeamento codigo_usina -> nome_usina
                            mapeamento_nomes = clast.usinas[['codigo_usina', 'nome_usina']].drop_duplicates()
                            
                            if 'nome_usina' not in df_conjuntural.columns:
                                # Se a coluna não existe, fazer merge
                                df_conjuntural = df_conjuntural.merge(
                                    mapeamento_nomes,
                                    on='codigo_usina',
                                    how='left'
                                )
                            else:
                                # Se a coluna existe mas está vazia, preencher com merge
                                df_conjuntural = df_conjuntural.merge(
                                    mapeamento_nomes,
                                    on='codigo_usina',
                                    how='left',
                                    suffixes=('', '_novo')
                                )
                                # Preencher valores vazios/NaN com os valores do merge
                                mask_vazio = df_conjuntural['nome_usina'].isna() | (df_conjuntural['nome_usina'].astype(str).str.strip() == '')
                                df_conjuntural.loc[mask_vazio, 'nome_usina'] = df_conjuntural.loc[mask_vazio, 'nome_usina_novo']
                                df_conjuntural = df_conjuntural.drop(columns=['nome_usina_novo'], errors='ignore')
                            
                            debug_print(f"[TOOL] ✅ Nome da usina adicionado/preenchido nos dados conjunturais via join")
                    
                    # Aplicar filtros
                    if codigo_classe is not None:
                        df_conjuntural = df_conjuntural[df_conjuntural['codigo_usina'] == codigo_classe]
                        debug_print(f"[TOOL] ✅ Modificações filtradas por classe {codigo_classe}: {len(df_conjuntural)} registros")
                    
                    # Converter datas para string
                    dados_conjunturais = df_conjuntural.to_dict(orient="records")
                    for record in dados_conjunturais:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                            elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                                record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    
                    # Calcular estatísticas
                    if len(df_conjuntural) > 0:
                        stats_conjuntural = {
                            'total_modificacoes': len(df_conjuntural),
                            'classes_afetadas': df_conjuntural['codigo_usina'].nunique() if 'codigo_usina' in df_conjuntural.columns else 0,
                            'custo_medio': float(df_conjuntural['custo'].mean()) if 'custo' in df_conjuntural.columns else 0,
                            'custo_min': float(df_conjuntural['custo'].min()) if 'custo' in df_conjuntural.columns else 0,
                            'custo_max': float(df_conjuntural['custo'].max()) if 'custo' in df_conjuntural.columns else 0,
                        }
                    
                    debug_print(f"[TOOL] ✅ {len(dados_conjunturais)} registros conjunturais processados")
                else:
                    debug_print("[TOOL] ⚠️ Nenhum dado conjuntural disponível (clast.modificacoes é None)")
            
            # ETAPA 8: Formatar resultado
            debug_print("[TOOL] ETAPA 8: Formatando resultado...")
            
            # Adicionar flag indicando que é CVU (para garantir que todos os anos foram retornados)
            if is_cvu:
                debug_print("[TOOL] ✅ Flag CVU: Garantindo que todos os anos foram incluídos na resposta")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if codigo_classe is not None:
                if clast.usinas is not None:
                    classe_info = clast.usinas[clast.usinas['codigo_usina'] == codigo_classe]
                    if not classe_info.empty:
                        filtro_info['classe'] = {
                            'codigo': codigo_classe,
                            'nome': classe_info.iloc[0].get('nome_usina', f'Classe {codigo_classe}'),
                            'tipo_combustivel': classe_info.iloc[0].get('tipo_combustivel', 'N/A')
                        }
            if tipo_combustivel is not None:
                filtro_info['tipo_combustivel'] = tipo_combustivel
            
            return {
                "success": True,
                "dados_estruturais": dados_estruturais,
                "dados_conjunturais": dados_conjunturais,
                "tipo_solicitado": tipo_valor or "ambos",
                "filtros": filtro_info if filtro_info else None,
                "stats_estrutural": stats_estrutural,
                "stats_conjuntural": stats_conjuntural,
                "description": "Valores estruturais (custos base) e conjunturais (modificações sazonais) do CLAST.DAT",
                "tool": self.get_name(),
                "deck_path": self.deck_path  # IMPORTANTE: Necessário para extrair ano do deck corretamente
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
                "error": f"Erro ao processar CLAST.DAT: {str(e)}",
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
        Custos de classes térmicas. Valores estruturais e conjunturais do CLAST. Custos operacionais das classes térmicas.
        
        IMPORTANTE: Quando a query mencionar CVU (Custo Variável Unitário) ou "custo variável unitário", 
        a resposta SEMPRE deve retornar dados de TODOS OS ANOS disponíveis, não apenas de um ano específico.
        Mesmo que a query mencione um ano específico (ex: "CVU da classe ANGRA 1 para 2025"), 
        a resposta deve incluir todos os anos disponíveis no arquivo.
        
        Queries que ativam esta tool:
        - "quais são os custos das classes térmicas"
        - "custos das classes térmicas"
        - "custo da classe térmica"
        - "valores estruturais do CLAST"
        - "valores estruturais"
        - "valores conjunturais do CLAST"
        - "valores conjunturais"
        - "CVU da classe ANGRA 1" (retorna TODOS OS ANOS)
        - "CVU da classe 211" (retorna TODOS OS ANOS)
        - "custo variável unitário" (retorna TODOS OS ANOS)
        - "custos base das classes térmicas"
        - "custos operacionais das classes térmicas"
        - "modificações sazonais da classe 211"
        - "modificações sazonais"
        - "ajustes sazonais de custos"
        - "custos conjunturais das classes térmicas"
        - "classes térmicas com custo zero"
        - "custos por tipo de combustível"
        - "preços de operação das classes térmicas"
        - "custos de geração das classes térmicas"
        - "quais classes têm os menores custos"
        - "custos base das termelétricas"
        - "dados do CLAST"
        - "CVU de curto prazo da classe ANGRA 1" (retorna TODOS OS ANOS)
        
        Termos-chave: clast, CVU, classe térmica, classes térmicas, custo térmico, custos térmicos, valor estrutural, valores estruturais, valor conjuntural, valores conjunturais, custos base, custos operacionais, CVU, custo variável unitário, preços de operação, custos de geração, modificação sazonal, modificações sazonais.
        """

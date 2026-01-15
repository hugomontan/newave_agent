"""
Tool para consultar agrupamentos de intercâmbio.
Acessa o arquivo AGRINT.DAT, propriedades agrupamentos e limites_agrupamentos.
"""
from newave_agent.app.tools.base import NEWAVETool
from inewave.newave import Agrint
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from datetime import datetime

class AgrintTool(NEWAVETool):
    """
    Tool para consultar agrupamentos de intercâmbio.
    Acessa o arquivo AGRINT.DAT, propriedades agrupamentos e limites_agrupamentos.
    """
    
    def get_name(self) -> str:
        return "AgrintTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre agrupamentos de intercâmbio.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "agrupamento de intercambio",
            "agrupamento de intercâmbio",
            "agrupamentos de intercambio",
            "agrupamentos de intercâmbio",
            "agrupamento intercambio",
            "agrupamento intercâmbio",
            "agrint",
            "restricao linear",
            "restrição linear",
            "restricoes lineares",
            "restrições lineares",
            "limite de agrupamento",
            "limites de agrupamento",
            "combinação linear",
            "combinacao linear",
            "corredor de transmissao",
            "corredor de transmissão",
            "limite combinado",
            "limites combinados",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_agrupamento_from_query(self, query: str) -> Optional[int]:
        """
        Extrai número do agrupamento da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Número do agrupamento ou None se não encontrado
        """
        query_lower = query.lower()
        
        patterns = [
            r'agrupamento\s*(\d+)',
            r'agrupamento\s*n[úu]mero\s*(\d+)',
            r'agrupamento\s*#?\s*(\d+)',
            r'agr\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    agrupamento = int(match.group(1))
                    print(f"[TOOL] ✅ Agrupamento {agrupamento} encontrado na query")
                    return agrupamento
                except ValueError:
                    continue
        
        return None
    
    def _extract_patamar_from_query(self, query: str) -> Optional[int]:
        """
        Extrai patamar de carga da query.
        
        Args:
            query: Query do usuário
            
        Returns:
            Número do patamar (1-5) ou None se não encontrado
        """
        query_lower = query.lower()
        
        patterns = [
            r'patamar\s*(\d+)',
            r'patamar\s*n[úu]mero\s*(\d+)',
            r'patamar\s*#?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    patamar = int(match.group(1))
                    if 1 <= patamar <= 5:
                        print(f"[TOOL] ✅ Patamar {patamar} encontrado na query")
                        return patamar
                except ValueError:
                    continue
        
        return None
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de agrupamentos de intercâmbio.
        
        Fluxo:
        1. Verifica se AGRINT.DAT existe
        2. Lê o arquivo usando inewave
        3. Acessa propriedades agrupamentos e limites_agrupamentos
        4. Processa e retorna dados
        """
        print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        print(f"[TOOL] Query: {query[:100]}")
        print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            print("[TOOL] ETAPA 1: Verificando existência do arquivo AGRINT.DAT...")
            agrint_path = os.path.join(self.deck_path, "AGRINT.DAT")
            
            if not os.path.exists(agrint_path):
                agrint_path_lower = os.path.join(self.deck_path, "agrint.dat")
                if os.path.exists(agrint_path_lower):
                    agrint_path = agrint_path_lower
                else:
                    print(f"[TOOL] ❌ Arquivo AGRINT.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo AGRINT.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            print(f"[TOOL] ✅ Arquivo encontrado: {agrint_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            agrint = Agrint.read(agrint_path)
            print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Acessar propriedades
            print("[TOOL] ETAPA 3: Acessando propriedades...")
            df_agrupamentos = agrint.agrupamentos
            df_limites = agrint.limites_agrupamentos
            
            if df_agrupamentos is None or df_agrupamentos.empty:
                print("[TOOL] ⚠️ Nenhum agrupamento encontrado no arquivo")
                return {
                    "success": False,
                    "error": "Nenhum agrupamento encontrado no arquivo AGRINT.DAT",
                    "tool": self.get_name()
                }
            
            print(f"[TOOL] ✅ Agrupamentos obtidos: {len(df_agrupamentos)} interligações")
            if df_limites is not None:
                print(f"[TOOL] ✅ Limites obtidos: {len(df_limites)} registros")
            
            # ETAPA 4: Identificar filtros da query
            print("[TOOL] ETAPA 4: Identificando filtros...")
            agrupamento_filtro = self._extract_agrupamento_from_query(query)
            patamar_filtro = self._extract_patamar_from_query(query)
            
            # Detectar se query pede agrupamentos ou limites
            query_lower = query.lower()
            pede_agrupamentos = any(kw in query_lower for kw in [
                "agrupamento", "interligacoes", "interligações", "coeficiente", "coeficientes"
            ])
            pede_limites = any(kw in query_lower for kw in [
                "limite", "limites", "patamar", "patamares", "periodo", "período"
            ])
            
            # Se não especificar, retornar ambos
            if not pede_agrupamentos and not pede_limites:
                pede_agrupamentos = True
                pede_limites = True
            
            # ETAPA 5: Processar agrupamentos
            dados_agrupamentos = None
            stats_agrupamentos = None
            
            if pede_agrupamentos:
                print("[TOOL] ETAPA 5: Processando agrupamentos...")
                df_agrup_filtrado = df_agrupamentos.copy()
                
                if agrupamento_filtro is not None:
                    df_agrup_filtrado = df_agrup_filtrado[
                        df_agrup_filtrado['agrupamento'] == agrupamento_filtro
                    ]
                    print(f"[TOOL] ✅ Filtrado por agrupamento: {agrupamento_filtro}")
                
                # Converter para lista de dicts
                dados_agrupamentos = df_agrup_filtrado.to_dict(orient="records")
                
                # Converter tipos para JSON-serializable
                for record in dados_agrupamentos:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                
                # Estatísticas
                if len(df_agrup_filtrado) > 0:
                    agrupamentos_unicos = df_agrup_filtrado['agrupamento'].nunique()
                    stats_agrupamentos = {
                        'total_interligacoes': len(df_agrup_filtrado),
                        'total_agrupamentos': agrupamentos_unicos,
                        'coeficiente_medio': float(df_agrup_filtrado['coeficiente'].mean()),
                        'coeficiente_min': float(df_agrup_filtrado['coeficiente'].min()),
                        'coeficiente_max': float(df_agrup_filtrado['coeficiente'].max()),
                    }
                    
                    # Estatísticas por agrupamento
                    stats_por_agrupamento = []
                    for agr in df_agrup_filtrado['agrupamento'].unique():
                        df_agr = df_agrup_filtrado[df_agrup_filtrado['agrupamento'] == agr]
                        stats_por_agrupamento.append({
                            'agrupamento': int(agr),
                            'total_interligacoes': len(df_agr),
                            'coeficiente_medio': float(df_agr['coeficiente'].mean()),
                            'coeficiente_soma': float(df_agr['coeficiente'].sum()),
                        })
                    stats_agrupamentos['stats_por_agrupamento'] = stats_por_agrupamento
                
                print(f"[TOOL] ✅ {len(dados_agrupamentos)} interligações processadas")
            
            # ETAPA 6: Processar limites
            dados_limites = None
            stats_limites = None
            
            if pede_limites and df_limites is not None and not df_limites.empty:
                print("[TOOL] ETAPA 6: Processando limites...")
                df_limites_filtrado = df_limites.copy()
                
                if agrupamento_filtro is not None:
                    df_limites_filtrado = df_limites_filtrado[
                        df_limites_filtrado['agrupamento'] == agrupamento_filtro
                    ]
                    print(f"[TOOL] ✅ Limites filtrados por agrupamento: {agrupamento_filtro}")
                
                if patamar_filtro is not None:
                    df_limites_filtrado = df_limites_filtrado[
                        df_limites_filtrado['patamar'] == patamar_filtro
                    ]
                    print(f"[TOOL] ✅ Limites filtrados por patamar: {patamar_filtro}")
                
                # Adicionar colunas auxiliares
                if 'data_inicio' in df_limites_filtrado.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_limites_filtrado['data_inicio']):
                        df_limites_filtrado['ano_inicio'] = df_limites_filtrado['data_inicio'].dt.year
                        df_limites_filtrado['mes_inicio'] = df_limites_filtrado['data_inicio'].dt.month
                
                if 'data_fim' in df_limites_filtrado.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_limites_filtrado['data_fim']):
                        df_limites_filtrado['ano_fim'] = df_limites_filtrado['data_fim'].dt.year
                        df_limites_filtrado['mes_fim'] = df_limites_filtrado['data_fim'].dt.month
                
                # Converter para lista de dicts
                dados_limites = df_limites_filtrado.to_dict(orient="records")
                
                # Converter tipos para JSON-serializable
                for record in dados_limites:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                            record[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                
                # Estatísticas
                if len(df_limites_filtrado) > 0:
                    stats_limites = {
                        'total_registros': len(df_limites_filtrado),
                        'agrupamentos_unicos': df_limites_filtrado['agrupamento'].nunique(),
                        'patamares_unicos': sorted(df_limites_filtrado['patamar'].unique().tolist()) if 'patamar' in df_limites_filtrado.columns else [],
                        'limite_medio': float(df_limites_filtrado['valor'].mean()) if 'valor' in df_limites_filtrado.columns else 0,
                        'limite_min': float(df_limites_filtrado['valor'].min()) if 'valor' in df_limites_filtrado.columns else 0,
                        'limite_max': float(df_limites_filtrado['valor'].max()) if 'valor' in df_limites_filtrado.columns else 0,
                    }
                    
                    # Estatísticas por agrupamento
                    if 'agrupamento' in df_limites_filtrado.columns:
                        stats_por_agrupamento_limites = []
                        for agr in df_limites_filtrado['agrupamento'].unique():
                            df_agr = df_limites_filtrado[df_limites_filtrado['agrupamento'] == agr]
                            stats_por_agrupamento_limites.append({
                                'agrupamento': int(agr),
                                'total_registros': len(df_agr),
                                'limite_medio': float(df_agr['valor'].mean()) if 'valor' in df_agr.columns else 0,
                                'limite_min': float(df_agr['valor'].min()) if 'valor' in df_agr.columns else 0,
                                'limite_max': float(df_agr['valor'].max()) if 'valor' in df_agr.columns else 0,
                            })
                        stats_limites['stats_por_agrupamento'] = stats_por_agrupamento_limites
                
                print(f"[TOOL] ✅ {len(dados_limites)} limites processados")
            
            # ETAPA 7: Formatar resultado
            print("[TOOL] ETAPA 7: Formatando resultado...")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if agrupamento_filtro is not None:
                filtro_info['agrupamento'] = agrupamento_filtro
            if patamar_filtro is not None:
                filtro_info['patamar'] = patamar_filtro
            
            return {
                "success": True,
                "agrupamentos": dados_agrupamentos,
                "limites": dados_limites,
                "summary": {
                    "total_interligacoes": len(dados_agrupamentos) if dados_agrupamentos else 0,
                    "total_limites": len(dados_limites) if dados_limites else 0,
                    "filtro_aplicado": filtro_info if filtro_info else None
                },
                "stats_agrupamentos": stats_agrupamentos,
                "stats_limites": stats_limites,
                "description": "Agrupamentos de intercâmbio e seus limites",
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
                "error": f"Erro ao processar AGRINT.DAT: {str(e)}",
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
        Agrupamentos de intercâmbio. Restrições lineares de transmissão. Limites combinados de interligações. Corredores de transmissão.
        
        Queries que ativam esta tool:
        - "quais são os agrupamentos de intercâmbio"
        - "agrupamentos de intercâmbio"
        - "agrupamento 1"
        - "limites do agrupamento 1"
        - "interligações do agrupamento 2"
        - "coeficientes do agrupamento"
        - "limites por patamar do agrupamento"
        - "restrições lineares de transmissão"
        - "corredor de transmissão"
        - "limite combinado de interligações"
        - "agrupamento de intercâmbio número 3"
        - "limites do agrupamento no patamar 1"
        - "combinação linear de interligações"
        - "restrições de agrupamento"
        
        Termos-chave: agrupamento de intercâmbio, agrupamentos de intercâmbio, agrint, restrição linear, restrições lineares, limite de agrupamento, limites de agrupamento, combinação linear, corredor de transmissão, limite combinado, limites combinados, coeficiente de agrupamento.
        """


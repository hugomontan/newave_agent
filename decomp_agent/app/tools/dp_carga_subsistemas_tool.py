"""
Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
Acessa dados de demanda por patamar, duração dos patamares, etc.
"""
from decomp_agent.app.tools.base import DECOMPTool
from decomp_agent.app.config import safe_print
from idecomp.decomp import Dadger
import os
import pandas as pd
import re
from typing import Dict, Any, Optional, List

class DPCargaSubsistemasTool(DECOMPTool):
    """
    Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
    
    Dados disponíveis:
    - Estágio
    - Código do submercado
    - Número de patamares
    - Para cada patamar (1=PESADA, 2=MEDIA, 3=LEVE):
      - Demanda (MWmed)
      - Duração do patamar (horas)
    """
    
    def get_name(self) -> str:
        return "DPCargaSubsistemasTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre carga dos subsistemas do Bloco DP.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "carga dos subsistemas",
            "carga subsistemas",
            "demanda subsistemas",
            "demanda dos subsistemas",
            "bloco dp",
            "registro dp",
            "dp decomp",
            "patamares de carga",
            "patamares carga",
            "duração patamares",
            "duracao patamares",
            "demanda por patamar",
            "carga por patamar",
            "mwmed",
            "mw médio",
            "mw medio",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def get_description(self) -> str:
        return """
        Tool para consultar informações do Bloco DP (Carga dos Subsistemas) do DECOMP.
        
        Acessa dados do registro DP que define:
        - Carga/Demanda dos subsistemas por patamar
        - Estágio de operação
        - Código do submercado
        - Número de patamares
        - Dados por patamar (1=PESADA, 2=MEDIA, 3=LEVE):
          * Demanda (MWmed - MW médio)
          * Duração do patamar (horas)
        
        Exemplos de queries:
        - "Quais são as cargas dos subsistemas?"
        - "Qual a demanda do submercado 1 no estágio 1?"
        - "Mostre os patamares de carga"
        - "Demanda por patamar do Sudeste"
        """
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta sobre carga dos subsistemas do Bloco DP.
        
        Args:
            query: Query do usuário
            **kwargs: Argumentos adicionais opcionais
            
        Returns:
            Dict com dados da carga dos subsistemas formatados
        """
        try:
            # ⚡ OTIMIZAÇÃO: Usar cache global do Dadger
            from decomp_agent.app.utils.dadger_cache import get_cached_dadger
            dadger = get_cached_dadger(self.deck_path)
            
            if dadger is None:
                return {
                    "success": False,
                    "error": "Arquivo dadger não encontrado (nenhum arquivo dadger.rv* encontrado)"
                }
            
            # Extrair filtros da query
            codigo_submercado = self._extract_codigo_submercado(query)
            estagio = self._extract_estagio(query)
            numero_patamares = self._extract_numero_patamares(query)
            
            safe_print(f"[DP TOOL] Query recebida: {query}")
            safe_print(f"[DP TOOL] Codigo submercado extraido: {codigo_submercado}")
            safe_print(f"[DP TOOL] Estagio extraido: {estagio}")
            safe_print(f"[DP TOOL] Numero patamares extraido: {numero_patamares}")
            
            # Obter dados da carga dos subsistemas
            dp_data = dadger.dp(
                codigo_submercado=codigo_submercado,
                estagio=estagio,
                numero_patamares=numero_patamares,
                df=True  # Retornar como DataFrame
            )
            
            if dp_data is None or (isinstance(dp_data, pd.DataFrame) and dp_data.empty):
                return {
                    "success": False,
                    "error": "Nenhum registro de carga encontrado com os filtros especificados"
                }
            
            # DEBUG: Verificar colunas reais do DataFrame
            if isinstance(dp_data, pd.DataFrame):
                safe_print(f"[DP TOOL] Colunas disponíveis: {list(dp_data.columns)}")
                if len(dp_data) > 0:
                    safe_print(f"[DP TOOL] Primeiro registro: {dp_data.iloc[0].to_dict()}")
            
            # Converter para formato padronizado
            if isinstance(dp_data, pd.DataFrame):
                data = dp_data.to_dict('records')
            elif isinstance(dp_data, list):
                data = [self._dp_to_dict(dp) for dp in dp_data]
            else:
                data = [self._dp_to_dict(dp_data)]
            
            safe_print(f"[DP TOOL] Retornando {len(data)} registros de carga dos subsistemas")
            safe_print(f"[DP TOOL] Filtros aplicados: submercado={codigo_submercado}, estagio={estagio}, patamares={numero_patamares}")
            
            # Preparar filtros
            filtros_dict = {
                "codigo_submercado": codigo_submercado,
                "estagio": estagio,
                "numero_patamares": numero_patamares,
            }
            
            return {
                "success": True,
                "data": data,
                "total_registros": len(data),
                "filtros": filtros_dict,
                "tool": self.get_name()
            }
            
        except Exception as e:
            safe_print(f"[DP TOOL] ❌ Erro ao consultar Bloco DP: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Erro ao consultar Bloco DP: {str(e)}",
                "tool": self.get_name()
            }
    
    def _extract_codigo_submercado(self, query: str) -> Optional[int]:
        """Extrai código do submercado da query."""
        patterns = [
            r'submercado\s*(\d+)',
            r'su\s*(\d+)',
            r'subsistema\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_estagio(self, query: str) -> Optional[int]:
        """Extrai estágio da query."""
        patterns = [
            r'estágio\s*(\d+)',
            r'estagio\s*(\d+)',
            r'estágio\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_numero_patamares(self, query: str) -> Optional[int]:
        """Extrai número de patamares da query."""
        patterns = [
            r'patamares?\s*(\d+)',
            r'pat\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _dp_to_dict(self, dp_obj) -> Dict[str, Any]:
        """Converte objeto DP para dict."""
        if isinstance(dp_obj, dict):
            return dp_obj
        if hasattr(dp_obj, '__dict__'):
            return dp_obj.__dict__
        
        # Extrair atributos conhecidos do registro DP
        # Tentar múltiplas variações de nomes de atributos
        result = {}
        
        # Campos básicos
        result["estagio"] = (
            getattr(dp_obj, 'estagio', None) or
            getattr(dp_obj, 'ip', None)
        )
        result["codigo_submercado"] = (
            getattr(dp_obj, 'codigo_submercado', None) or
            getattr(dp_obj, 'submercado', None) or
            getattr(dp_obj, 's', None)
        )
        result["numero_patamares"] = (
            getattr(dp_obj, 'numero_patamares', None) or
            getattr(dp_obj, 'patamares', None) or
            getattr(dp_obj, 'pat', None) or
            3
        )
        
        # Campos de demanda e duração por patamar - tentar todas as variações
        for patamar_idx in [1, 2, 3]:
            # Demanda
            demanda = (
                getattr(dp_obj, f'demanda_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'demanda_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'mwmed_pat{patamar_idx}', None) or
                getattr(dp_obj, f'demanda_pat{patamar_idx}', None)
            )
            result[f"demanda_patamar_{patamar_idx}"] = demanda
            
            # Duração
            duracao = (
                getattr(dp_obj, f'duracao_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'duracao_{patamar_idx}', None) or
                getattr(dp_obj, f'horas_{patamar_idx}', None) or
                getattr(dp_obj, f'horas_patamar_{patamar_idx}', None) or
                getattr(dp_obj, f'duracao_pat{patamar_idx}', None) or
                getattr(dp_obj, f'horas_pat{patamar_idx}', None)
            )
            result[f"duracao_patamar_{patamar_idx}"] = duracao
        
        return result

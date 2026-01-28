"""
Tool para consultar volume inicial percentual (v.inic) do CONFHD.DAT por usina.
Retorna dados brutos de todas as usinas para comparação entre decks.
"""
from backend.newave.tools.base import NEWAVETool
from inewave.newave import Confhd
import os
import pandas as pd
import re
from typing import Dict, Any, Optional
from backend.newave.config import debug_print, safe_print

class VariacaoReservatorioInicialTool(NEWAVETool):
    """
    Tool para consultar volume inicial percentual (v.inic) do CONFHD.DAT por usina.
    Retorna dados brutos de todas as usinas para comparação entre decks.
    """
    
    def get_name(self) -> str:
        return "VariacaoReservatorioInicialTool"
    
    def can_handle(self, query: str) -> bool:
        """
        Verifica se a query é sobre reservatório inicial por usina.
        
        Args:
            query: Query do usuário
            
        Returns:
            True se a tool pode processar a query
        """
        query_lower = query.lower()
        keywords = [
            "v.inic",
            "v inic",
            "v. inic",
            "reservatório inicial",
            "reservatorio inicial",
            "volume inicial",
            "volume inicial percentual",
            "reservatório inicial por usina",
            "reservatorio inicial por usina",
            "v.inic por usina",
            "volume inicial usina",
        ]
        return any(kw in query_lower for kw in keywords)
    
    def _extract_usina_from_query(self, query: str, confhd: Confhd) -> Optional[int]:
        """
        Extrai código da usina da query usando HydraulicPlantMatcher unificado.
        
        Args:
            query: Query do usuário
            confhd: Objeto Confhd já lido
            
        Returns:
            Código da usina ou None se não encontrado
        """
        if confhd.usinas is None or confhd.usinas.empty:
            return None
        
        from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
        
        matcher = get_hydraulic_plant_matcher()
        result = matcher.extract_plant_from_query(
            query=query,
            available_plants=confhd.usinas,
            return_format="codigo",
            threshold=0.5
        )
        
        return result
    
    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Executa a consulta de volume inicial percentual por usina.
        
        Fluxo:
        1. Verifica se CONFHD.DAT existe
        2. Lê o arquivo usando inewave
        3. Identifica filtros (usina específica)
        4. Processa e retorna dados brutos
        """
        debug_print(f"[TOOL] {self.get_name()}: Iniciando execução...")
        debug_print(f"[TOOL] Query: {query[:100]}")
        debug_print(f"[TOOL] Deck path: {self.deck_path}")
        
        try:
            # ETAPA 1: Verificar existência do arquivo
            debug_print("[TOOL] ETAPA 1: Verificando existência do arquivo CONFHD.DAT...")
            confhd_path = os.path.join(self.deck_path, "CONFHD.DAT")
            
            if not os.path.exists(confhd_path):
                confhd_path_lower = os.path.join(self.deck_path, "confhd.dat")
                if os.path.exists(confhd_path_lower):
                    confhd_path = confhd_path_lower
                else:
                    safe_print(f"[TOOL] ❌ Arquivo CONFHD.DAT não encontrado")
                    return {
                        "success": False,
                        "error": f"Arquivo CONFHD.DAT não encontrado em {self.deck_path}",
                        "tool": self.get_name()
                    }
            
            debug_print(f"[TOOL] ✅ Arquivo encontrado: {confhd_path}")
            
            # ETAPA 2: Ler arquivo usando inewave
            debug_print("[TOOL] ETAPA 2: Lendo arquivo com inewave...")
            confhd = Confhd.read(confhd_path)
            debug_print("[TOOL] ✅ Arquivo lido com sucesso")
            
            # ETAPA 3: Identificar filtros (codigo_usina=CONFHD interno para filtro; codigo_csv para selected_plant)
            debug_print("[TOOL] ETAPA 3: Identificando filtros...")
            codigo_usina = None
            codigo_csv = None
            usinas_df = confhd.usinas if confhd.usinas is not None else pd.DataFrame()
            forced = kwargs.get("forced_plant_code")
            if forced is not None:
                codigo_csv = int(forced)
                from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                matcher = get_hydraulic_plant_matcher()
                if codigo_csv in matcher.code_to_names and not usinas_df.empty:
                    nome_csv, _, _ = matcher.code_to_names[codigo_csv]
                    nome_upper = (nome_csv or "").upper().strip()
                    match = usinas_df[usinas_df["nome_usina"].astype(str).str.upper().str.strip() == nome_upper]
                    if not match.empty:
                        codigo_usina = int(match.iloc[0]["codigo_usina"])
                    else:
                        for _, row in usinas_df.iterrows():
                            n = str(row.get("nome_usina", "")).upper().strip()
                            if nome_upper in n or n in nome_upper:
                                codigo_usina = int(row["codigo_usina"])
                                break
            else:
                ext = self._extract_usina_from_query(query, confhd)
                if ext is not None:
                    codigo_usina = ext
                    from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                    matcher = get_hydraulic_plant_matcher()
                    if not usinas_df.empty:
                        confhd_row = usinas_df[usinas_df["codigo_usina"] == codigo_usina]
                        if not confhd_row.empty:
                            nome_confhd = str(confhd_row.iloc[0].get("nome_usina", "")).upper().strip()
                            for c, (nome_arq, nome_compl, _) in matcher.code_to_names.items():
                                if (nome_arq and nome_arq.upper().strip() == nome_confhd) or (nome_compl and nome_compl.upper().strip() == nome_confhd):
                                    codigo_csv = c
                                    break
                    if codigo_csv is None:
                        codigo_csv = codigo_usina
            
            if codigo_usina is not None:
                debug_print(f"[TOOL] ✅ Filtro por usina: CONFHD={codigo_usina} CSV={codigo_csv}")
            
            # ETAPA 4: Processar dados de volume inicial
            debug_print("[TOOL] ETAPA 4: Processando dados de volume inicial...")
            dados_volume_inicial = None
            stats = None
            
            if confhd.usinas is not None:
                df_volume = confhd.usinas.copy()
                
                # Filtrar apenas colunas relevantes
                colunas_relevantes = ['codigo_usina', 'nome_usina', 'volume_inicial_percentual']
                colunas_disponiveis = [c for c in colunas_relevantes if c in df_volume.columns]
                df_volume = df_volume[colunas_disponiveis]
                
                # Aplicar filtro por usina se especificado
                if codigo_usina is not None:
                    df_volume = df_volume[df_volume['codigo_usina'] == codigo_usina]
                    debug_print(f"[TOOL] ✅ Dados filtrados por usina {codigo_usina}: {len(df_volume)} registros")
                
                # Converter para lista de dicts
                dados_volume_inicial = df_volume.to_dict(orient="records")
                
                # Converter tipos para JSON-serializable
                for record in dados_volume_inicial:
                    for key, value in record.items():
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, (int, float)):
                            # Garantir que números sejam float
                            record[key] = float(value) if value is not None else None
                
                # Calcular estatísticas
                if len(df_volume) > 0 and 'volume_inicial_percentual' in df_volume.columns:
                    stats = {
                        'total_usinas': len(df_volume),
                        'volume_medio': float(df_volume['volume_inicial_percentual'].mean()) if not df_volume['volume_inicial_percentual'].isna().all() else 0,
                        'volume_min': float(df_volume['volume_inicial_percentual'].min()) if not df_volume['volume_inicial_percentual'].isna().all() else 0,
                        'volume_max': float(df_volume['volume_inicial_percentual'].max()) if not df_volume['volume_inicial_percentual'].isna().all() else 0,
                    }
                
                debug_print(f"[TOOL] ✅ {len(dados_volume_inicial)} registros processados")
            else:
                debug_print("[TOOL] ⚠️ Nenhum dado de usinas disponível (confhd.usinas é None)")
            
            # ETAPA 5: Obter metadados da usina selecionada (sempre codigo_csv para follow-up)
            selected_plant = None
            if codigo_csv is not None:
                from backend.newave.utils.hydraulic_plant_matcher import get_hydraulic_plant_matcher
                matcher = get_hydraulic_plant_matcher()
                if codigo_csv in matcher.code_to_names:
                    nome_arquivo_csv, nome_completo_csv, _ = matcher.code_to_names[codigo_csv]
                    selected_plant = {
                        "type": "hydraulic",
                        "codigo": codigo_csv,
                        "nome": nome_arquivo_csv,
                        "nome_completo": nome_completo_csv if nome_completo_csv else nome_arquivo_csv,
                        "tool_name": self.get_name()
                    }
            
            # ETAPA 6: Formatar resultado
            debug_print("[TOOL] ETAPA 6: Formatando resultado...")
            
            # Informações sobre filtros aplicados
            filtro_info = {}
            if codigo_usina is not None:
                if confhd.usinas is not None:
                    usina_info = confhd.usinas[confhd.usinas['codigo_usina'] == codigo_usina]
                    if not usina_info.empty:
                        filtro_info['usina'] = {
                            'codigo': codigo_usina,
                            'nome': usina_info.iloc[0].get('nome_usina', f'Usina {codigo_usina}'),
                        }
            
            result = {
                "success": True,
                "dados_volume_inicial": dados_volume_inicial,
                "filtros": filtro_info if filtro_info else None,
                "stats": stats,
                "description": "Volume inicial percentual (v.inic) por usina do CONFHD.DAT",
                "tool": self.get_name()
            }
            
            # Adicionar metadados da usina selecionada se disponível
            if selected_plant:
                result["selected_plant"] = selected_plant
            
            return result
            
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
                "error": f"Erro ao processar CONFHD.DAT: {str(e)}",
                "error_type": type(e).__name__,
                "tool": self.get_name()
            }
    
    def get_description(self) -> str:
        """
        Retorna descrição da tool para uso pelo LLM.
        
        Returns:
            String com descrição detalhada
        """
        return """Volume inicial percentual V.INIC reservatórios CONFHD.DAT usina hidrelétrica."""

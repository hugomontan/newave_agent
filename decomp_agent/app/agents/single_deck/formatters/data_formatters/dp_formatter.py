"""
Formatter específico para DPCargaSubsistemasTool (Bloco DP do DECOMP).
"""

from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter


class DPSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da DPCargaSubsistemasTool.
    Formata dados do Bloco DP (Carga dos Subsistemas) do DECOMP.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da DPCargaSubsistemasTool."""
        return tool_name == "DPCargaSubsistemasTool" or "dp" in tool_name.lower()
    
    def get_priority(self) -> int:
        """Prioridade alta para esta tool específica."""
        return 90
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta da DPCargaSubsistemasTool.
        
        Args:
            tool_result: Resultado da execução da tool
            tool_name: Nome da tool
            query: Query original do usuário
            
        Returns:
            Dict com final_response e visualization_data
        """
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"## Erro ao Consultar Bloco DP\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        total_registros = tool_result.get("total_registros", len(data))
        filtros = tool_result.get("filtros", {})
        calcular_media = tool_result.get("calcular_media_ponderada", False)
        
        if not data:
            return {
                "final_response": "## Bloco DP - Carga dos Subsistemas\n\nNenhum registro encontrado com os filtros especificados.",
                "visualization_data": None
            }
        
        # 🔒 FILTRO DE SEGURANÇA: Filtrar dados antes de normalizar
        # Garantir que apenas dados do submercado/estágio solicitado sejam processados
        data_filtrada = data
        if filtros:
            codigo_submercado_filtro = filtros.get("codigo_submercado")
            estagio_filtro = filtros.get("estagio")
            
            if codigo_submercado_filtro is not None or estagio_filtro is not None:
                data_filtrada = []
                for registro in data:
                    # Verificar submercado (comparar como números para evitar problemas de tipo)
                    if codigo_submercado_filtro is not None:
                        codigo_submercado_reg = (
                            registro.get("codigo_submercado") or 
                            registro.get("submercado") or 
                            registro.get("s")
                        )
                        # Converter ambos para float para comparação segura
                        try:
                            if float(codigo_submercado_reg) != float(codigo_submercado_filtro):
                                continue  # Pular registros de outros submercados
                        except (ValueError, TypeError):
                            # Se não conseguir converter, usar comparação direta
                            if codigo_submercado_reg != codigo_submercado_filtro:
                                continue
                    
                    # Verificar estágio (comparar como números para evitar problemas de tipo)
                    if estagio_filtro is not None:
                        estagio_reg = (
                            registro.get("estagio") or 
                            registro.get("ip")
                        )
                        # Converter ambos para float para comparação segura
                        try:
                            if float(estagio_reg) != float(estagio_filtro):
                                continue  # Pular registros de outros estágios
                        except (ValueError, TypeError):
                            # Se não conseguir converter, usar comparação direta
                            if estagio_reg != estagio_filtro:
                                continue
                    
                    data_filtrada.append(registro)
        
        # Normalizar dados para formato padronizado
        normalized_data = self._normalize_data(data_filtrada)
        
        # Extrair MW médios se houver cálculo (usar dados filtrados)
        mw_medios = []
        if calcular_media:
            from decomp_agent.app.config import safe_print
            safe_print(f"[DP FORMATTER] Extraindo MW médios de {len(data_filtrada)} registros")
            for idx, registro in enumerate(data_filtrada):
                safe_print(f"[DP FORMATTER] Registro {idx+1}: chaves={list(registro.keys())}")
                mw_medio = registro.get("mw_medio") or registro.get("carga_media_ponderada")
                safe_print(f"[DP FORMATTER] MW médio encontrado: {mw_medio}")
                if mw_medio is not None:
                    estagio = registro.get("estagio") or registro.get("ip")
                    codigo_submercado = registro.get("codigo_submercado") or registro.get("submercado") or registro.get("s")
                    mw_medios.append({
                        "estagio": estagio,
                        "codigo_submercado": codigo_submercado,
                        "mw_medio": mw_medio
                    })
                    safe_print(f"[DP FORMATTER] ✅ MW médio adicionado: {mw_medio} (Estágio {estagio}, Submercado {codigo_submercado})")
            safe_print(f"[DP FORMATTER] Total de MW médios extraídos: {len(mw_medios)}")
        
        # Construir resposta em Markdown
        response_parts = []
        
        # Título baseado no tipo de consulta
        if calcular_media:
            if filtros.get("codigo_submercado") and filtros.get("estagio"):
                response_parts.append(f"## Carga Média Ponderada - Submercado {filtros['codigo_submercado']}, Estágio {filtros['estagio']}\n\n")
            elif filtros.get("codigo_submercado"):
                response_parts.append(f"## Carga Média Ponderada - Submercado {filtros['codigo_submercado']}\n\n")
            elif filtros.get("estagio"):
                response_parts.append(f"## Carga Média Ponderada - Estágio {filtros['estagio']}\n\n")
            else:
                response_parts.append("## Carga Média Ponderada\n\n")
        else:
            # Se filtrado por submercado ou estágio específico
            if filtros.get("codigo_submercado"):
                response_parts.append(f"## Bloco DP - Submercado {filtros['codigo_submercado']}\n\n")
                response_parts.append(f"Total de registros: {total_registros}\n\n")
            elif filtros.get("estagio"):
                response_parts.append(f"## Bloco DP - Estágio {filtros['estagio']}\n\n")
                response_parts.append(f"Total de registros: {total_registros}\n\n")
            else:
                # Sem filtro - resposta completa
                response_parts.append("## Bloco DP - Carga dos Subsistemas\n\n")
                response_parts.append(f"**Total de registros encontrados**: {total_registros}\n\n")
        
        # Dados de visualização
        visualization_data = {
            "table": normalized_data,
            "chart_data": None,
            "visualization_type": "table_with_summary" if calcular_media and mw_medios else "table_only",
            "tool_name": tool_name,
            "filtros": {
                "submercado": filtros.get("codigo_submercado"),
                "estagio": filtros.get("estagio"),
                "numero_patamares": filtros.get("numero_patamares"),
            } if filtros else None,
        }
        
        # Adicionar MW médios se houver cálculo
        if calcular_media and mw_medios:
            visualization_data["mw_medios"] = mw_medios
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza os dados da carga dos subsistemas para um formato consistente.
        Expande patamares em linhas separadas para melhor visualização.
        
        Args:
            data: Lista de dicionários com dados da carga
            
        Returns:
            Lista de dicionários normalizados (expandidos por patamar)
        """
        from decomp_agent.app.config import safe_print
        
        normalized = []
        
        # DEBUG: Verificar estrutura dos dados recebidos
        if data and len(data) > 0:
            safe_print(f"[DP FORMATTER] Primeiro registro recebido: {data[0]}")
            safe_print(f"[DP FORMATTER] Chaves disponíveis: {list(data[0].keys())}")
        
        # Mapeamento de índices de patamar para nomes
        patamar_names = {
            1: "PESADA",
            2: "MEDIA",
            3: "LEVE"
        }
        
        for registro in data:
            # Tentar múltiplas variações de nomes de campos
            estagio = (
                registro.get("estagio") or 
                registro.get("ip") or
                registro.get("estagio")
            )
            codigo_submercado = (
                registro.get("codigo_submercado") or 
                registro.get("submercado") or 
                registro.get("s") or
                registro.get("codigo_submercado")
            )
            numero_patamares = (
                registro.get("numero_patamares") or 
                registro.get("patamares") or 
                registro.get("pat") or
                registro.get("numero_patamares") or
                3
            )
            
            # Expandir por patamar (1, 2, 3)
            for patamar_idx in [1, 2, 3]:
                if patamar_idx > numero_patamares:
                    continue  # Pular patamares além do número especificado
                
                patamar_nome = patamar_names.get(patamar_idx, f"PATAMAR_{patamar_idx}")
                
                # Primeiro, tentar usar dados de patamares se houver cálculo de média
                demanda = None
                duracao = None
                
                patamares_dict = registro.get("patamares", {})
                if patamares_dict:
                    patamar_key = {1: "pesada", 2: "media", 3: "leve"}.get(patamar_idx)
                    if patamar_key and patamar_key in patamares_dict:
                        patamar_data = patamares_dict[patamar_key]
                        if isinstance(patamar_data, dict):
                            demanda = patamar_data.get("demanda_mwmed")
                            duracao = patamar_data.get("duracao_horas")
                
                # Se não encontrou nos patamares, tentar variações de nomes de campos
                if demanda is None:
                    # Tentar TODAS as variações possíveis de nomes de campos
                    # Para demanda (MWmed) - baseado no formato do arquivo: MWmed Pat_1, MWmed Pat_2, etc.
                    # O idecomp pode usar nomes como: demanda_1, demanda_2, demanda_3 ou mwmed_1, mwmed_2, mwmed_3
                    for prefix in ["demanda_patamar_", "demanda_", "mwmed_", "mwmed_patamar_", "mwmed_pat", 
                                   "demanda_pat", "carga_patamar_", "carga_"]:
                        for suffix in [f"{patamar_idx}", f"patamar_{patamar_idx}", f"pat{patamar_idx}", 
                                       f"patamar{patamar_idx}"]:
                            key = f"{prefix}{suffix}"
                            if key in registro and registro[key] is not None:
                                demanda = registro[key]
                                break
                        if demanda is not None:
                            break
                    
                    # Se ainda não encontrou, tentar acessar diretamente por índice (caso seja lista)
                    if demanda is None:
                        # Tentar acessar como lista ordenada: [estagio, submercado, patamares, demanda_1, horas_1, demanda_2, horas_2, ...]
                        if isinstance(registro, dict):
                            # Tentar chaves numéricas ou com padrões diferentes
                            for key, value in registro.items():
                                if value is not None and isinstance(value, (int, float)):
                                    # Verificar se a chave sugere que é demanda do patamar
                                    key_lower = str(key).lower()
                                    if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                                        f"_{patamar_idx}" in key_lower) and ("demanda" in key_lower or "mwmed" in key_lower or "carga" in key_lower):
                                        if "hora" not in key_lower and "duracao" not in key_lower:
                                            demanda = value
                                            break
                
                # Para duração (horas) - baseado no formato: Pat_1(h), Pat_2(h), etc.
                if duracao is None:
                    # Tentar todas as variações possíveis
                    for prefix in ["duracao_patamar_", "duracao_", "horas_", "horas_patamar_", "duracao_pat", 
                                   "horas_pat", "pat_"]:
                        for suffix in [f"{patamar_idx}", f"patamar_{patamar_idx}", f"pat{patamar_idx}", 
                                       f"patamar{patamar_idx}", f"{patamar_idx}_horas", f"{patamar_idx}h"]:
                            key = f"{prefix}{suffix}"
                            if key in registro and registro[key] is not None:
                                duracao = registro[key]
                                break
                        if duracao is not None:
                            break
                    
                    # Se ainda não encontrou, tentar acessar diretamente
                    if duracao is None:
                        if isinstance(registro, dict):
                            for key, value in registro.items():
                                if value is not None and isinstance(value, (int, float)):
                                    key_lower = str(key).lower()
                                    if (f"pat{patamar_idx}" in key_lower or f"patamar{patamar_idx}" in key_lower or 
                                        f"_{patamar_idx}" in key_lower) and ("hora" in key_lower or "duracao" in key_lower):
                                        duracao = value
                                        break
                
                normalized_record = {
                    "estagio": estagio,
                    "codigo_submercado": codigo_submercado,
                    "numero_patamares": numero_patamares,
                    "patamar": patamar_nome,
                    "patamar_numero": patamar_idx,
                    "demanda_mwmed": demanda,
                    "duracao_horas": duracao,
                }
                
                # Apenas adicionar se houver dados relevantes
                if normalized_record.get("demanda_mwmed") is not None or \
                   normalized_record.get("duracao_horas") is not None:
                    normalized.append(normalized_record)
        
        safe_print(f"[DP FORMATTER] Total de registros normalizados: {len(normalized)}")
        if normalized and len(normalized) > 0:
            safe_print(f"[DP FORMATTER] Primeiro registro normalizado: {normalized[0]}")
        
        return normalized

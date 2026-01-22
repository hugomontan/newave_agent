"""
Formatter específico para GLGeracoesGNLTool (Gerações de Termelétricas GNL já Comandadas).
"""
from typing import Dict, Any, List, Optional
from decomp_agent.app.agents.single_deck.formatters.base import SingleDeckFormatter
from decomp_agent.app.config import safe_print
from datetime import datetime


class GLSingleDeckFormatter(SingleDeckFormatter):
    """
    Formatter específico para resultados da GLGeracoesGNLTool.
    Formata dados de gerações GNL já comandadas com tabela e 3 gráficos (um por patamar).
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar resultados da GLGeracoesGNLTool."""
        return tool_name == "GLGeracoesGNLTool" or "gl" in tool_name.lower()
    
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
        Formata resposta da GLGeracoesGNLTool.
        
        Args:
            tool_result: Resultado da execução da tool
            tool_name: Nome da tool
            query: Query original do usuário
            
        Returns:
            Dict com final_response e visualization_data (tabela + 3 gráficos)
        """
        if not tool_result.get("success", False):
            error = tool_result.get("error", "Erro desconhecido")
            return {
                "final_response": f"❌ **Erro ao Consultar Gerações GNL**\n\n{error}",
                "visualization_data": None
            }
        
        data = tool_result.get("data", [])
        codigo_usina = tool_result.get("codigo_usina")
        nome_usina = tool_result.get("nome_usina")
        
        if not data:
            return {
                "final_response": "❌ **Nenhum Dado Encontrado**\n\nNenhum registro GL encontrado.",
                "visualization_data": None
            }
        
        # Processar e ordenar dados por data_inicio
        table_data = []
        for record in data:
            data_inicio_raw = record.get("data_inicio")
            data_inicio_formatted = self._format_date(data_inicio_raw) if data_inicio_raw else None
            
            table_row = {
                "data_inicio": data_inicio_formatted,
                "data_inicio_raw": data_inicio_raw,  # Para ordenação
                "semana": record.get("semana") or record.get("estagio"),
                "estagio": record.get("estagio"),
                "geracao_patamar_1": record.get("geracao_patamar_1"),
                "geracao_patamar_2": record.get("geracao_patamar_2"),
                "geracao_patamar_3": record.get("geracao_patamar_3"),
                "duracao_patamar_1": record.get("duracao_patamar_1"),
                "duracao_patamar_2": record.get("duracao_patamar_2"),
                "duracao_patamar_3": record.get("duracao_patamar_3"),
                "codigo_usina": record.get("codigo_usina"),
                "codigo_submercado": record.get("codigo_submercado"),
            }
            table_data.append(table_row)
        
        # Ordenar por data_inicio (usando data_inicio_raw para ordenação cronológica)
        table_data.sort(key=lambda x: self._parse_date_for_sort(x.get("data_inicio_raw", "")))
        
        # Criar 3 gráficos (um por patamar)
        charts_by_patamar = {}
        
        for patamar_num in [1, 2, 3]:
            patamar_nome = {1: "PESADA", 2: "MÉDIA", 3: "LEVE"}[patamar_num]
            patamar_key = f"patamar_{patamar_num}"
            
            # Extrair labels (datas) e valores (geração) para este patamar
            chart_labels = []
            chart_values = []
            
            for row in table_data:
                data_inicio = row.get("data_inicio")
                geracao = row.get(f"geracao_patamar_{patamar_num}")
                
                if data_inicio:
                    chart_labels.append(data_inicio)
                    # Incluir valores zero (0.0) - são válidos
                    chart_values.append(geracao if geracao is not None else None)
            
            # Criar chart_data para este patamar
            chart_data = {
                "labels": chart_labels,
                "datasets": [{
                    "label": f"Geração Patamar {patamar_num} ({patamar_nome})",
                    "data": chart_values,
                    "borderColor": {
                        1: "rgb(239, 68, 68)",   # red-500 - PESADA
                        2: "rgb(234, 179, 8)",   # yellow-500 - MÉDIA
                        3: "rgb(34, 197, 94)"    # green-500 - LEVE
                    }[patamar_num],
                    "backgroundColor": {
                        1: "rgba(239, 68, 68, 0.1)",
                        2: "rgba(234, 179, 8, 0.1)",
                        3: "rgba(34, 197, 94, 0.1)"
                    }[patamar_num],
                    "tension": 0.1
                }]
            } if chart_labels else None
            
            charts_by_patamar[patamar_key] = {
                "patamar": patamar_nome,
                "patamar_numero": patamar_num,
                "chart_data": chart_data,
                "chart_config": {
                    "type": "line",
                    "title": f"Evolução da Geração - Patamar {patamar_num} ({patamar_nome})",
                    "x_axis": "Data",
                    "y_axis": "Geração (MW)"
                }
            }
        
        # Resposta mínima - toda informação está na visualização
        nome_usina_display = nome_usina if nome_usina else (f"Usina {codigo_usina}" if codigo_usina else "Usina")
        response_parts = []
        response_parts.append(f"## Gerações GNL já Comandadas - {nome_usina_display}\n\n")
        if codigo_usina:
            if nome_usina:
                response_parts.append(f"Usina: {nome_usina} (Código: {codigo_usina})\n\n")
            else:
                response_parts.append(f"Código: {codigo_usina}\n\n")
        response_parts.append(f"Total de registros: {len(table_data)}\n\n")
        
        # Preparar dados de visualização
        visualization_data = {
            "table": table_data,
            "charts_by_patamar": charts_by_patamar,
            "visualization_type": "gl_geracoes_gnl",
            "usina": {
                "codigo": codigo_usina,
                "nome": nome_usina
            },
            "tool_name": tool_name
        }
        
        safe_print(f"[GL FORMATTER] ✅ Tabela criada com {len(table_data)} linha(s)")
        safe_print(f"[GL FORMATTER] ✅ 3 gráficos criados (um por patamar)")
        safe_print(f"[GL FORMATTER] 📋 Dados da usina: codigo={codigo_usina}, nome={nome_usina}")
        
        return {
            "final_response": "".join(response_parts),
            "visualization_data": visualization_data
        }
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """
        Converte data de DDMMYYYY para DD/MM/YYYY.
        
        Args:
            date_str: Data no formato DDMMYYYY (ex: "03012026")
            
        Returns:
            Data formatada como DD/MM/YYYY (ex: "03/01/2026") ou None se inválida
        """
        if not date_str or len(date_str) != 8:
            return None
        
        try:
            day = date_str[0:2]
            month = date_str[2:4]
            year = date_str[4:8]
            return f"{day}/{month}/{year}"
        except Exception:
            return None
    
    def _parse_date_for_sort(self, date_str: str) -> str:
        """
        Converte data DDMMYYYY para formato ordenável (YYYYMMDD).
        
        Args:
            date_str: Data no formato DDMMYYYY (ex: "03012026")
            
        Returns:
            Data no formato YYYYMMDD (ex: "20260103") para ordenação, ou "99999999" se inválida
        """
        if not date_str or len(date_str) != 8:
            return "99999999"
        
        try:
            day = date_str[0:2]
            month = date_str[2:4]
            year = date_str[4:8]
            return f"{year}{month}{day}"  # YYYYMMDD para ordenação cronológica
        except Exception:
            return "99999999"

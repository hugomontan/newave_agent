"""
Formatador para VariacaoReservatorioInicialTool - volume inicial percentual por usina.
Visualização: Tabela comparativa + Gráfico de linha (deck vs deck)
"""
import math
from typing import Dict, Any, List, Optional
from app.agents.multi_deck.formatting.base import ComparisonFormatter


class VariacaoReservatorioInicialFormatter(ComparisonFormatter):
    """
    Formatador para VariacaoReservatorioInicialTool - volume inicial percentual por usina.
    Visualização: Tabela comparativa + Gráfico de linha (deck vs deck)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "VariacaoReservatorioInicialTool" and (
            "dados_volume_inicial" in result_structure
        )
    
    def get_priority(self) -> int:
        return 100  # Alta prioridade - muito específico
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de volume inicial percentual por usina.
        Compara valores entre dezembro e janeiro, criando tabela e gráfico.
        """
        dados_dec = result_dec.get("dados_volume_inicial", [])
        dados_jan = result_jan.get("dados_volume_inicial", [])
        
        if not dados_dec and not dados_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "reservatorio_inicial_table",
            }
        
        # Indexar por código da usina
        dec_indexed = {r.get("codigo_usina"): r for r in dados_dec if r.get("codigo_usina") is not None}
        jan_indexed = {r.get("codigo_usina"): r for r in dados_jan if r.get("codigo_usina") is not None}
        
        # Construir tabela comparativa
        comparison_table = []
        chart_datasets = []
        
        all_codigos = sorted(set(dec_indexed.keys()) | set(jan_indexed.keys()))
        
        for codigo in all_codigos:
            dec_record = dec_indexed.get(codigo, {})
            jan_record = jan_indexed.get(codigo, {})
            
            nome_usina = dec_record.get("nome_usina") or jan_record.get("nome_usina", f"Usina {codigo}")
            # Formato: "Nome da Usina (Código)" para confirmação visual
            usina_info = f"{nome_usina} ({codigo})"
            
            volume_dec = self._sanitize_number(dec_record.get("volume_inicial_percentual"))
            volume_jan = self._sanitize_number(jan_record.get("volume_inicial_percentual"))
            
            # Formato vertical: uma linha por deck
            # Linha para Dezembro 2025
            if volume_dec is not None:
                comparison_table.append({
                    "usina": usina_info,
                    "codigo_usina": codigo,
                    "data": "12-2025",  # MM-YYYY
                    "periodo": "Dezembro 2025",
                    "volume_inicial": round(volume_dec, 2)
                })
            
            # Linha para Janeiro 2026
            if volume_jan is not None:
                comparison_table.append({
                    "usina": usina_info,
                    "codigo_usina": codigo,
                    "data": "01-2026",  # MM-YYYY
                    "periodo": "Janeiro 2026",
                    "volume_inicial": round(volume_jan, 2)
                })
            
            # Adicionar ao gráfico (mantém formato original para o gráfico)
            if volume_dec is not None or volume_jan is not None:
                chart_datasets.append({
                    "label": usina_info,
                    "data": [
                        volume_dec if volume_dec is not None else None,
                        volume_jan if volume_jan is not None else None
                    ]
                })
        
        # Construir chart_data
        chart_data = {
            "labels": ["Dezembro 2025", "Janeiro 2026"],
            "datasets": chart_datasets
        } if chart_datasets else None
        
        return {
            "comparison_table": comparison_table,
            "chart_data": chart_data,
            "visualization_type": "reservatorio_inicial_table",
            "chart_config": {
                "type": "line",
                "title": "Volume Inicial Percentual por Usina",
                "x_axis": "Deck",
                "y_axis": "Volume Inicial (%)"
            }
        }
    
    def _sanitize_number(self, value: Any) -> Optional[float]:
        """
        Sanitiza número, convertendo para float ou retornando None.
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                return None
            return float(value)
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None
            return num
        except (ValueError, TypeError):
            return None

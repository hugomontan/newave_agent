"""
Formatador de tabela para comparação multi-deck.
Para tools que retornam dados em formato tabular simples.
"""
from typing import Dict, Any, List, Optional
from app.comparison.base import ComparisonFormatter


class TableComparisonFormatter(ComparisonFormatter):
    """
    Formatador para ConfhdTool.
    Visualização: Tabela lado a lado destacando mudanças
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "ConfhdTool" and "dados_usina" in result_structure
    
    def get_priority(self) -> int:
        return 60
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de configuração (CONFHD).
        Tabela lado a lado destacando campos que mudaram.
        """
        dados_dec = result_dec.get("dados_usina", {})
        dados_jan = result_jan.get("dados_usina", {})
        
        if not dados_dec and not dados_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "side_by_side_table"
            }
        
        # Construir tabela comparativa
        comparison_table = []
        
        all_keys = set(dados_dec.keys()) | set(dados_jan.keys())
        
        # Ordenar campos: campos importantes primeiro
        campos_importantes = [
            "codigo_usina", "nome_usina", "ree", "status",
            "volume_inicial_percentual", "posto"
        ]
        
        keys_ordered = [k for k in campos_importantes if k in all_keys]
        keys_ordered.extend([k for k in sorted(all_keys) if k not in campos_importantes])
        
        for key in keys_ordered:
            val_dec = dados_dec.get(key)
            val_jan = dados_jan.get(key)
            
            changed = val_dec != val_jan
            
            # Para valores numéricos, considerar mudança se diferença > 0.01
            if isinstance(val_dec, (int, float)) and isinstance(val_jan, (int, float)):
                changed = abs(float(val_dec) - float(val_jan)) > 0.01
            
            comparison_table.append({
                "campo": key,
                "deck_1_value": val_dec,
                "deck_2_value": val_jan,
                "changed": changed
            })
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "side_by_side_table"
        }


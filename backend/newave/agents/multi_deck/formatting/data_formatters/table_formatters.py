"""
Formatador de tabela para comparação multi-deck.
Para tools que retornam dados em formato tabular simples.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List, Optional
from backend.newave.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class TableComparisonFormatter(ComparisonFormatter):
    """
    Formatador para ConfhdTool.
    Visualização: Tabela lado a lado destacando mudanças
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name == "ConfhdTool" and "dados_usina" in result_structure
    
    def get_priority(self) -> int:
        return 60
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de configuração para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "visualization_type": "side_by_side_table",
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        all_keys = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados = result.get("dados_usina", {})
            all_keys.update(dados.keys())
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "dados": dados
            })
        
        # Ordenar campos: campos importantes primeiro
        campos_importantes = [
            "codigo_usina", "nome_usina", "ree", "status",
            "volume_inicial_percentual", "posto"
        ]
        
        keys_ordered = [k for k in campos_importantes if k in all_keys]
        keys_ordered.extend([k for k in sorted(all_keys) if k not in campos_importantes])
        
        # Construir tabela comparativa com N colunas
        comparison_table = []
        for key in keys_ordered:
            table_row = {"campo": key}
            
            # Verificar se algum valor mudou
            values = []
            for deck_idx, deck_info in enumerate(decks_info):
                val = deck_info["dados"].get(key)
                values.append(val)
                table_row[f"deck_{deck_idx + 1}"] = val
            
            # Verificar se há mudanças
            changed = len(set(v for v in values if v is not None)) > 1
            
            # Para valores numéricos, considerar mudança se diferença > 0.01
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if len(numeric_values) > 1:
                changed = any(abs(float(numeric_values[0]) - float(v)) > 0.01 for v in numeric_values[1:])
            
            table_row["changed"] = changed
            comparison_table.append(table_row)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "side_by_side_table",
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _format_comparison_internal(
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


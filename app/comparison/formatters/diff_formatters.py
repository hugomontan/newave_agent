"""
Formatadores de diff para comparação multi-deck.
Para tools que listam modificações (adicionado/removido/alterado).
"""
from typing import Dict, Any, List, Optional, Tuple
from app.comparison.base import ComparisonFormatter


class DiffComparisonFormatter(ComparisonFormatter):
    """
    Formatador para ExptOperacaoTool e ModifOperacaoTool.
    Visualização: Lista de diferenças (added, removed, modified)
    Com liberdade para LLM interpretar os dados.
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name in ["ExptOperacaoTool", "ModifOperacaoTool"] and (
            "dados_expansoes" in result_structure or
            "dados_por_tipo" in result_structure
        )
    
    def get_priority(self) -> int:
        return 85
    
    def format_comparison(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de modificações (expansões/modificações).
        Gera estrutura de diff: added, removed, modified.
        """
        if tool_name == "ExptOperacaoTool":
            return self._format_expt(result_dec, result_jan, query)
        else:  # ModifOperacaoTool
            return self._format_modif(result_dec, result_jan, query)
    
    def _format_expt(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de dados do EXPT (expansões/modificações térmicas)."""
        dados_dec = result_dec.get("dados_expansoes", [])
        dados_jan = result_jan.get("dados_expansoes", [])
        
        # Chave primária: (codigo_usina, tipo, data_inicio ou período)
        dec_indexed = self._index_expt_records(dados_dec)
        jan_indexed = self._index_expt_records(dados_jan)
        
        # Computar diferenças
        added = []
        removed = []
        modified = []
        
        all_keys = set(dec_indexed.keys()) | set(jan_indexed.keys())
        
        for key in all_keys:
            dec_record = dec_indexed.get(key)
            jan_record = jan_indexed.get(key)
            
            if dec_record and not jan_record:
                removed.append(dec_record)
            elif jan_record and not dec_record:
                added.append(jan_record)
            elif dec_record and jan_record:
                # Comparar valores para ver se mudou
                if self._records_different(dec_record, jan_record):
                    modified.append({
                        "original": dec_record,
                        "modified": jan_record
                    })
        
        return {
            "comparison_table": None,  # Não usar tabela padrão
            "chart_data": None,  # Sem gráfico
            "visualization_type": "diff_list",
            "diff_categories": {
                "added": added,
                "removed": removed,
                "modified": modified
            },
            "llm_context": {
                "tool_type": "expt",
                "total_added": len(added),
                "total_removed": len(removed),
                "total_modified": len(modified)
            }
        }
    
    def _format_modif(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de dados do MODIF (modificações hídricas)."""
        dados_por_tipo_dec = result_dec.get("dados_por_tipo", {})
        dados_por_tipo_jan = result_jan.get("dados_por_tipo", {})
        
        # Para MODIF, dados estão organizados por tipo (VOLMIN, VAZMIN, etc)
        all_types = set(dados_por_tipo_dec.keys()) | set(dados_por_tipo_jan.keys())
        
        diff_by_type = {}
        
        for tipo in all_types:
            dados_dec = dados_por_tipo_dec.get(tipo, [])
            dados_jan = dados_por_tipo_jan.get(tipo, [])
            
            # Indexar por chave primária apropriada
            dec_indexed = self._index_modif_records(dados_dec, tipo)
            jan_indexed = self._index_modif_records(dados_jan, tipo)
            
            added = []
            removed = []
            modified = []
            
            all_keys = set(dec_indexed.keys()) | set(jan_indexed.keys())
            
            for key in all_keys:
                dec_record = dec_indexed.get(key)
                jan_record = jan_indexed.get(key)
                
                if dec_record and not jan_record:
                    removed.append(dec_record)
                elif jan_record and not dec_record:
                    added.append(jan_record)
                elif dec_record and jan_record:
                    if self._records_different(dec_record, jan_record):
                        modified.append({
                            "original": dec_record,
                            "modified": jan_record
                        })
            
            if added or removed or modified:
                diff_by_type[tipo] = {
                    "added": added,
                    "removed": removed,
                    "modified": modified
                }
        
        return {
            "comparison_table": None,
            "chart_data": None,
            "visualization_type": "diff_list",
            "diff_categories": diff_by_type,
            "llm_context": {
                "tool_type": "modif",
                "types_affected": list(diff_by_type.keys()),
                "total_changes": sum(
                    len(v["added"]) + len(v["removed"]) + len(v["modified"])
                    for v in diff_by_type.values()
                )
            }
        }
    
    def _index_expt_records(self, records: List[Dict]) -> Dict[str, Dict]:
        """Indexa registros do EXPT por chave primária."""
        index = {}
        for record in records:
            codigo = record.get("codigo_usina")
            tipo = record.get("tipo")
            data_inicio = record.get("data_inicio")
            
            # Criar chave primária
            if codigo is not None and tipo:
                key_parts = [str(codigo), str(tipo)]
                if data_inicio:
                    key_parts.append(str(data_inicio))
                key = "|".join(key_parts)
                index[key] = record
        return index
    
    def _index_modif_records(self, records: List[Dict], tipo: str) -> Dict[str, Dict]:
        """Indexa registros do MODIF por chave primária."""
        index = {}
        for record in records:
            codigo = record.get("codigo_usina") or record.get("codigo")
            # Para MODIF, chave pode incluir volume, vazão, nível, etc dependendo do tipo
            key_parts = [str(codigo), tipo]
            
            # Adicionar campos específicos do tipo à chave
            if "volume" in record:
                key_parts.append(str(record.get("volume")))
            if "vazao" in record:
                key_parts.append(str(record.get("vazao")))
            if "nivel" in record:
                key_parts.append(str(record.get("nivel")))
            
            key = "|".join(key_parts)
            index[key] = record
        return index
    
    def _records_different(self, record1: Dict, record2: Dict) -> bool:
        """Verifica se dois registros são diferentes."""
        # Comparar campos numéricos relevantes
        numeric_fields = ["valor", "volume", "vazao", "nivel", "custo", "potencia"]
        
        for field in numeric_fields:
            val1 = record1.get(field)
            val2 = record2.get(field)
            
            if val1 is not None and val2 is not None:
                try:
                    if abs(float(val1) - float(val2)) > 0.01:  # Tolerância para comparação
                        return True
                except (ValueError, TypeError):
                    pass
        
        return False


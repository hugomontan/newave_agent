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
        """
        Formata comparação de dados do EXPT (expansões/modificações térmicas).
        Formato hierárquico: por tipo e por usina, apenas tabelas.
        """
        dados_dec = result_dec.get("dados_expansoes", [])
        dados_jan = result_jan.get("dados_expansoes", [])
        
        # Chave primária: (codigo_usina, tipo, data_inicio)
        dec_indexed = self._index_expt_records(dados_dec)
        jan_indexed = self._index_expt_records(dados_jan)
        
        # Organizar por tipo
        comparison_by_type = {}
        all_types = set()
        
        # Coletar todos os tipos
        for record in dados_dec + dados_jan:
            tipo = record.get("tipo")
            if tipo:
                all_types.add(tipo)
        
        # Processar cada tipo
        for tipo in sorted(all_types):
            tipo_records_dec = [r for r in dados_dec if r.get("tipo") == tipo]
            tipo_records_jan = [r for r in dados_jan if r.get("tipo") == tipo]
            
            # Indexar registros deste tipo
            tipo_dec_indexed = {k: v for k, v in dec_indexed.items() if v.get("tipo") == tipo}
            tipo_jan_indexed = {k: v for k, v in jan_indexed.items() if v.get("tipo") == tipo}
            
            # Construir tabela comparativa para este tipo
            tipo_table = []
            tipo_added = []
            tipo_removed = []
            tipo_modified = []
            
            all_tipo_keys = set(tipo_dec_indexed.keys()) | set(tipo_jan_indexed.keys())
            
            for key in sorted(all_tipo_keys):
                dec_record = tipo_dec_indexed.get(key)
                jan_record = tipo_jan_indexed.get(key)
                
                codigo_usina = dec_record.get("codigo_usina") if dec_record else (jan_record.get("codigo_usina") if jan_record else None)
                nome_usina = dec_record.get("nome_usina") if dec_record else (jan_record.get("nome_usina") if jan_record else "N/A")
                data_inicio = dec_record.get("data_inicio") if dec_record else (jan_record.get("data_inicio") if jan_record else None)
                data_fim = dec_record.get("data_fim") if dec_record else (jan_record.get("data_fim") if jan_record else None)
                
                modificacao_dec = dec_record.get("modificacao") if dec_record else None
                modificacao_jan = jan_record.get("modificacao") if jan_record else None
                
                # Formatar datas
                data_inicio_str = self._format_date(data_inicio)
                data_fim_str = self._format_date(data_fim)
                
                # Calcular diferenças
                difference = None
                difference_percent = None
                status = "unchanged"
                
                if dec_record and not jan_record:
                    status = "removed"
                    tipo_removed.append(dec_record)
                elif jan_record and not dec_record:
                    status = "added"
                    tipo_added.append(jan_record)
                elif dec_record and jan_record:
                    if self._records_different(dec_record, jan_record):
                        status = "modified"
                        tipo_modified.append({
                            "original": dec_record,
                            "modified": jan_record
                        })
                        
                        # Calcular diferenças numéricas
                        if modificacao_dec is not None and modificacao_jan is not None:
                            try:
                                diff_val = float(modificacao_jan) - float(modificacao_dec)
                                difference = round(diff_val, 2)
                                if float(modificacao_dec) != 0:
                                    diff_pct = (diff_val / float(modificacao_dec)) * 100
                                    difference_percent = round(diff_pct, 2)
                                else:
                                    difference_percent = 0.0
                            except (ValueError, TypeError):
                                pass
                
                # Adicionar à tabela
                tipo_table.append({
                    "codigo_usina": codigo_usina,
                    "nome_usina": nome_usina,
                    "tipo": tipo,
                    "data_inicio": data_inicio_str,
                    "data_fim": data_fim_str,
                    "deck_1_value": self._safe_float(modificacao_dec),
                    "deck_2_value": self._safe_float(modificacao_jan),
                    "difference": difference,
                    "difference_percent": difference_percent,
                    "status": status
                })
            
            # Resumo por tipo
            summary = {
                "total_dezembro": len(tipo_records_dec),
                "total_janeiro": len(tipo_records_jan),
                "added_count": len(tipo_added),
                "removed_count": len(tipo_removed),
                "modified_count": len(tipo_modified)
            }
            
            comparison_by_type[tipo] = {
                "comparison_table": tipo_table,
                "summary": summary,
                "diff_categories": {
                    "added": tipo_added,
                    "removed": tipo_removed,
                    "modified": tipo_modified
                }
            }
        
        # Organizar por usina
        comparison_by_usina = {}
        all_usinas = set()
        
        # Coletar todas as usinas
        for record in dados_dec + dados_jan:
            codigo = record.get("codigo_usina")
            if codigo is not None:
                all_usinas.add(codigo)
        
        # Processar cada usina
        for codigo_usina in sorted(all_usinas):
            usina_records_dec = [r for r in dados_dec if r.get("codigo_usina") == codigo_usina]
            usina_records_jan = [r for r in dados_jan if r.get("codigo_usina") == codigo_usina]
            
            # Obter nome da usina
            nome_usina = None
            for record in usina_records_dec + usina_records_jan:
                nome = record.get("nome_usina")
                if nome:
                    nome_usina = nome
                    break
            if not nome_usina:
                nome_usina = f"Usina {codigo_usina}"
            
            # Indexar registros desta usina
            usina_dec_indexed = {k: v for k, v in dec_indexed.items() if v.get("codigo_usina") == codigo_usina}
            usina_jan_indexed = {k: v for k, v in jan_indexed.items() if v.get("codigo_usina") == codigo_usina}
            
            # Construir tabela comparativa para esta usina
            usina_table = []
            usina_added = []
            usina_removed = []
            usina_modified = []
            
            all_usina_keys = set(usina_dec_indexed.keys()) | set(usina_jan_indexed.keys())
            
            for key in sorted(all_usina_keys):
                dec_record = usina_dec_indexed.get(key)
                jan_record = usina_jan_indexed.get(key)
                
                tipo = dec_record.get("tipo") if dec_record else (jan_record.get("tipo") if jan_record else None)
                data_inicio = dec_record.get("data_inicio") if dec_record else (jan_record.get("data_inicio") if jan_record else None)
                data_fim = dec_record.get("data_fim") if dec_record else (jan_record.get("data_fim") if jan_record else None)
                
                modificacao_dec = dec_record.get("modificacao") if dec_record else None
                modificacao_jan = jan_record.get("modificacao") if jan_record else None
                
                # Formatar datas
                data_inicio_str = self._format_date(data_inicio)
                data_fim_str = self._format_date(data_fim)
                
                # Calcular diferenças
                difference = None
                difference_percent = None
                status = "unchanged"
                
                if dec_record and not jan_record:
                    status = "removed"
                    usina_removed.append(dec_record)
                elif jan_record and not dec_record:
                    status = "added"
                    usina_added.append(jan_record)
                elif dec_record and jan_record:
                    if self._records_different(dec_record, jan_record):
                        status = "modified"
                        usina_modified.append({
                            "original": dec_record,
                            "modified": jan_record
                        })
                        
                        # Calcular diferenças numéricas
                        if modificacao_dec is not None and modificacao_jan is not None:
                            try:
                                diff_val = float(modificacao_jan) - float(modificacao_dec)
                                difference = round(diff_val, 2)
                                if float(modificacao_dec) != 0:
                                    diff_pct = (diff_val / float(modificacao_dec)) * 100
                                    difference_percent = round(diff_pct, 2)
                                else:
                                    difference_percent = 0.0
                            except (ValueError, TypeError):
                                pass
                
                # Adicionar à tabela
                usina_table.append({
                    "tipo": tipo,
                    "data_inicio": data_inicio_str,
                    "data_fim": data_fim_str,
                    "deck_1_value": self._safe_float(modificacao_dec),
                    "deck_2_value": self._safe_float(modificacao_jan),
                    "difference": difference,
                    "difference_percent": difference_percent,
                    "status": status
                })
            
            # Resumo por usina
            summary = {
                "total_modificacoes_dezembro": len(usina_records_dec),
                "total_modificacoes_janeiro": len(usina_records_jan),
                "novas_modificacoes": len(usina_added),
                "modificacoes_removidas": len(usina_removed),
                "modificacoes_alteradas": len(usina_modified)
            }
            
            comparison_by_usina[str(codigo_usina)] = {
                "codigo_usina": codigo_usina,
                "nome_usina": nome_usina,
                "comparison_table": usina_table,
                "summary": summary,
                "modificacoes": {
                    "added": usina_added,
                    "removed": usina_removed,
                    "modified": usina_modified
                }
            }
        
        # Calcular totais gerais
        total_added = sum(len(v["diff_categories"]["added"]) for v in comparison_by_type.values())
        total_removed = sum(len(v["diff_categories"]["removed"]) for v in comparison_by_type.values())
        total_modified = sum(len(v["diff_categories"]["modified"]) for v in comparison_by_type.values())
        
        return {
            "comparison_table": None,  # Não usar tabela padrão única
            "chart_data": None,  # Sem gráficos
            "visualization_type": "expt_hierarchical",
            "comparison_by_type": comparison_by_type,
            "comparison_by_usina": comparison_by_usina,
            "llm_context": {
                "tool_type": "expt",
                "total_added": total_added,
                "total_removed": total_removed,
                "total_modified": total_modified,
                "tipos_afetados": list(all_types),
                "usinas_afetadas": len(all_usinas),
                "total_tipos": len(all_types),
                "total_usinas": len(all_usinas)
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
        numeric_fields = ["valor", "volume", "vazao", "nivel", "custo", "potencia", "modificacao"]
        
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
    
    def _format_date(self, date_value: Any) -> Optional[str]:
        """Formata uma data para string legível."""
        if date_value is None:
            return None
        
        try:
            # Se for string ISO
            if isinstance(date_value, str):
                if 'T' in date_value:
                    return date_value.split('T')[0]
                return date_value
            
            # Se for objeto datetime
            if hasattr(date_value, 'date'):
                return date_value.date().isoformat()
            if hasattr(date_value, 'isoformat'):
                return date_value.isoformat().split('T')[0]
            
            return str(date_value)
        except Exception:
            return str(date_value) if date_value else None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Converte um valor para float de forma segura."""
        if value is None:
            return None
        
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return None


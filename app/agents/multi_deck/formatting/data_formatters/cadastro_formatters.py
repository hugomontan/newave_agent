"""
Formatadores de cadastro para comparação multi-deck.
Para tools que retornam dados cadastrais de usinas.
Suporta N decks para comparação dinâmica.
"""
from typing import Dict, Any, List, Optional
from app.agents.multi_deck.formatting.base import ComparisonFormatter, DeckData


class CadastroComparisonFormatter(ComparisonFormatter):
    """
    Formatador para HidrCadastroTool e TermCadastroTool.
    Visualização: Cards comparativos por usina (antes/depois)
    """
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        return tool_name in ["HidrCadastroTool", "TermCadastroTool"] and (
            "dados_usina" in result_structure
        )
    
    def get_priority(self) -> int:
        return 70
    
    def format_multi_deck_comparison(
        self,
        decks_data: List[DeckData],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata comparação de dados cadastrais para N decks."""
        if len(decks_data) < 2:
            return {
                "comparison_table": [],
                "visualization_type": "comparison_cards",
                "cards": [],
                "error": "São necessários pelo menos 2 decks para comparação"
            }
        
        # Extrair dados de todos os decks
        all_keys = set()
        decks_info = []
        
        for deck in decks_data:
            result = deck.result
            dados = result.get("dados_usina", {})
            all_keys.update(dados.keys() if dados else [])
            
            decks_info.append({
                "deck": deck,
                "display_name": deck.display_name,
                "dados": dados or {}
            })
        
        # Criar cards para cada deck
        cards = []
        for deck_info in decks_info:
            dados = deck_info["dados"]
            codigo = dados.get("codigo_usina") or dados.get("codigo")
            nome = dados.get("nome_usina") or dados.get("nome") or f"Usina {codigo}" if codigo else "N/A"
            
            cards.append({
                "usina": nome,
                "codigo": codigo,
                "deck": deck_info["display_name"],
                "dados": dados,
                "changed": False
            })
        
        # Identificar campos que mudaram entre todos os decks
        campos_alterados = self._identify_changed_fields_multi(decks_info)
        
        # Criar tabela comparativa com N colunas
        comparison_table = self._build_comparison_table_multi(decks_info, all_keys)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "comparison_cards",
            "cards": cards,
            "campos_alterados": campos_alterados,
            "deck_names": self.get_deck_names(decks_data),
            "is_multi_deck": len(decks_data) > 2
        }
    
    def _identify_changed_fields_multi(
        self,
        decks_info: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Identifica campos que mudaram entre todos os decks."""
        campos_alterados = []
        all_keys = set()
        
        for deck_info in decks_info:
            all_keys.update(deck_info["dados"].keys())
        
        for key in all_keys:
            values = [deck_info["dados"].get(key) for deck_info in decks_info]
            
            # Verificar se há mudanças
            if len(set(v for v in values if v is not None)) > 1:
                # Para valores numéricos, considerar mudança se diferença > 0.01
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                if len(numeric_values) > 1:
                    if any(abs(float(numeric_values[0]) - float(v)) > 0.01 for v in numeric_values[1:]):
                        campos_alterados.append({
                            "campo": key,
                            "values": {f"deck_{i+1}": val for i, val in enumerate(values)}
                        })
                else:
                    campos_alterados.append({
                        "campo": key,
                        "values": {f"deck_{i+1}": val for i, val in enumerate(values)}
                    })
        
        return campos_alterados
    
    def _build_comparison_table_multi(
        self,
        decks_info: List[Dict],
        all_keys: set
    ) -> List[Dict[str, Any]]:
        """Constrói tabela comparativa com N colunas."""
        table = []
        
        # Campos principais para comparar
        campos_principais = [
            "codigo_usina", "codigo", "nome_usina", "nome",
            "potencia", "potencia_instalada", "potencia_efetiva",
            "volume_maximo", "volume_util", "volume_minimo",
            "vazao_maxima", "vazao_minima",
            "fator_capacidade", "fcmax",
            "indisponibilidade", "teif", "ip"
        ]
        
        # Priorizar campos principais
        keys_to_compare = list(set(campos_principais) & all_keys)
        keys_to_compare.extend([k for k in all_keys if k not in campos_principais])
        
        for key in keys_to_compare[:30]:  # Limitar a 30 campos
            table_row = {"campo": key}
            
            # Adicionar valores de cada deck
            values = []
            for deck_idx, deck_info in enumerate(decks_info):
                val = deck_info["dados"].get(key)
                table_row[f"deck_{deck_idx + 1}"] = val
                values.append(val)
            
            # Verificar se há mudanças
            changed = len(set(v for v in values if v is not None)) > 1
            if changed:
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                if len(numeric_values) > 1:
                    changed = any(abs(float(numeric_values[0]) - float(v)) > 0.01 for v in numeric_values[1:])
            
            table_row["changed"] = changed
            table.append(table_row)
        
        return table
    
    def _format_comparison_internal(
        self,
        result_dec: Dict[str, Any],
        result_jan: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata comparação de dados cadastrais.
        Gera cards comparativos mostrando antes/depois.
        """
        dados_usina_dec = result_dec.get("dados_usina", {})
        dados_usina_jan = result_jan.get("dados_usina", {})
        
        # Se não há dados_usina, pode ser que a tool retornou erro ou não encontrou
        if not dados_usina_dec and not dados_usina_jan:
            return {
                "comparison_table": [],
                "chart_data": None,
                "visualization_type": "comparison_cards",
                "cards": []
            }
        
        # Criar card comparativo
        codigo_dec = dados_usina_dec.get("codigo_usina") or dados_usina_dec.get("codigo")
        codigo_jan = dados_usina_jan.get("codigo_usina") or dados_usina_jan.get("codigo")
        
        # Se códigos diferentes, pode ser usinas diferentes (raro, mas possível)
        if codigo_dec != codigo_jan and codigo_dec and codigo_jan:
            # Usinas diferentes - criar cards separados
            cards = [
                {
                    "usina": dados_usina_dec.get("nome_usina") or f"Usina {codigo_dec}",
                    "codigo": codigo_dec,
                    "deck": "Dezembro",
                    "dados": dados_usina_dec,
                    "changed": False
                },
                {
                    "usina": dados_usina_jan.get("nome_usina") or f"Usina {codigo_jan}",
                    "codigo": codigo_jan,
                    "deck": "Janeiro",
                    "dados": dados_usina_jan,
                    "changed": False
                }
            ]
        else:
            # Mesma usina - comparar campos
            codigo = codigo_dec or codigo_jan
            nome = dados_usina_dec.get("nome_usina") or dados_usina_jan.get("nome_usina") or f"Usina {codigo}"
            
            # Identificar campos que mudaram
            campos_alterados = self._identify_changed_fields(dados_usina_dec, dados_usina_jan)
            
            card = {
                "usina": nome,
                "codigo": codigo,
                "deck_1": dados_usina_dec,
                "deck_2": dados_usina_jan,
                "campos_alterados": campos_alterados,
                "has_changes": len(campos_alterados) > 0
            }
            cards = [card]
        
        # Também criar tabela comparativa com campos principais
        comparison_table = self._build_comparison_table(dados_usina_dec, dados_usina_jan)
        
        return {
            "comparison_table": comparison_table,
            "chart_data": None,
            "visualization_type": "comparison_cards",
            "cards": cards
        }
    
    def _identify_changed_fields(
        self,
        dados_dec: Dict[str, Any],
        dados_jan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identifica campos que mudaram entre os dois decks."""
        campos_alterados = []
        
        all_keys = set(dados_dec.keys()) | set(dados_jan.keys())
        
        for key in all_keys:
            val_dec = dados_dec.get(key)
            val_jan = dados_jan.get(key)
            
            # Comparar valores
            if val_dec != val_jan:
                # Normalizar para comparação (tratar floats)
                if isinstance(val_dec, (int, float)) and isinstance(val_jan, (int, float)):
                    if abs(float(val_dec) - float(val_jan)) > 0.01:
                        campos_alterados.append({
                            "campo": key,
                            "deck_1_value": val_dec,
                            "deck_2_value": val_jan
                        })
                elif val_dec != val_jan:
                    campos_alterados.append({
                        "campo": key,
                        "deck_1_value": val_dec,
                        "deck_2_value": val_jan
                    })
        
        return campos_alterados
    
    def _build_comparison_table(
        self,
        dados_dec: Dict[str, Any],
        dados_jan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Constrói tabela comparativa com campos principais."""
        table = []
        
        # Campos principais para comparar (prioritários)
        campos_principais = [
            "codigo_usina", "codigo", "nome_usina", "nome",
            "potencia", "potencia_instalada", "potencia_efetiva",
            "volume_maximo", "volume_util", "volume_minimo",
            "vazao_maxima", "vazao_minima",
            "fator_capacidade", "fcmax",
            "indisponibilidade", "teif", "ip"
        ]
        
        all_keys = set(dados_dec.keys()) | set(dados_jan.keys())
        
        # Priorizar campos principais
        keys_to_compare = list(set(campos_principais) & all_keys)
        keys_to_compare.extend([k for k in all_keys if k not in campos_principais])
        
        for key in keys_to_compare[:30]:  # Limitar a 30 campos
            val_dec = dados_dec.get(key)
            val_jan = dados_jan.get(key)
            
            if val_dec is not None or val_jan is not None:
                changed = val_dec != val_jan
                
                # Para valores numéricos, considerar mudança se diferença > 0.01
                if isinstance(val_dec, (int, float)) and isinstance(val_jan, (int, float)):
                    changed = abs(float(val_dec) - float(val_jan)) > 0.01
                
                table.append({
                    "campo": key,
                    "deck_1_value": val_dec,
                    "deck_2_value": val_jan,
                    "changed": changed
                })
        
        return table


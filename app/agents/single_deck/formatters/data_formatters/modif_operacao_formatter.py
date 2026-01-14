"""
Formatter para ModifOperacaoTool no single deck.
Replica a formatação do LLM mas pré-configurada para ser mais rápida.
"""
from typing import Dict, Any, List
from app.agents.single_deck.formatters.base import SingleDeckFormatter
from app.agents.single_deck.formatters.text_formatters.simple import format_modif_operacao_simple


class ModifOperacaoSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para ModifOperacaoTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar ModifOperacaoTool."""
        return tool_name == "ModifOperacaoTool" and "dados_por_tipo" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade média."""
        return 75
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de ModifOperacaoTool."""
        dados_por_tipo = tool_result.get("dados_por_tipo", {})
        filtros = tool_result.get("filtros")
        stats_geral = tool_result.get("stats_geral")
        
        if not dados_por_tipo:
            return {
                "final_response": "## ✅ Dados de Operação Hídrica do MODIF.DAT\n\nNenhum dado encontrado.",
                "visualization_data": {
                    "table": [],
                    "tables_by_tipo": {},
                    "visualization_type": "modif_operacao",
                    "tool_name": "ModifOperacaoTool"
                }
            }
        
        # Criar tabelas separadas por tipo de modificação
        tables_by_tipo: Dict[str, List[Dict[str, Any]]] = {}
        
        for tipo, dados in dados_por_tipo.items():
            # Processar e limpar dados para cada tipo
            table_data = []
            for record in dados:
                # Criar registro limpo com campos relevantes
                registro_limpo = {}
                for key, value in record.items():
                    if value is not None:
                        # Formatar datas
                        if key == 'data_inicio' and isinstance(value, str) and 'T' in value:
                            registro_limpo[key] = value.split('T')[0]
                        else:
                            registro_limpo[key] = value
                table_data.append(registro_limpo)
            
            tables_by_tipo[tipo] = table_data
        
        # Criar tabela única para compatibilidade (primeira tipo ou todas se apenas uma)
        table_data = []
        if len(tables_by_tipo) == 1:
            # Se apenas um tipo, usar tabela única
            table_data = list(tables_by_tipo.values())[0]
        else:
            # Se múltiplos tipos, concatenar todas (frontend vai separar)
            for tipo, registros in sorted(tables_by_tipo.items()):
                table_data.extend(registros)
        
        # Criar título descritivo
        titulo = "Dados de Operação Hídrica do MODIF.DAT"
        final_response = format_modif_operacao_simple(
            tables_by_tipo, 
            filtros, 
            stats_geral,
            titulo
        )
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "tables_by_tipo": tables_by_tipo,
                "filtros": filtros,
                "stats_geral": stats_geral,
                "visualization_type": "modif_operacao",
                "tool_name": "ModifOperacaoTool"
            }
        }

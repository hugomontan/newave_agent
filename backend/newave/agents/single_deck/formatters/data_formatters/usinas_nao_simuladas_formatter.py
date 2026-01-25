"""
Formatter para UsinasNaoSimuladasTool no single deck.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.single_deck.formatters.text_formatters.simple import format_usinas_nao_simuladas_simple


class UsinasNaoSimuladasSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para UsinasNaoSimuladasTool."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar UsinasNaoSimuladasTool."""
        return tool_name == "UsinasNaoSimuladasTool" and "dados" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade média."""
        return 75
    
    def _format_date_to_mm_yyyy(self, data_val: Any, ano: Optional[int] = None, mes: Optional[int] = None) -> Optional[str]:
        """Formata data para MM-YYYY."""
        # Prioridade: usar ano e mes se disponíveis
        if ano is not None and mes is not None:
            try:
                return f"{mes:02d}-{ano}"
            except (ValueError, TypeError):
                pass
        
        # Tentar extrair de data_val
        if data_val:
            if isinstance(data_val, str):
                # Formato ISO: "2025-01-01T00:00:00" ou "2025-01-01"
                if "T" in data_val:
                    data_val = data_val.split("T")[0]
                if len(data_val) >= 7 and "-" in data_val:
                    parts = data_val.split("-")
                    if len(parts) >= 2:
                        try:
                            ano_str = parts[0]
                            mes_str = parts[1]
                            return f"{int(mes_str):02d}-{ano_str}"
                        except (ValueError, IndexError):
                            pass
            elif hasattr(data_val, 'year') and hasattr(data_val, 'month'):
                try:
                    return f"{data_val.month:02d}-{data_val.year}"
                except (AttributeError, ValueError):
                    pass
        
        return None
    
    def _sanitize_value(self, valor: Any) -> Optional[float]:
        """Sanitiza valor numérico."""
        if valor is None:
            return None
        if valor == "-" or valor == "":
            return None
        try:
            float_val = float(valor)
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _parse_date_for_sorting(self, data_str: Optional[str]) -> tuple:
        """
        Extrai (ano, mes) de uma string MM-YYYY para ordenação cronológica.
        Retorna (9999, 99) se não conseguir parsear (vai para o final).
        """
        if not data_str or "-" not in data_str:
            return (9999, 99)  # Colocar no final se inválido
        
        try:
            parts = data_str.split("-")
            if len(parts) == 2:
                mes = int(parts[0])
                ano = int(parts[1])
                return (ano, mes)  # Ordenar primeiro por ano, depois por mês
        except (ValueError, IndexError):
            pass
        
        return (9999, 99)  # Fallback: colocar no final
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """Formata resposta de UsinasNaoSimuladasTool."""
        dados = tool_result.get("dados", [])
        
        if not dados:
            return {
                "final_response": "## Usinas Não Simuladas\n\nNenhum dado encontrado.",
                "visualization_data": {
                    "table": [],
                    "visualization_type": "usinas_nao_simuladas",
                    "tool_name": "UsinasNaoSimuladasTool"
                }
            }
        
        # Agrupar dados por fonte
        dados_por_fonte: Dict[str, List[Dict[str, Any]]] = {}
        
        for record in dados:
            fonte = record.get("fonte")
            if not fonte:
                continue
            
            # Formatar data para MM-YYYY
            data_formatada = self._format_date_to_mm_yyyy(
                record.get("data"),
                record.get("ano"),
                record.get("mes")
            )
            
            # Sanitizar valor
            valor = self._sanitize_value(record.get("valor"))
            
            # Criar registro simplificado com apenas: data, fonte, valor
            registro_simplificado = {
                "data": data_formatada,
                "fonte": fonte,
                "valor": valor
            }
            
            if fonte not in dados_por_fonte:
                dados_por_fonte[fonte] = []
            
            dados_por_fonte[fonte].append(registro_simplificado)
        
        # Ordenar registros por data dentro de cada fonte (cronologicamente: ano primeiro, depois mês)
        for fonte in dados_por_fonte:
            dados_por_fonte[fonte].sort(key=lambda x: self._parse_date_for_sorting(x.get("data")))
        
        # Criar tabelas separadas por fonte
        tables_by_fonte: Dict[str, List[Dict[str, Any]]] = {}
        for fonte, registros in dados_por_fonte.items():
            tables_by_fonte[fonte] = registros
        
        # Criar tabela única para compatibilidade (primeira fonte ou todas se apenas uma)
        table_data = []
        if len(tables_by_fonte) == 1:
            # Se apenas uma fonte, usar tabela única
            table_data = list(tables_by_fonte.values())[0]
        else:
            # Se múltiplas fontes, concatenar todas (frontend vai separar)
            for fonte, registros in sorted(tables_by_fonte.items()):
                table_data.extend(registros)
        
        # Extrair informações para criar título descritivo
        fontes_info = sorted(list(tables_by_fonte.keys()))
        
        # Verificar se há filtro de submercado aplicado
        nome_submercado = None
        filtros = tool_result.get("filtros_aplicados")
        if filtros and isinstance(filtros, dict) and "submercado" in filtros:
            submercado_info = filtros["submercado"]
            if isinstance(submercado_info, dict):
                nome_submercado = submercado_info.get("nome")
        
        # Se não encontrou nos filtros, verificar se todos os dados são do mesmo submercado
        if not nome_submercado and dados:
            submercados_unicos = set()
            for record in dados:
                submercado_info = record.get("submercado")
                if submercado_info and isinstance(submercado_info, dict):
                    nome = submercado_info.get("nome")
                    if nome:
                        submercados_unicos.add(nome)
            
            # Se há apenas um submercado único, usar no título
            if len(submercados_unicos) == 1:
                nome_submercado = list(submercados_unicos)[0]
        
        # Criar título descritivo
        titulo_parts = ["Usinas Não Simuladas"]
        if nome_submercado:
            titulo_parts.append(f" - {nome_submercado}")
        if fontes_info:
            titulo_parts.append(f" - {', '.join(fontes_info)}")
        
        titulo = "".join(titulo_parts)
        final_response = format_usinas_nao_simuladas_simple(table_data, titulo)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "tables_by_fonte": tables_by_fonte,
                "visualization_type": "usinas_nao_simuladas",
                "tool_name": "UsinasNaoSimuladasTool"
            }
        }

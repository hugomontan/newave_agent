"""
Formatter para RestricaoEletricaTool no single deck.
Sem uso de LLM - formatação direta dos dados.
"""
import math
from typing import Dict, Any, List, Optional
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.single_deck.formatters.text_formatters.simple import format_restricao_eletrica_simple
from backend.newave.config import safe_print


class RestricaoEletricaSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para RestricaoEletricaTool - sem LLM."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar RestricaoEletricaTool."""
        return tool_name == "RestricaoEletricaTool" and "dados" in result_structure
    
    def get_priority(self) -> int:
        """Prioridade alta."""
        return 85
    
    def format_response(
        self,
        tool_result: Dict[str, Any],
        tool_name: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Formata resposta de RestricaoEletricaTool.
        Agrupa por nome da restrição e patamar.
        Mostra apenas limites superiores (não inferiores).
        """
        dados = tool_result.get("dados", [])
        
        if not dados:
            return {
                "final_response": format_restricao_eletrica_simple([]),
                "visualization_data": {
                    "table": [],
                    "charts_by_restricao": {},
                    "visualization_type": "restricao_eletrica",
                    "tool_name": "RestricaoEletricaTool"
                }
            }
        
        # Filtrar apenas limites (tipo 'limite')
        limites = [d for d in dados if d.get('tipo') == 'limite']
        
        if not limites:
            return {
                "final_response": format_restricao_eletrica_simple([]),
                "visualization_data": {
                    "table": [],
                    "charts_by_restricao": {},
                    "visualization_type": "restricao_eletrica",
                    "tool_name": "RestricaoEletricaTool"
                }
            }
        
        # Indexar por (nome_restricao, patamar, período)
        indexed = self._index_by_restricao_patamar_periodo(limites)
        safe_print(f"[RESTRICAO ELETRICA FORMATTER] Limites processados: {len(limites)}, Indexados: {len(indexed)} restrições")
        
        # Construir tabela e gráficos
        table_data = []
        charts_by_restricao = {}
        
        for nome_restricao in sorted(indexed.keys()):
            patamares_data = indexed[nome_restricao]
            
            for patamar_num in sorted(patamares_data.keys()):
                periodos_data = patamares_data[patamar_num]
                
                # Obter nome do patamar
                nome_patamar = periodos_data.get('nome_patamar', f'Patamar {patamar_num}')
                
                # Processar períodos
                for periodo_key in sorted(periodos_data.get('periodos', {}).keys()):
                    record = periodos_data['periodos'][periodo_key]
                    
                    lim_sup = record.get('lim_sup')
                    if lim_sup is None:
                        continue
                    
                    # Formatar período
                    periodo_formatted = self._format_period_label(record.get('per_ini'), record.get('per_fin'))
                    
                    table_data.append({
                        "restricao": nome_restricao or f"Restrição {record.get('cod_rest', 'N/A')}",
                        "patamar": nome_patamar,
                        "patamar_num": patamar_num,
                        "periodo": periodo_formatted,
                        "limite_superior": self._safe_round(lim_sup),
                        "cod_rest": record.get('cod_rest')
                    })
                
                # Preparar dados do gráfico para este patamar
                if nome_restricao not in charts_by_restricao:
                    charts_by_restricao[nome_restricao] = {
                        "restricao": nome_restricao,
                        "patamares": {}
                    }
                
                # Dados do gráfico para este patamar
                periodo_labels = []
                limite_values = []
                
                for periodo_key in sorted(periodos_data.get('periodos', {}).keys()):
                    record = periodos_data['periodos'][periodo_key]
                    lim_sup = record.get('lim_sup')
                    if lim_sup is not None:
                        periodo_labels.append(self._format_period_label(record.get('per_ini'), record.get('per_fin')))
                        limite_values.append(self._safe_round(lim_sup))
                
                if periodo_labels:
                    charts_by_restricao[nome_restricao]["patamares"][nome_patamar] = {
                        "labels": periodo_labels,
                        "data": limite_values,
                        "patamar_num": patamar_num
                    }
        
        # Criar chart_data estruturado
        chart_data = {}
        for nome_restricao, restricao_data in charts_by_restricao.items():
            datasets = []
            patamares_ordenados = sorted(
                restricao_data["patamares"].items(),
                key=lambda x: x[1]["patamar_num"]
            )
            
            for nome_patamar, patamar_data in patamares_ordenados:
                datasets.append({
                    "label": nome_patamar,
                    "data": patamar_data["data"]
                })
            
            if datasets:
                chart_data[nome_restricao] = {
                    "labels": restricao_data["patamares"][patamares_ordenados[0][0]]["labels"],
                    "datasets": datasets
                }
        
        final_response = format_restricao_eletrica_simple(table_data, query)
        
        safe_print(f"[RESTRICAO ELETRICA FORMATTER] Tabela: {len(table_data)} registros, Gráficos: {len(chart_data)} restrições")
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "charts_by_restricao": chart_data,
                "visualization_type": "restricao_eletrica",
                "chart_config": {
                    "type": "line",
                    "title": "Limites Superiores por Restrição e Patamar",
                    "x_axis": "Período",
                    "y_axis": "Limite Superior (MW)"
                },
                "tool_name": "RestricaoEletricaTool"
            }
        }
    
    def _index_by_restricao_patamar_periodo(self, limites: List[Dict]) -> Dict[str, Dict[int, Dict]]:
        """
        Indexa limites por (nome_restricao, patamar, período).
        Retorna: {nome_restricao: {patamar: {periodos: {periodo_key: record}}}}
        """
        indexed = {}
        
        for record in limites:
            nome_restricao = record.get('nome_restricao')
            if not nome_restricao:
                nome_restricao = f"Restrição {record.get('cod_rest', 'N/A')}"
            
            patamar = record.get('patamar')
            if patamar is None:
                continue
            
            # Criar chave de período
            per_ini = record.get('per_ini')
            per_fin = record.get('per_fin')
            periodo_key = f"{per_ini}_{per_fin}"
            
            if nome_restricao not in indexed:
                indexed[nome_restricao] = {}
            
            if patamar not in indexed[nome_restricao]:
                indexed[nome_restricao][patamar] = {
                    'nome_patamar': record.get('nome_patamar', f'Patamar {patamar}'),
                    'periodos': {}
                }
            
            indexed[nome_restricao][patamar]['periodos'][periodo_key] = record
        
        return indexed
    
    def _format_period_label(self, per_ini: Optional[str], per_fin: Optional[str]) -> str:
        """Formata período para label legível."""
        if per_ini and per_fin:
            if per_ini == per_fin:
                return per_ini.replace('/', '-')  # "2025/12" -> "2025-12"
            return f"{per_ini.replace('/', '-')} a {per_fin.replace('/', '-')}"
        elif per_ini:
            return per_ini.replace('/', '-')
        elif per_fin:
            return per_fin.replace('/', '-')
        return "N/A"
    
    def _safe_round(self, value) -> Optional[float]:
        """Arredonda valor com tratamento de NaN/None."""
        if value is None:
            return None
        try:
            rounded = round(float(value), 2)
            if math.isnan(rounded) or math.isinf(rounded):
                return None
            if rounded == int(rounded):
                return int(rounded)
            return rounded
        except (ValueError, TypeError):
            return None

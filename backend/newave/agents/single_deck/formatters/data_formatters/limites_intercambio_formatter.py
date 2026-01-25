"""
Formatter para LimitesIntercambioTool no single deck.
Espelhado do multi-deck, mas adaptado para um único deck.
"""
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from backend.newave.agents.single_deck.formatters.base import SingleDeckFormatter
from backend.newave.agents.shared.formatting.data_processors.limites_intercambio_processor import LimitesIntercambioDataProcessor
from backend.newave.agents.single_deck.formatters.text_formatters.simple import format_limites_intercambio_simple
from backend.newave.config import safe_print


class LimitesIntercambioSingleDeckFormatter(SingleDeckFormatter):
    """Formatter específico para LimitesIntercambioTool - espelhado do multi-deck."""
    
    def can_format(self, tool_name: str, result_structure: Dict[str, Any]) -> bool:
        """Verifica se pode formatar LimitesIntercambioTool."""
        return tool_name == "LimitesIntercambioTool" and (
            "data" in result_structure or "stats_por_par" in result_structure
        )
    
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
        Formata resposta de LimitesIntercambioTool.
        Espelhado do multi-deck: agrupa por par e sentido, mostra múltiplas tabelas separadas.
        """
        data = tool_result.get("data", [])
        
        if not data:
            return {
                "final_response": format_limites_intercambio_simple([]),
                "visualization_data": {
                    "table": [],
                    "charts_by_par": {},
                    "visualization_type": "limites_intercambio",
                    "tool_name": "LimitesIntercambioTool"
                }
            }
        
        # Indexar dados por (par, sentido, período)
        indexed = self._index_by_par_sentido_periodo(data)
        
        # Obter todos os pares únicos
        all_pares = set(indexed.keys())
        
        # Detectar se a query especifica um par específico
        par_filtrado = self._extract_par_from_query(query, tool_result)
        
        # Se um par específico foi detectado, filtrar apenas esse par
        if par_filtrado is not None:
            pares_filtrados = set()
            for par_key in all_pares:
                parts = par_key.split("-")
                if len(parts) >= 2:
                    sub_de_key = parts[0]
                    sub_para_key = parts[1]
                    sentido_key = parts[2] if len(parts) >= 3 else None
                    
                    # Verificar se corresponde ao par filtrado
                    if len(par_filtrado) == 2:
                        # Apenas sub_de e sub_para foram especificados
                        if str(par_filtrado[0]) == sub_de_key and str(par_filtrado[1]) == sub_para_key:
                            pares_filtrados.add(par_key)
                    elif len(par_filtrado) == 3:
                        # sub_de, sub_para e sentido foram especificados
                        if (str(par_filtrado[0]) == sub_de_key and 
                            str(par_filtrado[1]) == sub_para_key and
                            sentido_key is not None and str(par_filtrado[2]) == sentido_key):
                            pares_filtrados.add(par_key)
            
            if pares_filtrados:
                all_pares = pares_filtrados
        
        # Construir tabela e charts_by_par
        table_data = []
        charts_by_par = {}
        
        for par_key in sorted(all_pares):
            records = indexed.get(par_key, {})
            
            # Extrair informações do par_key: "sub_de-sub_para-sentido"
            parts = par_key.split("-")
            if len(parts) >= 3:
                sub_de = parts[0]
                sub_para = parts[1]
                sentido = int(parts[2])
                
                # Obter nomes dos submercados
                nome_de = self._get_submercado_nome(sub_de, tool_result)
                nome_para = self._get_submercado_nome(sub_para, tool_result)
                sentido_label = "Mínimo Obrigatório" if sentido == 1 else "Máximo"
                par_label = f"{nome_de} → {nome_para}"
                
                # Obter todos os períodos únicos para este par
                all_periodos = sorted(records.keys())
                
                # Construir dados do gráfico e tabela para este par
                par_values = []
                par_labels = []
                
                for periodo in all_periodos:
                    record = records.get(periodo, {})
                    valor = self._sanitize_number(record.get("valor"))
                    
                    # Dados para gráfico
                    par_values.append(self._safe_round(valor))
                    
                    # Formatar período como mês-ano (ex: "12/2025") para labels do gráfico
                    periodo_formatted = self._format_period_label(periodo)
                    par_labels.append(periodo_formatted)
                    
                    # Incluir na tabela
                    periodo_formatted_table = self._format_period_label(periodo)
                    
                    table_data.append({
                        "data": periodo_formatted_table,  # Formato mês-ano
                        "par_key": par_key,
                        "par": par_label,
                        "sentido": sentido_label,
                        "limite": self._safe_round(valor),
                    })
                
                # Criar chart_data para este par
                par_chart_data = {
                    "labels": par_labels,  # Usar labels formatados (mês/ano)
                    "datasets": [{
                        "label": "Limite",
                        "data": par_values
                    }]
                } if all_periodos else None
                
                charts_by_par[par_key] = {
                    "par": par_label,
                    "sentido": sentido_label,
                    "chart_data": par_chart_data,
                    "chart_config": {
                        "type": "line",
                        "title": f"{par_label} - {sentido_label}",
                        "x_axis": "Período",
                        "y_axis": "Limite (MW)"
                    }
                }
        
        final_response = format_limites_intercambio_simple(table_data)
        
        return {
            "final_response": final_response,
            "visualization_data": {
                "table": table_data,
                "charts_by_par": charts_by_par,
                "visualization_type": "limites_intercambio",
                "chart_config": {
                    "type": "line",
                    "title": "Limites de Intercâmbio",
                    "x_axis": "Período",
                    "y_axis": "Limite (MW)"
                },
                "tool_name": "LimitesIntercambioTool"
            }
        }
    
    def _index_by_par_sentido_periodo(self, data: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """
        Indexa dados por (submercado_de, submercado_para, sentido) e depois por período.
        Retorna: {par_key: {periodo: record}}
        """
        indexed = {}
        
        for record in data:
            sub_de = record.get("submercado_de")
            sub_para = record.get("submercado_para")
            sentido = record.get("sentido")
            
            if sub_de is not None and sub_para is not None and sentido is not None:
                par_key = f"{sub_de}-{sub_para}-{sentido}"
                
                periodo = self._get_period_key(record)
                if periodo:
                    if par_key not in indexed:
                        indexed[par_key] = {}
                    indexed[par_key][periodo] = record
        
        return indexed
    
    def _get_period_key(self, record: Dict) -> Optional[str]:
        """Obtém chave de período no formato YYYY-MM."""
        # Tentar ano e mes primeiro
        ano = record.get("ano")
        mes = record.get("mes")
        
        if ano is not None and mes is not None:
            try:
                ano_int = int(float(ano)) if isinstance(ano, (int, float, str)) else None
                mes_int = int(float(mes)) if isinstance(mes, (int, float, str)) else None
                if ano_int is not None and mes_int is not None:
                    return f"{ano_int:04d}-{mes_int:02d}"
            except (ValueError, TypeError):
                pass
        
        # Tentar campo data
        data = record.get("data")
        if data:
            if isinstance(data, str):
                # Formato ISO: "2025-01-01T00:00:00" ou "2025-01-01"
                if len(data) >= 7 and "-" in data:
                    return data[:7]  # YYYY-MM
            elif hasattr(data, 'year') and hasattr(data, 'month'):
                try:
                    return f"{data.year:04d}-{data.month:02d}"
                except (AttributeError, ValueError):
                    pass
        
        # Tentar ano_mes se existir
        ano_mes = record.get("ano_mes")
        if ano_mes:
            if isinstance(ano_mes, str) and len(ano_mes) >= 7:
                return ano_mes[:7]  # YYYY-MM
        
        return None
    
    def _get_submercado_nome(self, codigo: str, tool_result: Dict) -> str:
        """Obtém nome do submercado a partir do código."""
        data = tool_result.get("data", [])
        for record in data:
            if str(record.get("submercado_de")) == str(codigo):
                nome = record.get("nome_submercado_de")
                if nome:
                    return nome
            if str(record.get("submercado_para")) == str(codigo):
                nome = record.get("nome_submercado_para")
                if nome:
                    return nome
        
        # Fallback: usar código
        return f"Subsistema {codigo}"
    
    def _format_period_label(self, periodo_key: str) -> str:
        """
        Formata chave de período (ex: "2025-12") para label legível (ex: "12-2025").
        Retorna formato MM-YYYY.
        """
        try:
            if "-" in periodo_key:
                parts = periodo_key.split("-")
                if len(parts) == 2:
                    # Verificar se está em formato YYYY-MM (ano tem 4 dígitos)
                    if len(parts[0]) == 4:
                        ano = parts[0]
                        mes = int(parts[1])
                        return f"{mes:02d}-{ano}"  # MM-YYYY
                    else:
                        # Já está em formato MM-YYYY
                        return periodo_key
            return periodo_key
        except (ValueError, IndexError):
            return periodo_key
    
    def _safe_round(self, value) -> Optional[float]:
        """Arredonda valor com tratamento de NaN/None, sem decimais quando inteiro."""
        if value is None:
            return None
        try:
            rounded = round(value, 2)
            # Verificar se o resultado é NaN ou Inf
            if math.isnan(rounded) or math.isinf(rounded):
                return None
            # Se for número inteiro, retornar sem decimais
            if rounded == int(rounded):
                return int(rounded)
            return rounded
        except (ValueError, TypeError):
            return None
    
    def _sanitize_number(self, value) -> Optional[float]:
        """Sanitiza valor numérico."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    def _extract_par_from_query(self, query: str, tool_result: Dict[str, Any]) -> Optional[Tuple]:
        """
        Extrai par de submercados (sub_de, sub_para) ou (sub_de, sub_para, sentido) da query.
        Retorna None se nenhum par específico for detectado.
        Espelhado do multi-deck.
        """
        query_lower = query.lower()
        safe_print(f"[FORMATTER] [SINGLE DECK] _extract_par_from_query - Query: '{query}'")
        
        # Obter lista de submercados disponíveis dos resultados
        subsistemas_disponiveis = []
        data = tool_result.get("data", [])
        
        for record in data:
            sub_de = record.get("submercado_de")
            nome_de = record.get("nome_submercado_de")
            if sub_de is not None and nome_de:
                subsistemas_disponiveis.append({
                    'codigo': int(sub_de) if isinstance(sub_de, (int, float, str)) else None,
                    'nome': str(nome_de).strip()
                })
            sub_para = record.get("submercado_para")
            nome_para = record.get("nome_submercado_para")
            if sub_para is not None and nome_para:
                subsistemas_disponiveis.append({
                    'codigo': int(sub_para) if isinstance(sub_para, (int, float, str)) else None,
                    'nome': str(nome_para).strip()
                })
        
        # Remover duplicatas
        seen = set()
        subsistemas_unicos = []
        for s in subsistemas_disponiveis:
            if s['codigo'] is not None:
                key = (s['codigo'], s['nome'])
                if key not in seen:
                    seen.add(key)
                    subsistemas_unicos.append(s)
        
        if not subsistemas_unicos:
            safe_print(f"[FORMATTER] [SINGLE DECK] Nenhum subsistema encontrado")
            return None
        
        # ETAPA 1: Tentar extrair números explícitos
        patterns = [
            r'subsistema\s*(\d+)\s*(?:para|->|→)\s*subsistema\s*(\d+)',
            r'submercado\s*(\d+)\s*(?:para|->|→)\s*submercado\s*(\d+)',
            r'(\d+)\s*(?:para|->|→)\s*(\d+)',
            r'entre\s*subsistema\s*(\d+)\s*e\s*subsistema\s*(\d+)',
            r'entre\s*submercado\s*(\d+)\s*e\s*submercado\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    sub_de = int(match.group(1))
                    sub_para = int(match.group(2))
                    codigos_validos = [s['codigo'] for s in subsistemas_unicos if s['codigo'] is not None]
                    if sub_de in codigos_validos and sub_para in codigos_validos:
                        # Verificar se há filtro de sentido
                        sentido = None
                        if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                            sentido = 1
                        elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                            sentido = 0
                        
                        if sentido is not None:
                            safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par com sentido: ({sub_de}, {sub_para}, {sentido})")
                            return (sub_de, sub_para, sentido)
                        safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par sem sentido: ({sub_de}, {sub_para})")
                        return (sub_de, sub_para)
                except (ValueError, IndexError):
                    continue
        
        # ETAPA 2: Buscar por nomes de submercados
        subsistemas_ordenados = sorted(subsistemas_unicos, key=lambda x: len(x['nome']), reverse=True)
        
        sub_de = None
        sub_para = None
        
        # Padrão especial: "entre X e Y"
        pattern_entre = re.search(r'entre\s+([^e]+?)\s+e\s+([^e]+?)(?:\s|$|,|\.)', query_lower)
        if pattern_entre:
            nome_1 = pattern_entre.group(1).strip()
            nome_2 = pattern_entre.group(2).strip()
            
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_1:
                    sub_de = subsistema['codigo']
                    break
            
            for subsistema in subsistemas_ordenados:
                nome_sub_lower = subsistema['nome'].lower().strip()
                if nome_sub_lower and nome_sub_lower in nome_2:
                    if subsistema['codigo'] != sub_de:
                        sub_para = subsistema['codigo']
                        break
            
            if sub_de is not None and sub_para is not None:
                sentido = None
                if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                    sentido = 1
                elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                    sentido = 0
                
                if sentido is not None:
                    safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par 'entre X e Y' com sentido: ({sub_de}, {sub_para}, {sentido})")
                    return (sub_de, sub_para, sentido)
                safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par 'entre X e Y' sem sentido: ({sub_de}, {sub_para})")
                return (sub_de, sub_para)
        
        # Padrão: "X para Y" ou "X → Y"
        submercados_encontrados = []
        for subsistema in subsistemas_ordenados:
            codigo_sub = subsistema['codigo']
            nome_sub = subsistema['nome']
            nome_sub_lower = nome_sub.lower().strip()
            
            if nome_sub_lower and nome_sub_lower in query_lower:
                pos = 0
                while True:
                    pos = query_lower.find(nome_sub_lower, pos)
                    if pos == -1:
                        break
                    submercados_encontrados.append({
                        'codigo': codigo_sub,
                        'nome': nome_sub,
                        'posicao': pos
                    })
                    pos += 1
        
        # Ordenar por posição na query (ordem cronológica)
        submercados_encontrados.sort(key=lambda x: x['posicao'])
        
        # Se encontrou pelo menos 2 submercados diferentes, usar os 2 primeiros
        if len(submercados_encontrados) >= 2:
            # Remover duplicatas mantendo a ordem
            submercados_unicos = []
            codigos_vistos = set()
            for sub in submercados_encontrados:
                if sub['codigo'] not in codigos_vistos:
                    codigos_vistos.add(sub['codigo'])
                    submercados_unicos.append(sub)
            
            if len(submercados_unicos) >= 2:
                sub_de = submercados_unicos[0]['codigo']
                sub_para = submercados_unicos[1]['codigo']
                
                sentido = None
                if any(kw in query_lower for kw in ["minimo", "mínimo", "obrigatorio", "obrigatório"]):
                    sentido = 1
                elif any(kw in query_lower for kw in ["maximo", "máximo"]):
                    sentido = 0
                
                if sentido is not None:
                    safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par 'X para Y' com sentido: ({sub_de}, {sub_para}, {sentido})")
                    return (sub_de, sub_para, sentido)
                safe_print(f"[FORMATTER] [SINGLE DECK] ✅ Par 'X para Y' sem sentido: ({sub_de}, {sub_para})")
                return (sub_de, sub_para)
        
        safe_print(f"[FORMATTER] [SINGLE DECK] ❌ Nenhum par detectado")
        return None

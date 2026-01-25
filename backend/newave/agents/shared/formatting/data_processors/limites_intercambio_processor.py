"""
Processador de dados para LimitesIntercambioTool.
Extrai dados puros sem formatação.
"""
import math
from typing import Dict, Any, List, Optional


class LimitesIntercambioDataProcessor:
    """Processador puro de dados para LimitesIntercambioTool."""
    
    @staticmethod
    def _sanitize_number(value: Any) -> Optional[float]:
        """Sanitiza número, retornando None se inválido."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return float_val
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _group_by_par_sentido(data: List[Dict]) -> Dict[str, Dict]:
        """Agrupa dados por par (sub_de-sub_para) e sentido."""
        grouped = {}
        for record in data:
            sub_de = record.get("submercado_de") or record.get("sub_de")
            sub_para = record.get("submercado_para") or record.get("sub_para")
            sentido = record.get("sentido")
            periodo = record.get("periodo") or record.get("ano_mes") or record.get("data")
            
            if sub_de is not None and sub_para is not None and sentido is not None and periodo:
                par_key = f"{sub_de}-{sub_para}-{sentido}"
                if par_key not in grouped:
                    grouped[par_key] = {}
                grouped[par_key][periodo] = record
        return grouped
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados tabulares de LimitesIntercambioTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Lista de dicionários com dados tabulares
        """
        data = tool_result.get("data", [])
        
        table_data = []
        for record in data:
            # A tool retorna: submercado_de, submercado_para, valor, data, sentido
            sub_de = record.get("submercado_de") or record.get("sub_de")
            sub_para = record.get("submercado_para") or record.get("sub_para")
            sentido = record.get("sentido")
            
            # Obter período: pode ser data (datetime ou string), periodo, ou ano_mes
            periodo = None
            if "periodo" in record and record.get("periodo"):
                periodo = str(record.get("periodo"))
            elif "ano_mes" in record and record.get("ano_mes"):
                periodo = str(record.get("ano_mes"))
            elif "data" in record and record.get("data"):
                data_val = record.get("data")
                if isinstance(data_val, str):
                    # Tentar extrair ano-mês de string ISO ou similar
                    # Formato ISO: "2026-01-01T00:00:00" ou "2026-01-01"
                    if len(data_val) >= 7 and data_val[4] == '-':
                        periodo = data_val[:7]  # YYYY-MM
                    elif 'T' in data_val:
                        # Formato ISO com timestamp
                        periodo = data_val.split('T')[0][:7]  # YYYY-MM
                    else:
                        periodo = data_val
                else:
                    periodo = str(data_val)
            
            # Se ainda não tem período, tentar construir a partir de ano e mês
            periodo_key_ordenacao = None  # Para ordenação (YYYY-MM)
            periodo_display = None  # Para exibição (MM-YYYY)
            
            if not periodo:
                ano = record.get("ano")
                mes = record.get("mes")
                if ano is not None and mes is not None:
                    ano_int = int(ano) if isinstance(ano, (int, float)) else ano
                    mes_int = int(mes) if isinstance(mes, (int, float)) else mes
                    periodo_key_ordenacao = f"{ano_int}-{mes_int:02d}"  # YYYY-MM para ordenação
                    periodo_display = f"{mes_int:02d}-{ano_int}"  # MM-YYYY para exibição
            else:
                # Converter período existente para MM-YYYY se estiver em YYYY-MM
                periodo_key_ordenacao = periodo
                if isinstance(periodo, str) and "-" in periodo:
                    parts = periodo.split("-")
                    if len(parts) == 2:
                        # Verificar se está em formato YYYY-MM (ano tem 4 dígitos)
                        if len(parts[0]) == 4:
                            periodo_display = f"{parts[1]}-{parts[0]}"  # MM-YYYY
                        else:
                            periodo_display = periodo
                    else:
                        periodo_display = periodo
                else:
                    periodo_display = periodo
            
            # Obter nomes dos submercados se disponíveis
            nome_de = record.get("nome_submercado_de") or record.get("nome_de")
            nome_para = record.get("nome_submercado_para") or record.get("nome_para")
            
            # Obter valor do limite
            limite = LimitesIntercambioDataProcessor._sanitize_number(record.get("valor") or record.get("limite"))
            
            if limite is not None and sub_de is not None and sub_para is not None and periodo_display:
                sentido_label = "Mínimo Obrigatório" if sentido == 1 else "Máximo"
                
                # Usar nomes se disponíveis, senão usar códigos
                sub_de_label = nome_de if nome_de else f"Subsistema {sub_de}"
                sub_para_label = nome_para if nome_para else f"Subsistema {sub_para}"
                
                # Criar par_key no formato "sub_de-sub_para-sentido" (igual ao multi-deck)
                par_key = f"{sub_de}-{sub_para}-{sentido}"
                
                table_data.append({
                    "sub_de": sub_de,
                    "sub_para": sub_para,
                    "nome_de": sub_de_label,
                    "nome_para": sub_para_label,
                    "par": f"{sub_de_label} → {sub_para_label}",
                    "par_key": par_key,  # Chave para agrupamento (igual ao multi-deck)
                    "sentido": sentido_label,
                    "codigo_sentido": sentido,
                    "periodo": periodo_key_ordenacao or periodo_display,  # YYYY-MM para ordenação
                    "data": periodo_display,  # MM-YYYY para exibição
                    "limite": round(limite, 2)
                })
        
        return sorted(table_data, key=lambda x: (x.get("sub_de", 0), x.get("sub_para", 0), x.get("codigo_sentido", 0), x.get("periodo", "")))
    
    @staticmethod
    def extract_chart_data_by_par(tool_result: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Extrai dados para gráfico agrupados por par.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Dict com chave sendo par_key e valor sendo chart_data
        """
        table_data = LimitesIntercambioDataProcessor.extract_table_data(tool_result)
        
        if not table_data:
            return {}
        
        # Agrupar por par e sentido
        charts_by_par = {}
        
        for record in table_data:
            par_key = f"{record.get('sub_de')}-{record.get('sub_para')}-{record.get('codigo_sentido')}"
            
            if par_key not in charts_by_par:
                charts_by_par[par_key] = {
                    "par": record.get("par"),
                    "sentido": record.get("sentido"),
                    "periodos": [],
                    "valores": []
                }
            
            # Usar campo "data" (MM-YYYY) para exibição, ou "periodo" como fallback
            periodo_display = record.get("data") or record.get("periodo")
            charts_by_par[par_key]["periodos"].append(periodo_display)
            charts_by_par[par_key]["valores"].append(record.get("limite"))
        
        # Converter para formato chart_data
        result = {}
        for par_key, data in charts_by_par.items():
            # Ordenar usando período como chave (pode estar em MM-YYYY ou YYYY-MM)
            # Criar tuplas com período original para ordenação
            periodos_com_ordenacao = []
            for periodo, valor in zip(data["periodos"], data["valores"]):
                # Converter MM-YYYY para YYYY-MM para ordenação se necessário
                if periodo and "-" in periodo:
                    parts = periodo.split("-")
                    if len(parts) == 2 and len(parts[0]) == 2:  # MM-YYYY
                        periodo_ordenacao = f"{parts[1]}-{parts[0]}"  # YYYY-MM
                    else:
                        periodo_ordenacao = periodo
                else:
                    periodo_ordenacao = periodo or ""
                periodos_com_ordenacao.append((periodo_ordenacao, periodo, valor))
            
            sorted_data = sorted(periodos_com_ordenacao, key=lambda x: x[0])
            
            result[par_key] = {
                "par": data["par"],
                "sentido": data["sentido"],
                "chart_data": {
                    "labels": [p for _, p, _ in sorted_data],  # Usar período original (MM-YYYY)
                    "datasets": [{
                        "label": "Limite",
                        "data": [v for _, _, v in sorted_data]
                    }]
                }
            }
        
        return result

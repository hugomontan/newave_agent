"""
Processador de dados para CargaMensalTool e CadicTool.
Extrai dados puros sem formatação.
"""
import math
from typing import Dict, Any, List, Optional

# Mapeamento de códigos de submercado para nomes
SUBMERCADO_NAMES = {
    1: "SUDESTE",
    2: "SUL",
    3: "NORDESTE",
    4: "NORTE"
}


class CargaDataProcessor:
    """Processador puro de dados para CargaMensalTool e CadicTool."""
    
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
    def _get_period_key(record: Dict[str, Any]) -> Optional[str]:
        """Gera chave de período a partir do record."""
        ano = record.get("ano")
        mes = record.get("mes")
        if ano is not None and mes is not None:
            # Converter para int se necessário
            ano_int = int(ano) if isinstance(ano, (int, float)) else ano
            mes_int = int(mes) if isinstance(mes, (int, float)) else mes
            return f"{ano_int}-{mes_int:02d}"
        return None
    
    @staticmethod
    def _group_by_submercado(data: List[Dict]) -> Dict[str, Dict]:
        """Agrupa dados por submercado."""
        grouped = {}
        for record in data:
            codigo_sub = record.get("codigo_submercado")
            if codigo_sub is not None:
                if codigo_sub not in grouped:
                    grouped[codigo_sub] = {
                        "nome": record.get("nome_submercado", f"Subsistema {codigo_sub}"),
                        "codigo": codigo_sub,
                        "dados": []
                    }
                grouped[codigo_sub]["dados"].append(record)
        return grouped
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados tabulares de CargaMensalTool ou CadicTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Lista de dicionários com dados tabulares
        """
        # Verificar se há dados_por_submercado
        dados_por_submercado = tool_result.get("dados_por_submercado", {})
        
        if dados_por_submercado:
            # Extrair de dados_por_submercado
            table_data = []
            for codigo_sub, sub_data in dados_por_submercado.items():
                # Obter nome do submercado: primeiro tenta do sub_data, depois do mapeamento
                nome_sub = sub_data.get("nome", "")
                if not nome_sub or nome_sub.startswith("Subsistema"):
                    # Se não tem nome ou é "Subsistema X", usar mapeamento
                    codigo_int = int(codigo_sub) if isinstance(codigo_sub, (int, float)) else codigo_sub
                    nome_sub = SUBMERCADO_NAMES.get(codigo_int, f"Subsistema {codigo_sub}")
                dados = sub_data.get("dados", [])
                
                for record in dados:
                    ano = record.get("ano")
                    mes = record.get("mes")
                    valor = CargaDataProcessor._sanitize_number(record.get("valor") or record.get("carga"))
                    razao = record.get("razao")  # Campo específico de CadicTool
                    
                    if valor is not None and ano is not None and mes is not None:
                        # Converter ano e mes para int se necessário
                        ano_int = int(ano) if isinstance(ano, (int, float)) else ano
                        mes_int = int(mes) if isinstance(mes, (int, float)) else mes
                        
                        # Formatar data como MM-YYYY
                        data_formatada = f"{mes_int:02d}-{ano_int}"
                        
                        row_data = {
                            "ano": ano_int,
                            "mes": mes_int,
                            "data": data_formatada,  # Formato MM-YYYY
                            "periodo": f"{ano_int}-{mes_int:02d}",  # Mantido para compatibilidade
                            "submercado": nome_sub,  # Nome do submercado
                            "codigo_submercado": codigo_sub,
                            "valor": round(valor, 2)
                        }
                        
                        # Adicionar razao se disponível (CadicTool)
                        if razao is not None:
                            row_data["razao"] = str(razao).strip()
                        
                        table_data.append(row_data)
        else:
            # Extrair de data
            data = tool_result.get("data", [])
            table_data = []
            
            for record in data:
                ano = record.get("ano")
                mes = record.get("mes")
                valor = CargaDataProcessor._sanitize_number(record.get("valor") or record.get("carga"))
                codigo_sub = record.get("codigo_submercado")
                razao = record.get("razao")  # Campo específico de CadicTool
                
                # Obter nome do submercado: primeiro tenta do record, depois do mapeamento, depois fallback
                nome_sub = record.get("nome_submercado")
                if not nome_sub or nome_sub.startswith("Subsistema"):
                    # Se não tem nome ou é "Subsistema X", usar mapeamento
                    if codigo_sub is not None:
                        codigo_int = int(codigo_sub) if isinstance(codigo_sub, (int, float)) else codigo_sub
                        nome_sub = SUBMERCADO_NAMES.get(codigo_int, f"Subsistema {codigo_sub}")
                    else:
                        nome_sub = "N/A"
                
                if valor is not None and ano is not None and mes is not None:
                    # Converter ano e mes para int se necessário
                    ano_int = int(ano) if isinstance(ano, (int, float)) else ano
                    mes_int = int(mes) if isinstance(mes, (int, float)) else mes
                    
                    # Formatar data como MM-YYYY
                    data_formatada = f"{mes_int:02d}-{ano_int}"
                    
                    row_data = {
                        "ano": ano_int,
                        "mes": mes_int,
                        "data": data_formatada,  # Formato MM-YYYY
                        "periodo": f"{ano_int}-{mes_int:02d}",  # Mantido para compatibilidade
                        "submercado": nome_sub,  # Nome do submercado
                        "codigo_submercado": codigo_sub,
                        "valor": round(valor, 2)
                    }
                    
                    # Adicionar razao se disponível (CadicTool)
                    if razao is not None:
                        row_data["razao"] = str(razao).strip()
                    
                    table_data.append(row_data)
        
        return sorted(table_data, key=lambda x: (x.get("ano", 0), x.get("mes", 0), x.get("codigo_submercado", 0)))
    
    @staticmethod
    def extract_chart_data(tool_result: Dict[str, Any]) -> Optional[Dict]:
        """
        Extrai dados para gráfico de CargaMensalTool ou CadicTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Dict com labels e datasets para Chart.js ou None
        """
        table_data = CargaDataProcessor.extract_table_data(tool_result)
        
        if not table_data:
            return None
        
        # Verificar se há campo razao (CadicTool)
        has_razao = any(r.get("razao") for r in table_data)
        
        # Agrupar por submercado (e razao se disponível)
        if has_razao:
            # Agrupar por combinação submercado + razao
            grupos_data = {}
            for record in table_data:
                submercado = record.get("submercado", "")
                razao = record.get("razao", "")
                grupo_key = f"{submercado} → {razao}" if razao else submercado
                if grupo_key not in grupos_data:
                    grupos_data[grupo_key] = []
                grupos_data[grupo_key].append(record)
        else:
            # Agrupar apenas por submercado (CargaMensalTool)
            grupos_data = {}
            for record in table_data:
                submercado = record.get("submercado")
                if submercado not in grupos_data:
                    grupos_data[submercado] = []
                grupos_data[submercado].append(record)
        
        # Obter todos os períodos únicos usando campo "data" (MM-YYYY) para exibição
        # Mas ordenar usando "periodo" (YYYY-MM) para manter ordem cronológica
        all_periods_display = []  # MM-YYYY para labels do gráfico
        all_periods_ordenacao = []  # YYYY-MM para ordenação
        
        periodos_set = set()
        for r in table_data:
            periodo_display = r.get("data") or r.get("periodo")
            periodo_ordenacao = r.get("periodo") or r.get("data")
            if periodo_display:
                # Converter MM-YYYY para YYYY-MM se necessário para ordenação
                if periodo_ordenacao and "-" in periodo_ordenacao:
                    parts = periodo_ordenacao.split("-")
                    if len(parts) == 2 and len(parts[0]) == 2:  # MM-YYYY
                        periodo_ordenacao = f"{parts[1]}-{parts[0]}"  # YYYY-MM
                
                key = (periodo_ordenacao, periodo_display)
                if key not in periodos_set:
                    periodos_set.add(key)
                    all_periods_ordenacao.append(periodo_ordenacao)
                    all_periods_display.append(periodo_display)
        
        # Ordenar por período de ordenação
        sorted_periods = sorted(zip(all_periods_ordenacao, all_periods_display), key=lambda x: x[0])
        all_periods_display_sorted = [p[1] for p in sorted_periods]
        
        # Criar datasets (uma linha por grupo)
        datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff"]
        
        for idx, (grupo_key, records) in enumerate(sorted(grupos_data.items())):
            # Criar mapa periodo_display -> valor (usar campo "data" se disponível)
            period_to_value = {}
            for r in records:
                periodo_display = r.get("data") or r.get("periodo")
                if periodo_display:
                    period_to_value[periodo_display] = r.get("valor")
            
            # Criar array de valores alinhado com all_periods_display_sorted
            values = []
            for periodo_display in all_periods_display_sorted:
                values.append(period_to_value.get(periodo_display))
            
            datasets.append({
                "label": grupo_key,
                "data": values
            })
        
        return {
            "labels": all_periods_display_sorted,  # MM-YYYY
            "datasets": datasets
        } if all_periods_display_sorted else None

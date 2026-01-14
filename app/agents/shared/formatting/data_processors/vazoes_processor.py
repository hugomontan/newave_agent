"""
Processador de dados para VazoesTool e DsvaguaTool.
Extrai dados puros sem formatação.
"""
import math
from typing import Dict, Any, List, Optional


class VazoesDataProcessor:
    """Processador puro de dados para VazoesTool e DsvaguaTool."""
    
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
        # VazoesTool retorna ano_mes no formato "YYYY-MM"
        ano_mes = record.get("ano_mes")
        if ano_mes:
            return str(ano_mes)
        
        # Tentar construir a partir de ano e mes
        ano = record.get("ano")
        mes = record.get("mes")
        if ano is not None and mes is not None:
            try:
                ano_int = int(ano) if isinstance(ano, (int, float)) else ano
                mes_int = int(mes) if isinstance(mes, (int, float)) else mes
                return f"{ano_int:04d}-{mes_int:02d}"
            except (ValueError, TypeError):
                pass
        
        # Tentar campo data
        data = record.get("data")
        if data:
            if isinstance(data, str) and len(data) >= 7:
                return data[:7]
        
        indice = record.get("indice")
        if indice is not None:
            return f"Índice {indice}"
        
        return None
    
    @staticmethod
    def _extract_value(record: Dict[str, Any]) -> Optional[float]:
        """Extrai valor de vazão/desvio do record."""
        # Tentar diferentes campos possíveis (VazoesTool retorna vazao_m3s)
        valor = record.get("vazao_m3s") or record.get("vazao") or record.get("valor") or record.get("desvio")
        return VazoesDataProcessor._sanitize_number(valor)
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados tabulares de VazoesTool ou DsvaguaTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Lista de dicionários com dados tabulares
        """
        # VazoesTool retorna "data", DsvaguaTool retorna "dados"
        data = tool_result.get("data") or tool_result.get("dados", [])
        
        table_data = []
        for record in data:
            periodo_key = VazoesDataProcessor._get_period_key(record)
            valor = VazoesDataProcessor._extract_value(record)
            
            # Obter informações adicionais
            posto = record.get("posto")
            nome_posto = record.get("nome_posto") or record.get("posto_nome")
            mes_nome = record.get("mes_nome")
            data_display = record.get("data_display")
            
            if valor is not None and periodo_key:
                # Formatar período para exibição como MM-YYYY
                if record.get("ano") and record.get("mes"):
                    try:
                        ano_int = int(record.get("ano"))
                        mes_int = int(record.get("mes"))
                        periodo_display = f"{mes_int:02d}-{ano_int}"  # MM-YYYY
                    except (ValueError, TypeError):
                        # Se periodo_key está em formato YYYY-MM, converter para MM-YYYY
                        if "-" in periodo_key:
                            parts = periodo_key.split("-")
                            if len(parts) == 2 and len(parts[0]) == 4:
                                periodo_display = f"{parts[1]}-{parts[0]}"  # MM-YYYY
                            else:
                                periodo_display = periodo_key
                        else:
                            periodo_display = periodo_key
                else:
                    # Se periodo_key está em formato YYYY-MM, converter para MM-YYYY
                    if "-" in periodo_key:
                        parts = periodo_key.split("-")
                        if len(parts) == 2 and len(parts[0]) == 4:
                            periodo_display = f"{parts[1]}-{parts[0]}"  # MM-YYYY
                        else:
                            periodo_display = periodo_key
                    else:
                        periodo_display = periodo_key
                
                table_data.append({
                    "periodo": periodo_key,  # Chave para ordenação (YYYY-MM)
                    "periodo_display": periodo_display,  # Para exibição (MM-YYYY)
                    "ano": record.get("ano"),
                    "mes": record.get("mes"),
                    "mes_nome": mes_nome,
                    "posto": posto,
                    "nome_posto": nome_posto or (f"Posto {posto}" if posto else None),
                    "valor": round(valor, 2)
                })
        
        return sorted(table_data, key=lambda x: x.get("periodo", ""))
    
    @staticmethod
    def extract_chart_data(tool_result: Dict[str, Any]) -> Optional[Dict]:
        """
        Extrai dados para gráfico de VazoesTool ou DsvaguaTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Dict com labels e datasets para Chart.js ou None
        """
        table_data = VazoesDataProcessor.extract_table_data(tool_result)
        
        if not table_data:
            return None
        
        # Criar uma única série temporal
        # Usar periodo_display se disponível, senão periodo
        labels = [r.get("periodo_display") or r.get("periodo") for r in table_data]
        values = [r.get("valor") for r in table_data]
        
        # Obter nome do posto se disponível para o label do dataset
        nome_posto = None
        if table_data:
            nome_posto = table_data[0].get("nome_posto")
        
        dataset_label = nome_posto if nome_posto else "Vazão"
        
        return {
            "labels": labels,
            "datasets": [{
                "label": dataset_label,
                "data": values
            }]
        } if labels else None

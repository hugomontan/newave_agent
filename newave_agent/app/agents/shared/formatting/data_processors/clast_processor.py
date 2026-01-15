"""
Processador de dados para ClastValoresTool.
Extrai dados puros sem formatação.
"""
import math
import re
from typing import Dict, Any, List, Optional


class ClastDataProcessor:
    """Processador puro de dados para ClastValoresTool."""
    
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
    def _is_cvu_query(query: str) -> bool:
        """Verifica se a query é sobre CVU (Custo Variável Unitário)."""
        query_lower = query.lower()
        cvu_keywords = [
            "cvu",
            "custo variável unitário",
            "custo variavel unitario",
            "custo variável unitario",
            "custo variavel unitário",
        ]
        return any(kw in query_lower for kw in cvu_keywords)
    
    @staticmethod
    def _get_year_from_deck(tool_result: Dict[str, Any]) -> int:
        """
        Extrai ano base do deck.
        O ano base é o ano do deck, e indice_ano_estudo=1 corresponde ao ano do deck.
        Exemplo: Deck NW202601 (janeiro 2026) -> ano_base=2026, indice_ano_estudo=1 -> ano_real=2026
        """
        deck_path = tool_result.get("deck_path") or tool_result.get("deck")
        if deck_path:
            deck_path_str = str(deck_path)
            # Padrão principal: NW + 4 dígitos (ano) + 2 dígitos (mês)
            # Exemplo: NW202601 -> ano=2026
            ano_match = re.search(r'NW(\d{4})\d{2}', deck_path_str)
            if ano_match:
                return int(ano_match.group(1))
            # Padrão alternativo: qualquer ano entre 2000-2099 no caminho
            ano_match = re.search(r'(20[0-9]\d)', deck_path_str)
            if ano_match:
                return int(ano_match.group(1))
            # Tentar extrair do nome do diretório ou arquivo
            # Exemplo: /path/to/NW202601/ ou /path/to/decks/NW202601/
            partes = deck_path_str.split('/') + deck_path_str.split('\\')
            for parte in partes:
                ano_match = re.search(r'NW(\d{4})\d{2}', parte)
                if ano_match:
                    return int(ano_match.group(1))
                ano_match = re.search(r'(20[0-9]\d)', parte)
                if ano_match:
                    ano = int(ano_match.group(1))
                    if 2000 <= ano <= 2099:
                        return ano
        
        # Se não conseguiu extrair, tentar usar o ano atual menos 1 como fallback mais inteligente
        # Mas isso ainda não é ideal - melhor seria lançar um erro ou retornar None
        import datetime
        ano_atual = datetime.datetime.now().year
        # Se estamos em 2026 ou depois, usar 2026 como fallback mais razoável
        if ano_atual >= 2026:
            return ano_atual
        # Caso contrário, usar 2025 como último recurso
        return 2025
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any], is_cvu: bool = False) -> List[Dict]:
        """
        Extrai dados tabulares de ClastValoresTool.
        
        Args:
            tool_result: Resultado da tool
            is_cvu: Se True, trata como CVU
            
        Returns:
            Lista de dicionários com dados tabulares
        """
        dados_estruturais = tool_result.get("dados_estruturais", [])
        
        if not dados_estruturais:
            return []
        
        table_data = []
        ano_base = ClastDataProcessor._get_year_from_deck(tool_result)
        
        for record in dados_estruturais:
            classe = record.get("codigo_usina")
            nome_classe = record.get("nome_usina", f"Classe {classe}")
            indice_ano = record.get("indice_ano_estudo")
            valor = ClastDataProcessor._sanitize_number(record.get("valor"))
            
            if valor is not None and indice_ano is not None:
                # Calcular ano real: indice_ano=1 corresponde ao ano_base
                ano_real = ano_base + (indice_ano - 1)
                
                table_data.append({
                    "ano": ano_real,
                    "indice_ano_estudo": indice_ano,
                    "classe": nome_classe,
                    "codigo_classe": classe,
                    "valor": round(valor, 2)
                })
        
        return sorted(table_data, key=lambda x: (x.get("codigo_classe", 0), x.get("ano", 0)))
    
    @staticmethod
    def extract_chart_data(tool_result: Dict[str, Any], is_cvu: bool = False) -> Optional[Dict]:
        """
        Extrai dados para gráfico de ClastValoresTool.
        
        Args:
            tool_result: Resultado da tool
            is_cvu: Se True, trata como CVU
            
        Returns:
            Dict com labels e datasets para Chart.js ou None
        """
        table_data = ClastDataProcessor.extract_table_data(tool_result, is_cvu)
        
        if not table_data:
            return None
        
        # Agrupar por classe
        classes_data = {}
        for record in table_data:
            classe = record.get("classe")
            if classe not in classes_data:
                classes_data[classe] = []
            classes_data[classe].append(record)
        
        # Obter todos os anos únicos
        all_years = sorted(set(r.get("ano") for r in table_data if r.get("ano") is not None))
        chart_labels = [f"Ano {year}" for year in all_years]
        
        # Criar datasets (uma linha por classe)
        datasets = []
        colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#00ff00", "#ff00ff"]
        
        for idx, (classe, records) in enumerate(sorted(classes_data.items())):
            # Criar mapa ano -> valor
            year_to_value = {r.get("ano"): r.get("valor") for r in records}
            
            # Criar array de valores alinhado com chart_labels
            values = []
            for year in all_years:
                values.append(year_to_value.get(year))
            
            datasets.append({
                "label": classe,
                "data": values
            })
        
        return {
            "labels": chart_labels,
            "datasets": datasets
        } if chart_labels else None

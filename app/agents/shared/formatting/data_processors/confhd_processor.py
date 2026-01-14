"""
Processador de dados para ConfhdTool.
Extrai dados puros sem formatação.
"""
from typing import Dict, Any, List, Optional


class ConfhdDataProcessor:
    """Processador puro de dados para ConfhdTool."""
    
    @staticmethod
    def _normalize_field_name(key: str) -> str:
        """Normaliza nome de campo para exibição."""
        return key.replace("_", " ").title()
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados tabulares de ConfhdTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Lista de dicionários com dados tabulares (campo, valor)
        """
        # ConfhdTool retorna "dados" como lista de dicionários
        # Se houver apenas uma usina, usar o primeiro elemento
        dados_lista = tool_result.get("dados", [])
        dados_usina = tool_result.get("dados_usina", {})
        
        # Se dados_usina existe (formato antigo), usar ele
        if dados_usina and isinstance(dados_usina, dict):
            dados_dict = dados_usina
        # Se dados é uma lista não vazia, usar o primeiro elemento
        elif dados_lista and isinstance(dados_lista, list) and len(dados_lista) > 0:
            dados_dict = dados_lista[0] if isinstance(dados_lista[0], dict) else {}
        else:
            return []
        
        if not dados_dict:
            return []
        
        table_data = []
        
        # Campos importantes para priorizar
        campos_importantes = [
            "codigo_usina", "nome_usina", "ree", "status",
            "volume_inicial_percentual", "posto"
        ]
        
        all_keys = list(dados_dict.keys())
        
        # Ordenar campos: importantes primeiro
        keys_ordered = [k for k in campos_importantes if k in all_keys]
        keys_ordered.extend([k for k in sorted(all_keys) if k not in campos_importantes])
        
        for key in keys_ordered:
            valor = dados_dict.get(key)
            
            if valor is not None:
                table_data.append({
                    "campo": ConfhdDataProcessor._normalize_field_name(key),
                    "campo_key": key,
                    "valor": valor
                })
        
        return table_data

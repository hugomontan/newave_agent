"""
Processador de dados para HidrCadastroTool e TermCadastroTool.
Extrai dados puros sem formatação.
"""
from typing import Dict, Any, List, Optional


class CadastroDataProcessor:
    """Processador puro de dados para HidrCadastroTool e TermCadastroTool."""
    
    @staticmethod
    def _normalize_field_name(key: str) -> str:
        """Normaliza nome de campo para exibição."""
        # Substituir underscores por espaços e capitalizar
        return key.replace("_", " ").title()
    
    @staticmethod
    def extract_table_data(tool_result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados tabulares de HidrCadastroTool ou TermCadastroTool.
        
        Args:
            tool_result: Resultado da tool
            
        Returns:
            Lista de dicionários com dados tabulares (campo, valor)
        """
        # HidrCadastroTool retorna "dados_usina" (dicionário único)
        # TermCadastroTool retorna "data" (lista de dicionários)
        dados_usina = tool_result.get("dados_usina", {})
        dados_lista = tool_result.get("data", [])
        
        # Se dados_usina existe (formato HidrCadastroTool), usar ele
        if dados_usina and isinstance(dados_usina, dict):
            dados_dict = dados_usina
        # Se dados é uma lista não vazia (formato TermCadastroTool), usar o primeiro elemento
        elif dados_lista and isinstance(dados_lista, list) and len(dados_lista) > 0:
            dados_dict = dados_lista[0] if isinstance(dados_lista[0], dict) else {}
        else:
            return []
        
        if not dados_dict:
            return []
        
        table_data = []
        
        # Campos principais para priorizar
        campos_principais = [
            "codigo_usina", "codigo", "nome_usina", "nome",
            "potencia", "potencia_instalada", "potencia_efetiva",
            "volume_maximo", "volume_util", "volume_minimo",
            "vazao_maxima", "vazao_minima",
            "fator_capacidade", "fcmax",
            "indisponibilidade", "teif", "ip"
        ]
        
        all_keys = list(dados_dict.keys())
        
        # Priorizar campos principais
        keys_to_show = [k for k in campos_principais if k in all_keys]
        keys_to_show.extend([k for k in all_keys if k not in campos_principais])
        
        for key in keys_to_show[:50]:  # Limitar a 50 campos
            valor = dados_dict.get(key)
            
            if valor is not None:
                table_data.append({
                    "campo": CadastroDataProcessor._normalize_field_name(key),
                    "campo_key": key,
                    "valor": valor
                })
        
        return table_data

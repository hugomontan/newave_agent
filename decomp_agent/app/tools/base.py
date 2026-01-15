"""
Classe base para tools do DECOMP.
"""
from shared.base_tool import BaseTool
from typing import Dict, Any


class DECOMPTool(BaseTool):
    """
    Classe base abstrata para todas as tools do DECOMP.
    Herda de shared.base_tool.BaseTool.
    
    Cada tool deve implementar:
    - can_handle(): Verifica se pode processar a query
    - execute(): Executa a tool e retorna dados
    - get_description(): Retorna descrição para o LLM
    """
    pass

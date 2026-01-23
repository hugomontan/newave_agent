"""
Classe base para tools do NEWAVE.
Herda de shared.base_tool.BaseTool para unificação de código.
"""
from shared.base_tool import BaseTool


class NEWAVETool(BaseTool):
    """
    Classe base para todas as tools do NEWAVE.
    
    Herda de BaseTool (shared) e mantém compatibilidade com código existente.
    
    Cada tool deve implementar:
    - can_handle(): Verifica se pode processar a query
    - execute(): Executa a tool e retorna dados
    - get_description(): Retorna descrição para o LLM
    """
    pass

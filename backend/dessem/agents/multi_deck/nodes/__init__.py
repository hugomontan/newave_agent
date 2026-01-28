"""
Nodes para o Multi-Deck Agent DESSEM.

Ainda não há lógica de comparação implementada; os nodes
atuam apenas como stubs.
"""

from .comparison_tool_router import comparison_tool_router_node
from .comparison_interpreter import comparison_interpreter_node

__all__ = ["comparison_tool_router_node", "comparison_interpreter_node"]


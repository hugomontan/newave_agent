"""
Nodes genéricos do LangGraph para Single Deck Agent.
"""
from .coder import coder_node, create_coder_prompts
from .executor import executor_node
from .interpreter import interpreter_node
from .tool_router_base import execute_tool

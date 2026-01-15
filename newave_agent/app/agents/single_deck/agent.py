"""
SingleDeckAgent - Classe que encapsula o graph do single deck agent.
"""

from typing import Optional, Generator
from langgraph.graph import StateGraph
from .state import SingleDeckState
from .graph import create_single_deck_agent, get_single_deck_agent as _get_agent


class SingleDeckAgent:
    """
    Agent para consultas de um único deck.
    Encapsula o LangGraph e fornece interface simplificada.
    """
    
    def __init__(self):
        """Inicializa o agent (lazy loading do graph)."""
        self._graph: Optional[StateGraph] = None
    
    @property
    def graph(self) -> StateGraph:
        """Retorna o graph compilado (lazy loading)."""
        if self._graph is None:
            self._graph = _get_agent()
        return self._graph
    
    def run_query(
        self,
        query: str,
        deck_path: str,
        session_id: Optional[str] = None,
        llm_mode: bool = False
    ) -> dict:
        """
        Executa uma query no agent.
        
        Args:
            query: Query do usuário
            deck_path: Caminho do deck NEWAVE
            session_id: ID da sessão (opcional)
            llm_mode: Se True, usa modo LLM (RAG Enhanced + LLM Planner)
            
        Returns:
            Dict com resultado da query
        """
        from .graph import run_query as _run_query
        return _run_query(query, deck_path, session_id, llm_mode)
    
    def run_query_stream(
        self,
        query: str,
        deck_path: str,
        session_id: Optional[str] = None,
        llm_mode: bool = False
    ) -> Generator[str, None, None]:
        """
        Executa uma query no agent com streaming.
        
        Args:
            query: Query do usuário
            deck_path: Caminho do deck NEWAVE
            session_id: ID da sessão (opcional)
            llm_mode: Se True, usa modo LLM (RAG Enhanced + LLM Planner)
            
        Yields:
            Strings no formato SSE (Server-Sent Events)
        """
        from .graph import run_query_stream as _run_query_stream
        return _run_query_stream(query, deck_path, session_id, llm_mode)

"""LLM Planner para Multi-Deck Agent DECOMP."""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from decomp_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL, safe_print
from decomp_agent.app.agents.multi_deck.state import MultiDeckState

LLM_PLANNER_SYSTEM_PROMPT = """Você é especialista em idecomp para análise de decks DECOMP.
Analise a query e contexto e crie instruções detalhadas para o Coder gerar código que compara N decks DECOMP.

CONTEXTO: {relevant_docs}
QUERY: {query}

Gere instruções estruturadas sobre:
1. Arquivos DECOMP necessários
2. Classes idecomp a usar
3. Métodos e colunas relevantes
4. Exemplos de código
5. Padrões e boas práticas"""

LLM_PLANNER_USER_PROMPT = """Crie instruções detalhadas para o Coder. Responda APENAS com as instruções."""

def llm_planner_node(state: MultiDeckState) -> dict:
    query = state["query"]
    relevant_docs = "\n\n".join(state.get("relevant_docs", []))
    
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", LLM_PLANNER_SYSTEM_PROMPT),
        ("human", LLM_PLANNER_USER_PROMPT)
    ])
    
    result = (prompt | llm).invoke({"query": query, "relevant_docs": relevant_docs})
    return {"llm_instructions": result.content.strip()}

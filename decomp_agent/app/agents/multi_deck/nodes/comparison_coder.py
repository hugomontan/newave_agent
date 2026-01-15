"""Comparison Coder para Multi-Deck Agent DECOMP."""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from decomp_agent.app.agents.multi_deck.state import MultiDeckState
from decomp_agent.app.config import OPENAI_API_KEY, OPENAI_MODEL

CODER_SYSTEM_PROMPT = """Você é especialista em Python e idecomp para análise de decks DECOMP.
Gere código que:
1. Use idecomp para ler arquivos de N decks DECOMP
2. Extraia dados de TODOS os decks
3. Compare os dados entre os decks
4. Retorne dados estruturados

DECKS DISPONÍVEIS:
{deck_paths_info}

REGRAS:
- Use APENAS imports: idecomp, pandas, numpy, datetime, os, json
- O código deve ser EXECUTÁVEL diretamente
- SEMPRE identifique de qual deck cada dado vem

DOCUMENTAÇÃO:
{relevant_docs}
"""

CODER_USER_PROMPT = """Pergunta: {query}
Gere código Python para comparar os decks DECOMP. Retorne APENAS o código."""

def comparison_coder_node(state: MultiDeckState) -> dict:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, temperature=0)
    query = state["query"]
    deck_paths = state.get("deck_paths", {})
    deck_display_names = state.get("deck_display_names", {})
    relevant_docs = "\n\n".join(state.get("relevant_docs", []))
    
    deck_paths_info = "\n".join([f"- {name} ({display}): {path}" for name, (path, display) in zip(deck_paths.keys(), [(p, deck_display_names.get(n, n)) for n, p in deck_paths.items()])])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CODER_SYSTEM_PROMPT),
        ("human", CODER_USER_PROMPT)
    ])
    
    result = (prompt | llm).invoke({
        "query": query,
        "deck_paths_info": deck_paths_info,
        "relevant_docs": relevant_docs
    })
    
    code = result.content.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()
    
    return {"generated_code": code, "code_history": state.get("code_history", []) + [code]}

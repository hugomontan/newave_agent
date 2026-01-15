"""RAG Enhanced para Multi-Deck Agent DECOMP."""
from pathlib import Path
from decomp_agent.app.rag.vectorstore import similarity_search
from decomp_agent.app.config import RAG_TOP_K, BASE_DIR, safe_print
from decomp_agent.app.agents.multi_deck.state import MultiDeckState

def load_tools_context() -> str:
    try:
        tools_context_path = BASE_DIR / "docs" / "tools_context.md"
        if tools_context_path.exists():
            return tools_context_path.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""

def rag_enhanced_node(state: MultiDeckState) -> dict:
    query = state["query"]
    abstract_docs = similarity_search(query, k=RAG_TOP_K)
    abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
    tools_context = load_tools_context()
    
    relevant_docs = []
    if abstract_context:
        relevant_docs.append(f"=== DOCUMENTAÇÃO GERAL DECOMP ===\n{abstract_context}\n=== FIM ===\n")
    if tools_context:
        relevant_docs.append(f"=== DOCUMENTAÇÃO DAS TOOLS DECOMP ===\n{tools_context}\n=== FIM ===\n")
    
    return {"relevant_docs": relevant_docs, "rag_status": "success"}

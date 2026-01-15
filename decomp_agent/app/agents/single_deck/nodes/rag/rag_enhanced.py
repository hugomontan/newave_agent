"""
RAG Enhanced Node para modo LLM DECOMP.
Busca em toda documentação + carrega tools_context.md para dar contexto completo ao LLM Planner.
Para Single Deck Agent DECOMP.
"""
from pathlib import Path
from typing import Dict, Any
from decomp_agent.app.rag.vectorstore import similarity_search
from decomp_agent.app.rag.indexer import load_specific_documentation, DECOMP_FILES
from decomp_agent.app.config import RAG_TOP_K, BASE_DIR, safe_print
from decomp_agent.app.agents.single_deck.state import SingleDeckState


def load_tools_context() -> str:
    """
    Carrega o documento tools_context.md do DECOMP.
    
    Returns:
        Conteúdo do tools_context.md ou string vazia se não encontrado
    """
    try:
        tools_context_path = BASE_DIR / "docs" / "tools_context.md"
        if not tools_context_path.exists():
            tools_context_path = Path("docs/tools_context.md")
        
        if tools_context_path.exists():
            content = tools_context_path.read_text(encoding="utf-8")
            safe_print(f"[RAG ENHANCED DECOMP] ✅ tools_context.md carregado ({len(content)} caracteres)")
            return content
        else:
            safe_print("[RAG ENHANCED DECOMP] ⚠️ tools_context.md não encontrado")
            return ""
    except Exception as e:
        safe_print(f"[RAG ENHANCED DECOMP] ❌ Erro ao carregar tools_context.md: {e}")
        return ""


def rag_enhanced_node(state: SingleDeckState) -> dict:
    """
    RAG completo: busca em toda documentação + tools_context.md
    Usado no modo LLM para dar contexto completo ao LLM Planner.
    
    Args:
        state: Estado do Single Deck Agent DECOMP
        
    Returns:
        Dict com:
        - relevant_docs: Lista com contexto completo (documentação + tools_context)
        - rag_status: "success"
    """
    query = state["query"]
    
    safe_print("[RAG ENHANCED DECOMP] ===== INÍCIO: rag_enhanced_node =====")
    safe_print(f"[RAG ENHANCED DECOMP] Query: {query[:100]}")
    
    try:
        # ETAPA 1: Busca semântica em toda documentação
        safe_print("[RAG ENHANCED DECOMP] ETAPA 1: Buscando em toda documentação...")
        
        abstract_docs = similarity_search(query, k=RAG_TOP_K)
        abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
        
        safe_print(f"[RAG ENHANCED DECOMP] ✅ {len(abstract_docs)} documentos do abstract encontrados")
        
        # ETAPA 2: Carregar tools_context.md
        safe_print("[RAG ENHANCED DECOMP] ETAPA 2: Carregando tools_context.md...")
        tools_context = load_tools_context()
        
        # ETAPA 3: Combinar contextos
        relevant_docs = []
        
        if abstract_context:
            relevant_docs.append(f"""
=== DOCUMENTAÇÃO GERAL DECOMP ===
{abstract_context}
=== FIM DA DOCUMENTAÇÃO GERAL ===
""")
        
        if tools_context:
            relevant_docs.append(f"""
=== DOCUMENTAÇÃO DAS TOOLS DECOMP ===
{tools_context}
=== FIM DA DOCUMENTAÇÃO DAS TOOLS ===
""")
        
        safe_print(f"[RAG ENHANCED DECOMP] ✅ Contexto completo preparado ({sum(len(doc) for doc in relevant_docs)} caracteres)")
        safe_print("[RAG ENHANCED DECOMP] ===== FIM: rag_enhanced_node =====")
        
        return {
            "relevant_docs": relevant_docs,
            "rag_status": "success"
        }
    except Exception as e:
        safe_print(f"[RAG ENHANCED DECOMP] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return {
            "relevant_docs": [],
            "rag_status": "success"
        }

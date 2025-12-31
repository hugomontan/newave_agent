"""
RAG Enhanced Node para modo LLM.
Busca em toda documentação + carrega tools_context.md para dar contexto completo ao LLM Planner.
"""
from pathlib import Path
from app.agents.state import AgentState
from app.rag.vectorstore import similarity_search
from app.rag.indexer import load_specific_documentation, NEWAVE_FILES
from app.config import RAG_TOP_K, BASE_DIR, safe_print


def load_tools_context() -> str:
    """
    Carrega o documento tools_context.md.
    
    Returns:
        Conteúdo do tools_context.md ou string vazia se não encontrado
    """
    try:
        tools_context_path = BASE_DIR / "docs" / "tools_context.md"
        if not tools_context_path.exists():
            # Tentar caminho alternativo
            tools_context_path = Path("docs/tools_context.md")
        
        if tools_context_path.exists():
            content = tools_context_path.read_text(encoding="utf-8")
            safe_print(f"[RAG ENHANCED] ✅ tools_context.md carregado ({len(content)} caracteres)")
            return content
        else:
            safe_print("[RAG ENHANCED] ⚠️ tools_context.md não encontrado")
            return ""
    except Exception as e:
        safe_print(f"[RAG ENHANCED] ❌ Erro ao carregar tools_context.md: {e}")
        return ""


def rag_enhanced_node(state: AgentState) -> dict:
    """
    RAG completo: busca em toda documentação + tools_context.md
    Usado no modo LLM para dar contexto completo ao LLM Planner.
    
    Fluxo:
    1. Busca semântica em toda documentação (abstract + arquivos específicos)
    2. Carrega tools_context.md
    3. Combina contextos e retorna
    
    Args:
        state: Estado do agente
        
    Returns:
        Dict com:
        - relevant_docs: Lista com contexto completo (documentação + tools_context)
        - rag_status: "success"
    """
    query = state["query"]
    
    safe_print("[RAG ENHANCED] ===== INÍCIO: rag_enhanced_node =====")
    safe_print(f"[RAG ENHANCED] Query: {query[:100]}")
    
    try:
        # ETAPA 1: Busca semântica em toda documentação (abstract + arquivos específicos)
        safe_print("[RAG ENHANCED] ETAPA 1: Buscando em toda documentação...")
        
        # Buscar no abstract (já indexado no ChromaDB)
        abstract_docs = similarity_search(query, k=RAG_TOP_K)
        abstract_context = "\n\n".join([doc.page_content for doc in abstract_docs])
        
        safe_print(f"[RAG ENHANCED] ✅ {len(abstract_docs)} documentos do abstract encontrados")
        
        # ETAPA 2: Tentar identificar arquivos relevantes e carregar documentação específica
        safe_print("[RAG ENHANCED] ETAPA 2: Identificando arquivos relevantes...")
        
        # Lista de arquivos candidatos baseado em palavras-chave da query
        query_lower = query.lower()
        arquivos_candidatos = []
        
        # Mapear palavras-chave para arquivos
        keywords_to_files = {
            "clast": ["clast.dat"],
            "carga": ["sistema.dat"],
            "demanda": ["sistema.dat"],
            "expt": ["expt.dat"],
            "modif": ["modif.dat"],
            "vazao": ["vazoes.dat"],
            "vazão": ["vazoes.dat"],
            "hidr": ["hidr.dat"],
            "confhd": ["confhd.dat"],
            "cadic": ["c_adic.dat"],
            "agrint": ["agrint.dat"],
            "intercambio": ["sistema.dat", "agrint.dat"],
            "intercâmbio": ["sistema.dat", "agrint.dat"],
            "dsvagua": ["dsvagua.dat"],
            "restricao": ["restricao-eletrica.csv"],
            "restrição": ["restricao-eletrica.csv"],
        }
        
        # Identificar arquivos candidatos
        for keyword, files in keywords_to_files.items():
            if keyword in query_lower:
                arquivos_candidatos.extend(files)
        
        # Remover duplicatas mantendo ordem
        arquivos_candidatos = list(dict.fromkeys(arquivos_candidatos))
        
        # Limitar a 3 arquivos para não sobrecarregar
        arquivos_candidatos = arquivos_candidatos[:3]
        
        specific_context = ""
        if arquivos_candidatos:
            safe_print(f"[RAG ENHANCED] Arquivos candidatos identificados: {arquivos_candidatos}")
            try:
                specific_context = load_specific_documentation(arquivos_candidatos)
                safe_print(f"[RAG ENHANCED] ✅ Documentação específica carregada ({len(specific_context)} caracteres)")
            except Exception as e:
                safe_print(f"[RAG ENHANCED] ⚠️ Erro ao carregar documentação específica: {e}")
                specific_context = ""
        else:
            safe_print("[RAG ENHANCED] Nenhum arquivo específico identificado")
        
        # ETAPA 3: Carregar tools_context.md
        safe_print("[RAG ENHANCED] ETAPA 3: Carregando tools_context.md...")
        tools_context = load_tools_context()
        
        # ETAPA 4: Combinar contextos
        safe_print("[RAG ENHANCED] ETAPA 4: Combinando contextos...")
        
        context_parts = []
        
        # Adicionar abstract
        if abstract_context:
            context_parts.append(f"=== DOCUMENTAÇÃO NEWAVE (ABSTRACT) ===\n{abstract_context}")
        
        # Adicionar documentação específica
        if specific_context:
            context_parts.append(f"=== DOCUMENTAÇÃO ESPECÍFICA DE ARQUIVOS ===\n{specific_context}")
        
        # Adicionar tools_context
        if tools_context:
            context_parts.append(f"=== DOCUMENTAÇÃO DE CONTEXTO DAS TOOLS ===\n{tools_context}")
        
        # Combinar tudo
        combined_context = "\n\n".join(context_parts)
        
        safe_print(f"[RAG ENHANCED] ✅ Contexto combinado preparado ({len(combined_context)} caracteres)")
        safe_print("[RAG ENHANCED] ===== FIM: rag_enhanced_node =====")
        
        return {
            "relevant_docs": [combined_context],
            "rag_status": "success"
        }
        
    except Exception as e:
        safe_print(f"[RAG ENHANCED] ❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()
        # Retornar contexto vazio em caso de erro - LLM Planner pode tentar sem contexto
        return {
            "relevant_docs": [],
            "rag_status": "success"  # Ainda é success, apenas sem docs
        }


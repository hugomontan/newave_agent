"""
Vector store para RAG do DECOMP.
Usa ChromaDB com collection separada para DECOMP.
"""
from langchain_chroma import Chroma
from langchain_core.documents import Document
from backend.decomp.config import DECOMP_CHROMA_DIR as CHROMA_DIR
from backend.core.azure_openai import get_azure_embeddings


_vectorstore = None


def get_embeddings():
    """Retorna o modelo de embeddings configurado."""
    return get_azure_embeddings()


def get_vectorstore() -> Chroma:
    """Retorna a instância do vectorstore DECOMP (singleton)."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="decomp_docs",
            embedding_function=get_embeddings(),
            persist_directory=str(CHROMA_DIR)
        )
    return _vectorstore


def add_documents(documents: list[Document]) -> None:
    """Adiciona documentos ao vectorstore DECOMP."""
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents)


def similarity_search(query: str, k: int = 5) -> list[Document]:
    """Busca documentos similares à query no vectorstore DECOMP."""
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(query, k=k)

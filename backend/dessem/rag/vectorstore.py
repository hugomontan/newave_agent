from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.dessem.config import DESSEM_CHROMA_DIR as CHROMA_DIR
from backend.core.azure_openai import get_azure_embeddings

_vectorstore = None


def get_embeddings():
    """Retorna o modelo de embeddings configurado para o DESSEM."""
    return get_azure_embeddings()


def get_vectorstore() -> Chroma:
    """Retorna a instância singleton do vectorstore de documentação DESSEM."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="dessem_docs",
            embedding_function=get_embeddings(),
            persist_directory=str(CHROMA_DIR),
        )
    return _vectorstore


def add_documents(documents: list[Document]) -> None:
    """Adiciona documentos ao vectorstore DESSEM."""
    vs = get_vectorstore()
    vs.add_documents(documents)


def similarity_search(query: str, k: int = 5) -> list[Document]:
    """Busca documentos similares à query na base DESSEM."""
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)


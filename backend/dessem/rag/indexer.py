from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.dessem.config import DESSEM_DOCS_DIR as DOCS_DIR, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP
from backend.dessem.rag.vectorstore import add_documents, get_vectorstore


def get_docs_root() -> Path:
    """
    Retorna o diretório raiz de documentação DESSEM.

    Espera-se que a documentação fique em `data/dessem/docs/`.
    """
    return DOCS_DIR


def get_abstract_path() -> Path:
    """
    Caminho para um arquivo `abstract.md` de documentação geral do DESSEM.

    Opcional: se o arquivo não existir, uma exceção será levantada
    apenas quando o indexador for chamado.
    """
    docs_root = get_docs_root()
    abstract_path = docs_root / "abstract.md"
    if abstract_path.exists():
        return abstract_path
    raise FileNotFoundError(f"abstract.md não encontrado em {docs_root}")


def parse_markdown_doc(doc_path: Path) -> list[Document]:
    """Divide um arquivo markdown em chunks para RAG."""
    content = doc_path.read_text(encoding="utf-8")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    chunks = splitter.split_text(content)
    docs: list[Document] = []

    for i, chunk in enumerate(chunks):
        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": str(doc_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "doc_type": "dessem_markdown",
                },
            )
        )

    return docs


def index_documentation() -> int:
    """
    Indexa a documentação básica do DESSEM em Chroma.

    No momento, se existir `abstract.md` em `data/dessem/docs/`,
    apenas esse arquivo é indexado.
    """
    vectorstore = get_vectorstore()
    existing = vectorstore._collection.count()
    if existing > 0:
        return existing

    abstract_path = get_abstract_path()
    documents = parse_markdown_doc(abstract_path)
    add_documents(documents)
    return len(documents)


def reindex_documentation() -> int:
    """Limpa o índice DESSEM e reindexa a documentação."""
    vectorstore = get_vectorstore()
    ids = vectorstore._collection.get().get("ids", [])
    if ids:
        vectorstore._collection.delete(ids=ids)

    abstract_path = get_abstract_path()
    documents = parse_markdown_doc(abstract_path)
    add_documents(documents)
    return len(documents)


import re
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import DOCS_DIR, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP
from app.rag.vectorstore import get_vectorstore, add_documents


# Mapeamento de arquivos NEWAVE para seus nomes de arquivo de documentação
NEWAVE_FILES = {
    "caso.dat": "caso_dat.md",
    "manutt.dat": "manutt_dat.md", 
    "clast.dat": "clast_dat.md",
    "agrint.dat": "agrint_dat.md",
    "cvar.dat": "cvar_dat.md",
    "sistema.dat": "sistema_dat.md",
    "ree.dat": "ree_dat.md",
    "confhd.dat": "confhd_dat.md",
    "hidr.dat": "hidr_dat.md",
    "vazoes.dat": "vazoes_dat.md",
    "exph.dat": "exph_dat.md",
    "expt.dat": "expt_dat.md",
    "modif.dat": "modif_dat.md",
    "c_adic.dat": "c_adic_dat.md",
    "adterm.dat": "adterm_dat.md",
}


def get_abstract_path() -> Path:
    """Retorna o caminho do arquivo abstract.md."""
    from app.config import BASE_DIR
    
    # Tenta primeiro relativo ao BASE_DIR
    abstract_path = BASE_DIR / "docs" / "abstract.md"
    if abstract_path.exists():
        return abstract_path
    
    # Tenta no diretório atual
    abstract_path = Path("docs/abstract.md")
    if abstract_path.exists():
        return abstract_path
    
    raise FileNotFoundError(f"abstract.md não encontrado em {BASE_DIR / 'docs'}")


def get_specific_doc_path(file_name: str) -> Path:
    """
    Retorna o caminho da documentação específica de um arquivo NEWAVE.
    
    Args:
        file_name: Nome do arquivo NEWAVE (ex: "hidr.dat")
        
    Returns:
        Path para o arquivo de documentação específica
    """
    from app.config import BASE_DIR
    
    file_name_lower = file_name.lower()
    
    if file_name_lower not in NEWAVE_FILES:
        raise ValueError(f"Arquivo NEWAVE não reconhecido: {file_name}")
    
    doc_filename = NEWAVE_FILES[file_name_lower]
    
    # Tenta primeiro relativo ao BASE_DIR
    specific_path = BASE_DIR / "docs" / "specific" / doc_filename
    if specific_path.exists():
        return specific_path
    
    # Tenta no diretório atual
    specific_path = Path("docs/specific") / doc_filename
    if specific_path.exists():
        return specific_path
    
    raise FileNotFoundError(f"Documentação específica não encontrada: {doc_filename}")


def load_specific_documentation(file_names: list[str]) -> str:
    """
    Carrega a documentação específica de um ou mais arquivos NEWAVE.
    
    Args:
        file_names: Lista de nomes de arquivos NEWAVE (ex: ["hidr.dat", "confhd.dat"])
        
    Returns:
        Conteúdo concatenado das documentações específicas
    """
    docs_content = []
    
    for file_name in file_names:
        try:
            doc_path = get_specific_doc_path(file_name)
            content = doc_path.read_text(encoding="utf-8")
            docs_content.append(f"\n{'='*60}\n# Documentação: {file_name.upper()}\n{'='*60}\n\n{content}")
        except (FileNotFoundError, ValueError) as e:
            docs_content.append(f"\n[ERRO] Não foi possível carregar documentação de {file_name}: {e}\n")
    
    return "\n".join(docs_content)


def parse_abstract(doc_path: Path) -> list[Document]:
    """
    Parseia o abstract.md e cria chunks.
    Este é o primeiro estágio do RAG - documento geral.
    """
    content = doc_path.read_text(encoding="utf-8")
    
    # Para o abstract, queremos chunks menores e mais focados
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n---\n", "\n### ", "\n## ", "\n\n", "\n", " "]
    )
    
    chunks = text_splitter.split_text(content)
    
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "source": str(doc_path),
                "section": "abstract",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_type": "abstract"
            }
        )
        documents.append(doc)
    
    return documents


def index_abstract() -> int:
    """
    Indexa apenas o abstract.md no ChromaDB.
    Retorna o número de documentos indexados.
    """
    abstract_path = get_abstract_path()
    
    vectorstore = get_vectorstore()
    existing = vectorstore._collection.count()
    
    if existing > 0:
        return existing
    
    documents = parse_abstract(abstract_path)
    add_documents(documents)
    
    return len(documents)


def reindex_abstract() -> int:
    """
    Reindexa o abstract.md (limpa e indexa novamente).
    """
    vectorstore = get_vectorstore()
    
    ids = vectorstore._collection.get()["ids"]
    if ids:
        vectorstore._collection.delete(ids=ids)
    
    abstract_path = get_abstract_path()
    documents = parse_abstract(abstract_path)
    add_documents(documents)
    
    return len(documents)


# Funções de compatibilidade com código antigo
def parse_documentation(doc_path: Path) -> list[Document]:
    """Mantido para compatibilidade. Usa parse_abstract."""
    return parse_abstract(doc_path)


def index_documentation() -> int:
    """Mantido para compatibilidade. Usa index_abstract."""
    return index_abstract()


def reindex_documentation() -> int:
    """Mantido para compatibilidade. Usa reindex_abstract."""
    return reindex_abstract()

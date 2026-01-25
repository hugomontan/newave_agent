"""
Módulo de observabilidade com Langfuse para rastrear chamadas LLM.
Genérico para uso em NEWAVE e DECOMP agents.
"""
from typing import Optional
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
import os


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: str = "agent",
    metadata: Optional[dict] = None,
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None
) -> Optional[CallbackHandler]:
    """
    Retorna um callback handler do Langfuse para rastrear chamadas LLM.
    
    Args:
        session_id: ID da sessão (geralmente o deck_path ou session_id)
        user_id: ID do usuário (opcional)
        trace_name: Nome do trace no Langfuse
        metadata: Metadados adicionais para o trace
        public_key: Chave pública do Langfuse (se None, tenta do ambiente)
        secret_key: Chave secreta do Langfuse (se None, tenta do ambiente)
        host: Host do Langfuse (se None, tenta do ambiente)
        
    Returns:
        CallbackHandler do Langfuse ou None se não configurado
    """
    # Obter credenciais do ambiente se não fornecidas
    if not public_key:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    if not secret_key:
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not host:
        host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://us.cloud.langfuse.com"
    
    if not public_key or not secret_key:
        return None
    
    # Configurar variáveis de ambiente (necessário para CallbackHandler)
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    os.environ["LANGFUSE_HOST"] = host
    
    # Criar cliente Langfuse para verificação
    try:
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
    except Exception as e:
        return None
    
    # Criar CallbackHandler
    try:
        handler = CallbackHandler(
            public_key=public_key,
            update_trace=True,
        )
        return handler
    except Exception as e:
        return None


def flush_langfuse(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: Optional[str] = None
):
    """
    Força o envio de todos os eventos pendentes para o Langfuse.
    Útil para chamar antes de encerrar a aplicação.
    """
    try:
        if not public_key:
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        if not secret_key:
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if not host:
            host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://us.cloud.langfuse.com"
        
        if not public_key or not secret_key:
            return
        
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        client.flush()
    except Exception as e:
        pass

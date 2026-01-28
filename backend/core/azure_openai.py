"""
Factory central para criação de modelos de embeddings usando Azure OpenAI.

Esta factory é usada pelos módulos de RAG (NEWAVE, DECOMP, DESSEM) e pelo
matcher semântico para garantir uma configuração consistente de embeddings.

Configuração esperada via variáveis de ambiente (recomendado em produção):
- AZURE_OPENAI_API_KEY: chave do recurso Azure OpenAI
- AZURE_OPENAI_ENDPOINT: endpoint, ex.: https://it-commodities.openai.azure.com/
- AZURE_OPENAI_API_VERSION: versão da API, ex.: 2024-02-01

Fallback:
- Se AZURE_OPENAI_API_KEY não for definida, usa OPENAI_API_KEY.
- Se AZURE_OPENAI_ENDPOINT não estiver definida, será levantado um erro
  explícito na criação do modelo de embeddings.
"""

from typing import Optional

from langchain_openai import AzureOpenAIEmbeddings

from backend.core.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    OPENAI_EMBEDDING_MODEL,
    safe_print,
)


def get_azure_embeddings(
    *,
    model: Optional[str] = None,
) -> AzureOpenAIEmbeddings:
    """
    Cria e retorna uma instância de AzureOpenAIEmbeddings configurada.

    Args:
        model: Nome do modelo/deployment a ser usado. Se None, usa
            OPENAI_EMBEDDING_MODEL (default: text-embedding-3-small).

    Raises:
        RuntimeError: Se endpoint ou chave de API não estiverem configurados.
    """
    api_key = AZURE_OPENAI_API_KEY
    endpoint = AZURE_OPENAI_ENDPOINT
    api_version = AZURE_OPENAI_API_VERSION
    model_name = model or OPENAI_EMBEDDING_MODEL

    missing = []
    if not api_key:
        missing.append("AZURE_OPENAI_API_KEY (ou OPENAI_API_KEY)")
    if not endpoint:
        missing.append("AZURE_OPENAI_ENDPOINT")

    if missing:
        msg = (
            "[AZURE OPENAI] Configuração inválida para embeddings. "
            "Variáveis obrigatórias ausentes: " + ", ".join(missing)
        )
        safe_print(msg)
        raise RuntimeError(msg)

    return AzureOpenAIEmbeddings(
        model=model_name,
        api_key=api_key,
        azure_endpoint=endpoint,
        openai_api_version=api_version,
    )


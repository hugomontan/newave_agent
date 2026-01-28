import types

import backend.core.azure_openai as azure_module
from backend.core import config


def test_get_azure_embeddings_fails_without_required_config(monkeypatch):
    """
    Deve falhar explicitamente quando endpoint ou chave não estiverem configurados.
    """
    # Isolar o módulo de config com valores vazios
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", None, raising=False)
    monkeypatch.setattr(config, "AZURE_OPENAI_ENDPOINT", None, raising=False)

    # Recarregar o módulo azure_openai para garantir que use o config monkeypatched
    # (importlib.reload não é estritamente necessário se a função lê direto de config)
    azure_module.config = config  # type: ignore[attr-defined]

    try:
        azure_module.get_azure_embeddings()
        assert False, "Era esperado RuntimeError quando config está incompleta"
    except RuntimeError as exc:
        assert "Configuração inválida para embeddings" in str(exc)


def test_get_azure_embeddings_uses_configured_values(monkeypatch):
    """
    Deve instanciar o modelo de embeddings Azure quando config estiver completa.
    """
    # Valores dummy para não bater em nenhum endpoint real durante o teste
    monkeypatch.setattr(config, "AZURE_OPENAI_API_KEY", "dummy-key", raising=False)
    monkeypatch.setattr(
        config,
        "AZURE_OPENAI_ENDPOINT",
        "https://dummy-endpoint.openai.azure.com/",
        raising=False,
    )
    monkeypatch.setattr(
        config,
        "AZURE_OPENAI_API_VERSION",
        "2024-02-01",
        raising=False,
    )
    monkeypatch.setattr(
        config,
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
        raising=False,
    )

    azure_module.config = config  # type: ignore[attr-defined]

    embeddings = azure_module.get_azure_embeddings()
    # Verificações mínimas sem fazer chamadas reais
    assert hasattr(embeddings, "embed_query")


"""
Entry point unificado - FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.newave.api import app as newave_app
from backend.decomp.api import app as decomp_app
from backend.dessem.api import app as dessem_app
from backend.core.azure_openai import get_azure_embeddings
from backend.core.config import safe_print

app = FastAPI(title="NW Multi Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount agents
app.mount("/api/newave", newave_app)
app.mount("/api/decomp", decomp_app)
app.mount("/api/dessem", dessem_app)


@app.on_event("startup")
async def validate_embeddings_config() -> None:
    """
    Valida a configuração de embeddings Azure OpenAI na subida da API.

    Garante que as variáveis necessárias estejam presentes e que o modelo
    possa ser instanciado, falhando cedo em caso de configuração inválida.
    """
    try:
        # Apenas instanciar o objeto já valida presença de endpoint/chave.
        _ = get_azure_embeddings()
        safe_print("[AZURE OPENAI] Configuração de embeddings validada com sucesso.")
    except Exception as exc:
        # Falhar explicitamente para evitar erros tardios em tempo de requisição.
        raise RuntimeError(
            "[AZURE OPENAI] Falha ao inicializar embeddings. "
            "Verifique as variáveis de ambiente de Azure OpenAI."
        ) from exc


@app.get("/")
def root():
    return {"status": "ok", "agents": ["newave", "decomp", "dessem"]}

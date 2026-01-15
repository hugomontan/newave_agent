"""
Backend unificado que roteia requisições para NEWAVE e DECOMP agents.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar apps dos agents
from newave_agent.app.main import app as newave_app
from decomp_agent.app.main import app as decomp_app

# Criar app principal
app = FastAPI(
    title="NW Multi Agent API",
    description="API unificada para consultas em decks NEWAVE e DECOMP",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar sub-apps
app.mount("/api/newave", newave_app)
app.mount("/api/decomp", decomp_app)

@app.get("/")
async def root():
    """Endpoint raiz que retorna informações dos modelos disponíveis."""
    return {
        "message": "NW Multi Agent API",
        "models": {
            "newave": {
                "name": "NEWAVE",
                "description": "Modelo de médio a longo prazo (até 5 anos, mensal)",
                "endpoints": "/api/newave/*"
            },
            "decomp": {
                "name": "DECOMP",
                "description": "Modelo de curto prazo (até 12 meses, semanal/mensal)",
                "endpoints": "/api/decomp/*"
            }
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

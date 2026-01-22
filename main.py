"""
Backend unificado que roteia requisições para NEWAVE e DECOMP agents.
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Importar apps dos agents
from newave_agent.app.main import app as newave_app
from decomp_agent.app.main import app as decomp_app

# Criar app principal
app = FastAPI(
    title="NW Multi Agent API",
    description="API unificada para consultas em decks NEWAVE e DECOMP",
    version="1.0.0"
)

# Lista de origens permitidas
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Middleware personalizado para garantir CORS em todas as rotas (incluindo sub-apps montados)
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Verificar se é uma requisição OPTIONS (preflight)
        if request.method == "OPTIONS":
            response = Response()
            if origin and origin in ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Expose-Headers"] = "*"
                response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # Processar requisição normal
        response = await call_next(request)
        
        # Adicionar headers CORS à resposta (sempre, se a origem for permitida)
        if origin and origin in ALLOWED_ORIGINS:
            # Não sobrescrever se já existir (pode ter sido adicionado pelo sub-app)
            if "Access-Control-Allow-Origin" not in response.headers:
                response.headers["Access-Control-Allow-Origin"] = origin
            if "Access-Control-Allow-Credentials" not in response.headers:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            if "Access-Control-Expose-Headers" not in response.headers:
                response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

# Adicionar middleware personalizado que garante CORS em TODAS as rotas
# Incluindo sub-apps montados (que não herdam middlewares do app principal)
# Este middleware é adicionado PRIMEIRO para ser executado por ÚLTIMO (ordem reversa no FastAPI)
app.add_middleware(CustomCORSMiddleware)

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

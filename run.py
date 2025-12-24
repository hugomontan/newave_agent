"""
Script para iniciar o servidor da API NEWAVE Agent.

Uso:
    python run.py

O servidor será iniciado em http://localhost:8000
Documentação da API em http://localhost:8000/docs
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


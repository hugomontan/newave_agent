"""
Entry point unificado - FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.newave.api import app as newave_app
from backend.decomp.api import app as decomp_app

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

@app.get("/")
def root():
    return {"status": "ok", "agents": ["newave", "decomp"]}

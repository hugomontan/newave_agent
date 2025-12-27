import uuid
import shutil
import zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.config import UPLOADS_DIR
from app.agents import run_query, run_query_stream
from app.rag import index_documentation


app = FastAPI(
    title="NEWAVE Agent API",
    description="API para consultas inteligentes em decks NEWAVE usando LangGraph e RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, Path] = {}


class QueryRequest(BaseModel):
    session_id: str
    query: str
    analysis_mode: str = "single"  # "single" ou "comparison"


class QueryResponse(BaseModel):
    session_id: str
    query: str
    response: str
    generated_code: str
    execution_success: bool
    execution_output: str | None = None
    raw_data: dict | list | None = None  # Dados brutos para download
    retry_count: int = 0
    error: str | None = None
    comparison_data: dict | None = None  # Dados de comparação multi-deck


class UploadResponse(BaseModel):
    session_id: str
    message: str
    files_count: int


class IndexResponse(BaseModel):
    documents_count: int
    message: str


def extract_json_data(stdout: str) -> tuple[str, dict | list | None]:
    """Extrai dados JSON do output se presentes."""
    if "---JSON_DATA_START---" in stdout and "---JSON_DATA_END---" in stdout:
        parts = stdout.split("---JSON_DATA_START---")
        clean_output = parts[0].strip()
        json_part = parts[1].split("---JSON_DATA_END---")[0].strip()
        try:
            import json
            raw_data = json.loads(json_part)
            return clean_output, raw_data
        except:
            return stdout, None
    return stdout, None


@app.on_event("startup")
async def startup_event():
    """Indexa a documentação ao iniciar."""
    try:
        count = index_documentation()
        print(f"Documentação indexada: {count} documentos")
    except Exception as e:
        print(f"Erro ao indexar documentação: {e}")


@app.get("/")
async def root():
    return {
        "message": "NEWAVE Agent API",
        "docs": "/docs",
        "endpoints": ["/upload", "/query", "/sessions/{session_id}", "/index"]
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_deck(file: UploadFile = File(...)):
    """
    Upload de um deck NEWAVE (arquivo .zip).
    Retorna um session_id para uso nas queries.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos .zip são aceitos"
        )
    
    session_id = str(uuid.uuid4())
    session_path = UPLOADS_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)
    
    zip_path = session_path / file.filename
    with open(zip_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(session_path)
    
    zip_path.unlink()
    
    extracted_items = list(session_path.iterdir())
    if len(extracted_items) == 1 and extracted_items[0].is_dir():
        inner_dir = extracted_items[0]
        for item in inner_dir.iterdir():
            shutil.move(str(item), str(session_path / item.name))
        inner_dir.rmdir()
    
    files_count = len(list(session_path.glob("*")))
    sessions[session_id] = session_path
    
    return UploadResponse(
        session_id=session_id,
        message="Deck NEWAVE carregado com sucesso",
        files_count=files_count
    )


@app.post("/query", response_model=QueryResponse)
async def query_deck(request: QueryRequest):
    """
    Envia uma pergunta sobre o deck NEWAVE.
    Requer um session_id válido de um upload anterior.
    """
    session_id = request.session_id
    
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Sessão {session_id} não encontrada. Faça upload do deck primeiro."
            )
    
    deck_path = str(sessions[session_id])
    
    try:
        result = run_query(request.query, deck_path, session_id=session_id)
        
        execution_result = result.get("execution_result") or {}
        stdout = execution_result.get("stdout", "")
        
        # Extrair dados JSON se presentes
        clean_output, raw_data = extract_json_data(stdout)
        
        return QueryResponse(
            session_id=session_id,
            query=request.query,
            response=result.get("final_response", ""),
            generated_code=result.get("generated_code", ""),
            execution_success=execution_result.get("success", False),
            execution_output=clean_output,
            raw_data=raw_data,
            retry_count=result.get("retry_count", 0),
            error=result.get("error"),
            comparison_data=result.get("comparison_data")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar query: {str(e)}"
        )


@app.post("/query/stream")
async def query_deck_stream(request: QueryRequest):
    """
    Envia uma pergunta sobre o deck NEWAVE com streaming de eventos.
    Retorna Server-Sent Events (SSE) com o progresso da execução.
    """
    session_id = request.session_id
    analysis_mode = request.analysis_mode or "single"
    
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Sessão {session_id} não encontrada. Faça upload do deck primeiro."
            )
    
    deck_path = str(sessions[session_id])
    
    def event_generator():
        try:
            yield from run_query_stream(request.query, deck_path, session_id=session_id, analysis_mode=analysis_mode)
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retorna informações sobre uma sessão.
    """
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Sessão {session_id} não encontrada"
            )
    
    session_path = sessions[session_id]
    files = [f.name for f in session_path.glob("*") if f.is_file()]
    
    return {
        "session_id": session_id,
        "path": str(session_path),
        "files": files,
        "files_count": len(files)
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Remove uma sessão e seus arquivos.
    """
    session_path = UPLOADS_DIR / session_id
    
    if session_path.exists():
        shutil.rmtree(session_path)
    
    if session_id in sessions:
        del sessions[session_id]
    
    return {"message": f"Sessão {session_id} removida com sucesso"}


@app.post("/index", response_model=IndexResponse)
async def reindex_docs():
    """
    Reindexa a documentação do inewave.
    """
    from app.rag import reindex_documentation
    
    try:
        count = reindex_documentation()
        return IndexResponse(
            documents_count=count,
            message="Documentação reindexada com sucesso"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao reindexar: {str(e)}"
        )


class LoadDeckRequest(BaseModel):
    deck_name: str


@app.post("/load-deck", response_model=UploadResponse)
async def load_deck_from_repo(request: LoadDeckRequest):
    """
    Carrega um deck do repositório (decks/).
    """
    from app.utils.deck_loader import load_deck
    import uuid
    
    try:
        deck_path = load_deck(request.deck_name)
        
        # Criar sessão para o deck carregado
        session_id = str(uuid.uuid4())
        session_path = UPLOADS_DIR / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Copiar arquivos do deck para a sessão
        import shutil
        for item in deck_path.iterdir():
            if item.is_file():
                shutil.copy2(item, session_path / item.name)
        
        files_count = len(list(session_path.glob("*")))
        sessions[session_id] = session_path
        
        return UploadResponse(
            session_id=session_id,
            message=f"Deck {request.deck_name} carregado do repositório",
            files_count=files_count
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Deck {request.deck_name} não encontrado no repositório: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar deck: {str(e)}"
        )


@app.post("/init-comparison", response_model=UploadResponse)
async def init_comparison_mode():
    """
    Inicializa o modo comparação usando os decks do repositório.
    """
    from app.utils.deck_loader import get_december_deck_path
    import uuid
    import shutil
    
    try:
        # Usar deck de dezembro como base para a sessão
        deck_path = get_december_deck_path()
        
        # Criar sessão para comparação
        session_id = str(uuid.uuid4())
        session_path = UPLOADS_DIR / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        
        # Copiar arquivos do deck de dezembro para a sessão
        for item in deck_path.iterdir():
            if item.is_file():
                shutil.copy2(item, session_path / item.name)
        
        files_count = len(list(session_path.glob("*")))
        sessions[session_id] = session_path
        
        return UploadResponse(
            session_id=session_id,
            message="Modo comparação inicializado (usando decks do repositório)",
            files_count=files_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao inicializar modo comparação: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


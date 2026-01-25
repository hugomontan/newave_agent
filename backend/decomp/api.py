"""Main API para DECOMP Agent."""
import sys
import os
import builtins

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

_original_print = builtins.print

def _safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(str(arg).encode('ascii', errors='replace').decode('ascii'))
        try:
            _original_print(*safe_args, **kwargs)
        except Exception:
            pass

if sys.platform == 'win32':
    builtins.print = _safe_print

import uuid
import shutil
import zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.decomp.config import UPLOADS_DIR
from backend.decomp.agents.single_deck.graph import run_query as single_deck_run_query, run_query_stream as single_deck_run_query_stream
from backend.decomp.agents.multi_deck.graph import run_query as multi_deck_run_query, run_query_stream as multi_deck_run_query_stream
from backend.decomp.rag import index_documentation
from backend.decomp.utils.dadger_cache import get_cached_dadger, get_cache_stats
from backend.decomp.utils.deck_loader import list_available_decks, load_deck
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

app = FastAPI(
    title="DECOMP Agent API",
    description="API para consultas inteligentes em decks DECOMP usando LangGraph e RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

sessions: dict[str, Path] = {}
comparison_sessions: dict[str, list[str]] = {}

class QueryRequest(BaseModel):
    session_id: str
    query: str
    analysis_mode: str = "single"

class QueryResponse(BaseModel):
    session_id: str
    query: str
    response: str
    error: str | None = None
    comparison_data: dict | None = None
    visualization_data: dict | None = None

class UploadResponse(BaseModel):
    session_id: str
    message: str
    files_count: int

class IndexResponse(BaseModel):
    documents_count: int
    message: str

class LoadDeckRequest(BaseModel):
    deck_name: str

class InitComparisonRequest(BaseModel):
    selected_decks: list[str] | None = None

class DeckInfo(BaseModel):
    name: str
    display_name: str
    year: int
    month: int
    week: int | None = None

class DecksListResponse(BaseModel):
    decks: list[DeckInfo]
    total: int

class ComparisonInitResponse(BaseModel):
    session_id: str
    message: str
    selected_decks: list[DeckInfo]
    files_count: int


def preload_decomp_decks():
    """
    Preload de todos os decks DECOMP disponíveis no cache.
    Executa de forma síncrona no startup para garantir que tudo esteja carregado.
    """
    try:
        print("\n" + "="*60)
        print("[PRELOAD DECOMP] ⚡ Iniciando preload de decks...")
        print("="*60)
        start_time = time.time()
        
        # Listar todos os decks disponíveis
        available_decks = list_available_decks()
        
        if not available_decks:
            print("[PRELOAD DECOMP] ⚠️ Nenhum deck DECOMP encontrado")
            return
        
        print(f"[PRELOAD DECOMP] 📦 Encontrados {len(available_decks)} decks")
        
        # Preload em paralelo (usar até 8 workers para não sobrecarregar)
        max_workers = min(8, len(available_decks))
        loaded_count = 0
        error_count = 0
        errors_detail = []
        
        def load_single_deck(deck_info):
            """Carrega um deck no cache."""
            try:
                deck_name = deck_info["name"]
                # Carregar deck (extrai se necessário)
                deck_path = load_deck(deck_name)
                # Carregar Dadger no cache
                dadger = get_cached_dadger(str(deck_path))
                if dadger:
                    return (deck_name, True, None)
                return (deck_name, False, "Dadger não encontrado")
            except Exception as e:
                return (deck_info.get('name', 'unknown'), False, str(e))
        
        print(f"[PRELOAD DECOMP] 🔄 Carregando {len(available_decks)} decks em paralelo ({max_workers} workers)...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(load_single_deck, deck): deck 
                for deck in available_decks
            }
            
            for future in as_completed(futures):
                deck_name, success, error = future.result()
                if success:
                    loaded_count += 1
                    if loaded_count % 10 == 0:
                        print(f"[PRELOAD DECOMP] ✅ {loaded_count}/{len(available_decks)} decks carregados...")
                else:
                    error_count += 1
                    errors_detail.append((deck_name, error))
                    if error:
                        print(f"[PRELOAD DECOMP] ⚠️ Erro ao carregar {deck_name}: {error}")
        
        elapsed = time.time() - start_time
        cache_stats = get_cache_stats()
        
        print("\n" + "-"*60)
        print(f"[PRELOAD DECOMP] ✅ Preload concluído em {elapsed:.2f}s")
        print(f"[PRELOAD DECOMP]   📊 Decks carregados: {loaded_count}/{len(available_decks)}")
        print(f"[PRELOAD DECOMP]   ❌ Erros: {error_count}")
        if error_count > 0:
            print(f"[PRELOAD DECOMP]   ⚠️ Decks com erro: {[e[0] for e in errors_detail[:5]]}")
        print(f"[PRELOAD DECOMP]   💾 Cache: {cache_stats['currsize']}/{cache_stats['maxsize']} slots usados")
        if cache_stats['hits'] + cache_stats['misses'] > 0:
            print(f"[PRELOAD DECOMP]   🎯 Hit rate: {cache_stats['hit_rate']*100:.1f}%")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[PRELOAD DECOMP] ❌ Erro crítico no preload: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")

@app.on_event("startup")
async def startup_event():
    """Executa no startup do servidor, ANTES de aceitar requisições."""
    # 1. Indexar documentação primeiro
    try:
        count = index_documentation()
        print(f"📚 Documentação DECOMP indexada: {count} documentos")
    except Exception as e:
        print(f"⚠️ Erro ao indexar documentação DECOMP: {e}")
    
    # 2. Preload síncrono de decks (bloqueia até terminar)
    preload_decomp_decks()

@app.get("/")
async def root():
    return {
        "message": "DECOMP Agent API",
        "docs": "/docs",
        "endpoints": ["/upload", "/query", "/sessions/{session_id}", "/index", "/decks", "/load-deck", "/init-comparison"]
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_deck(file: UploadFile = File(...)):
    """Upload de um deck DECOMP (arquivo .zip)."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .zip são aceitos")
    
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
        message="Deck DECOMP carregado com sucesso",
        files_count=files_count
    )

@app.post("/query", response_model=QueryResponse)
async def query_deck(request: QueryRequest):
    """Envia uma pergunta sobre o deck DECOMP."""
    session_id = request.session_id
    
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    
    deck_path = str(sessions[session_id])
    analysis_mode = request.analysis_mode or "single"
    
    try:
        if analysis_mode == "comparison":
            selected_decks = comparison_sessions.get(session_id)
            result = multi_deck_run_query(request.query, deck_path, session_id=session_id, selected_decks=selected_decks)
        else:
            result = single_deck_run_query(request.query, deck_path, session_id=session_id)
        
        return QueryResponse(
            session_id=session_id,
            query=request.query,
            response=result.get("final_response", ""),
            error=result.get("error"),
            comparison_data=result.get("comparison_data"),
            visualization_data=result.get("visualization_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar query: {str(e)}")

@app.post("/query/stream")
async def query_deck_stream(request: QueryRequest):
    """Envia uma pergunta sobre o deck DECOMP com streaming."""
    session_id = request.session_id
    analysis_mode = request.analysis_mode or "single"
    
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    
    deck_path = str(sessions[session_id])
    
    def event_generator():
        try:
            if analysis_mode == "comparison":
                selected_decks = comparison_sessions.get(session_id)
                yield from multi_deck_run_query_stream(request.query, deck_path, session_id=session_id, selected_decks=selected_decks)
            else:
                yield from single_deck_run_query_stream(request.query, deck_path, session_id=session_id)
        except Exception as e:
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retorna informações sobre uma sessão."""
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    
    session_path = sessions[session_id]
    files = [f.name for f in session_path.glob("*") if f.is_file()]
    
    return {"session_id": session_id, "path": str(session_path), "files": files, "files_count": len(files)}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Remove uma sessão e seus arquivos."""
    session_path = UPLOADS_DIR / session_id
    if session_path.exists():
        shutil.rmtree(session_path)
    if session_id in sessions:
        del sessions[session_id]
    return {"message": f"Sessão {session_id} removida com sucesso"}

@app.post("/index", response_model=IndexResponse)
async def reindex_docs():
    """Reindexa a documentação do DECOMP."""
    from backend.decomp.rag import reindex_documentation
    try:
        count = reindex_documentation()
        return IndexResponse(documents_count=count, message="Documentação DECOMP reindexada com sucesso")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao reindexar: {str(e)}")

@app.get("/decks", response_model=DecksListResponse)
async def list_decks():
    """Lista todos os decks DECOMP disponíveis."""
    from backend.decomp.utils.deck_loader import list_available_decks
    
    try:
        available_decks = list_available_decks()
        
        decks = [
            DeckInfo(
                name=d["name"], 
                display_name=d["display_name"], 
                year=d["year"], 
                month=d["month"],
                week=d.get("week")
            ) 
            for d in available_decks
        ]
        
        return DecksListResponse(decks=decks, total=len(decks))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao listar decks: {str(e)}")

@app.post("/load-deck", response_model=UploadResponse)
async def load_deck_from_repo(request: LoadDeckRequest):
    """Carrega um deck DECOMP do repositório."""
    from backend.decomp.utils.deck_loader import load_deck
    try:
        deck_path = load_deck(request.deck_name)
        session_id = str(uuid.uuid4())
        sessions[session_id] = deck_path
        files_count = len(list(deck_path.glob("*")))
        return UploadResponse(session_id=session_id, message=f"Deck {request.deck_name} carregado", files_count=files_count)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Deck {request.deck_name} não encontrado: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar deck: {str(e)}")

@app.post("/init-comparison", response_model=ComparisonInitResponse)
async def init_comparison_mode(request: InitComparisonRequest = None):
    """Inicializa o modo comparação DECOMP."""
    from backend.decomp.utils.deck_loader import list_available_decks, load_multiple_decks, get_deck_display_name
    try:
        available_decks = list_available_decks()
        if not available_decks:
            raise HTTPException(status_code=404, detail="Nenhum deck DECOMP disponível")
        
        if request and request.selected_decks:
            available_names = {d["name"] for d in available_decks}
            for deck_name in request.selected_decks:
                if deck_name not in available_names:
                    raise HTTPException(status_code=404, detail=f"Deck {deck_name} não encontrado")
            selected_deck_names = request.selected_decks
        else:
            if len(available_decks) >= 2:
                selected_deck_names = [d["name"] for d in available_decks[-2:]]
            else:
                selected_deck_names = [available_decks[0]["name"]]
        
        deck_paths = load_multiple_decks(selected_deck_names)
        first_deck_path = deck_paths[selected_deck_names[0]]
        session_id = str(uuid.uuid4())
        sessions[session_id] = first_deck_path
        comparison_sessions[session_id] = selected_deck_names
        files_count = len(list(first_deck_path.glob("*")))
        
        selected_decks_info = [
            DeckInfo(
                name=name,
                display_name=get_deck_display_name(name),
                year=next(d["year"] for d in available_decks if d["name"] == name),
                month=next(d["month"] for d in available_decks if d["name"] == name),
                week=next((d.get("week") for d in available_decks if d["name"] == name), None)
            )
            for name in selected_deck_names
        ]
        
        return ComparisonInitResponse(
            session_id=session_id,
            message=f"Modo comparação DECOMP inicializado com {len(selected_deck_names)} deck(s)",
            selected_decks=selected_decks_info,
            files_count=files_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar modo comparação: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

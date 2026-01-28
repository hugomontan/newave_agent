"""Main API para DESSEM Agent."""

import os
import sys
import builtins
import uuid
import shutil
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.dessem.config import UPLOADS_DIR
from backend.dessem.agent import (
    run_query as single_deck_run_query,
    run_query_stream as single_deck_run_query_stream,
)
from backend.dessem.agents.multi_deck.graph import (
    run_query as multi_deck_run_query,
    run_query_stream as multi_deck_run_query_stream,
)
from backend.dessem.rag import index_documentation
from backend.dessem.utils.deck_loader import list_available_decks, load_deck


# =======================
# Patch de print para Windows
# =======================

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

_original_print = builtins.print


def _safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode("ascii", errors="replace").decode("ascii"))
            else:
                safe_args.append(str(arg).encode("ascii", errors="replace").decode("ascii"))
        try:
            _original_print(*safe_args, **kwargs)
        except Exception:
            pass


if sys.platform == "win32":
    builtins.print = _safe_print


# =======================
# App e CORS
# =======================

app = FastAPI(
    title="DESSEM Agent API",
    description="API para consultas em decks DESSEM usando LangGraph e RAG",
    version="1.0.0",
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
    error: Optional[str] = None
    comparison_data: Optional[dict] = None
    visualization_data: Optional[dict] = None


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


class DecksListResponse(BaseModel):
    decks: list[DeckInfo]
    total: int


class ComparisonInitResponse(BaseModel):
    session_id: str
    message: str
    selected_decks: list[DeckInfo]
    files_count: int


def preload_dessem_decks():
    """
    Preload simples de todos os decks DESSEM disponíveis.

    Diferente de NEWAVE/DECOMP, aqui apenas garantimos que os ZIPs
    foram extraídos; não há cache adicional.
    """
    try:
        print("\n" + "=" * 60)
        print("[PRELOAD DESSEM] Iniciando preload de decks...")
        print("=" * 60)

        available_decks = list_available_decks()
        if not available_decks:
            print("[PRELOAD DESSEM] Nenhum deck DESSEM encontrado")
            return

        print(f"[PRELOAD DESSEM] Encontrados {len(available_decks)} decks")

        max_workers = min(8, len(available_decks))
        extracted_count = 0
        error_count = 0
        errors_detail: list[tuple[str, str]] = []

        def extract_single(deck_info: dict):
            try:
                deck_name = deck_info["name"]
                load_deck(deck_name)
                return deck_name, True, ""
            except Exception as exc:  # pragma: no cover - log apenas
                return deck_info.get("name", "unknown"), False, str(exc)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(extract_single, d): d for d in available_decks}
            for future in as_completed(futures):
                deck_name, success, err = future.result()
                if success:
                    extracted_count += 1
                else:
                    error_count += 1
                    errors_detail.append((deck_name, err))

        print(f"[PRELOAD DESSEM] Decks extraídos: {extracted_count}")
        print(f"[PRELOAD DESSEM] Erros: {error_count}")
        if error_count:
            print(f"[PRELOAD DESSEM] Decks com erro: {[e[0] for e in errors_detail[:5]]}")
        print("=" * 60 + "\n")
    except Exception as exc:  # pragma: no cover
        print(f"[PRELOAD DESSEM] Erro crítico: {exc}")


@app.on_event("startup")
async def startup_event():
    """Executa no startup do servidor DESSEM."""
    try:
        count = index_documentation()
        print(f"[DESSEM RAG] Documentação indexada: {count} documentos")
    except Exception as exc:  # pragma: no cover
        print(f"[DESSEM RAG] Erro ao indexar documentação: {exc}")

    preload_dessem_decks()


@app.get("/")
async def root():
    return {
        "message": "DESSEM Agent API",
        "docs": "/docs",
        "endpoints": [
            "/upload",
            "/query",
            "/query/stream",
            "/sessions/{session_id}",
            "/index",
            "/decks/list",
            "/load-deck",
            "/init-comparison",
        ],
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_deck(file: UploadFile = File(...)):
    """Upload de um deck DESSEM (.zip)."""
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
        message="Deck DESSEM carregado com sucesso",
        files_count=files_count,
    )


def _ensure_session_path(session_id: str) -> Path:
    if session_id not in sessions:
        session_path = UPLOADS_DIR / session_id
        if session_path.exists():
            sessions[session_id] = session_path
        else:
            raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    return sessions[session_id]


@app.post("/query", response_model=QueryResponse)
async def query_deck(request: QueryRequest):
    """Executa uma consulta sobre um deck DESSEM."""
    session_path = _ensure_session_path(request.session_id)
    deck_path = str(session_path)
    analysis_mode = request.analysis_mode or "single"

    try:
        if analysis_mode == "comparison":
            selected = comparison_sessions.get(request.session_id)
            result = multi_deck_run_query(
                request.query,
                deck_path,
                session_id=request.session_id,
                selected_decks=selected,
            )
        else:
            result = single_deck_run_query(request.query, deck_path, session_id=request.session_id)

        return QueryResponse(
            session_id=request.session_id,
            query=request.query,
            response=result.get("final_response", ""),
            error=result.get("error"),
            comparison_data=result.get("comparison_data"),
            visualization_data=result.get("visualization_data"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao processar query: {exc}")


@app.post("/query/stream")
async def query_deck_stream(request: QueryRequest):
    """Executa uma consulta sobre um deck DESSEM com SSE."""
    session_path = _ensure_session_path(request.session_id)
    deck_path = str(session_path)
    analysis_mode = request.analysis_mode or "single"

    def event_generator():
        try:
            if analysis_mode == "comparison":
                selected = comparison_sessions.get(request.session_id)
                yield from multi_deck_run_query_stream(
                    request.query,
                    deck_path,
                    session_id=request.session_id,
                    selected_decks=selected,
                )
            else:
                yield from single_deck_run_query_stream(
                    request.query,
                    deck_path,
                    session_id=request.session_id,
                )
        except Exception as exc:
            import json

            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retorna informações sobre uma sessão DESSEM."""
    session_path = _ensure_session_path(session_id)
    files = [f.name for f in session_path.glob("*") if f.is_file()]
    return {
        "session_id": session_id,
        "path": str(session_path),
        "files": files,
        "files_count": len(files),
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Remove uma sessão DESSEM e seus arquivos."""
    session_path = UPLOADS_DIR / session_id
    if session_path.exists():
        shutil.rmtree(session_path)
    if session_id in sessions:
        del sessions[session_id]
    return {"message": f"Sessão {session_id} removida com sucesso"}


@app.post("/index", response_model=IndexResponse)
async def reindex_docs():
    """Reindexa a documentação do DESSEM."""
    from backend.dessem.rag import reindex_documentation

    try:
        count = reindex_documentation()
        return IndexResponse(documents_count=count, message="Documentação DESSEM reindexada com sucesso")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao reindexar: {exc}")


@app.get("/decks/list", response_model=DecksListResponse)
async def list_decks():
    """Lista todos os decks DESSEM disponíveis no repositório."""
    try:
        available = list_available_decks()
        decks = [
            DeckInfo(
                name=d["name"],
                display_name=d["display_name"],
                year=d["year"],
                month=d["month"],
            )
            for d in available
        ]
        return DecksListResponse(decks=decks, total=len(decks))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao listar decks: {exc}")


@app.post("/load-deck", response_model=UploadResponse)
async def load_deck_from_repo(request: LoadDeckRequest):
    """Carrega um deck DESSEM diretamente do repositório (data/dessem/decks)."""
    try:
        deck_path = load_deck(request.deck_name)
        session_id = str(uuid.uuid4())
        sessions[session_id] = deck_path
        files_count = len(list(deck_path.glob("*")))
        return UploadResponse(
            session_id=session_id,
            message=f"Deck {request.deck_name} carregado",
            files_count=files_count,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Deck {request.deck_name} não encontrado: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar deck: {exc}")


@app.post("/init-comparison", response_model=ComparisonInitResponse)
async def init_comparison_mode(request: InitComparisonRequest | None = None):
    """
    Inicializa o modo comparação DESSEM.

    Se `selected_decks` não for informado, usa os dois decks mais recentes.
    """
    from backend.dessem.utils.deck_loader import (
        list_available_decks,
        load_multiple_decks,
        get_deck_display_name,
    )

    try:
        available = list_available_decks()
        if not available:
            raise HTTPException(status_code=404, detail="Nenhum deck DESSEM disponível")

        if request and request.selected_decks:
            names = {d["name"] for d in available}
            for deck_name in request.selected_decks:
                if deck_name not in names:
                    raise HTTPException(status_code=404, detail=f"Deck {deck_name} não encontrado")
            selected_names = request.selected_decks
        else:
            if len(available) >= 2:
                selected_names = [d["name"] for d in available[-2:]]
            else:
                selected_names = [available[0]["name"]]

        deck_paths = load_multiple_decks(selected_names)
        first_deck_path = deck_paths[selected_names[0]]

        session_id = str(uuid.uuid4())
        sessions[session_id] = first_deck_path
        comparison_sessions[session_id] = selected_names

        files_count = len(list(first_deck_path.glob("*")))

        selected_info = [
            DeckInfo(
                name=name,
                display_name=get_deck_display_name(name),
                year=next(d["year"] for d in available if d["name"] == name),
                month=next(d["month"] for d in available if d["name"] == name),
            )
            for name in selected_names
        ]

        return ComparisonInitResponse(
            session_id=session_id,
            message=f"Modo comparação DESSEM inicializado com {len(selected_names)} deck(s)",
            selected_decks=selected_info,
            files_count=files_count,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar modo comparação: {exc}")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)


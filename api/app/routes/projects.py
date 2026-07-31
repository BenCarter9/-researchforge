from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_claude_client, get_db, get_sec_client
from app.ids import new_id
from app.ingest.chunk_transcript import chunk_transcript
from app.llm.client import ClaudeClient
from app.models import AnalysisRun, Document, DocumentChunk, ResearchProject
from app.pipeline.runner import STAGES, PipelineDeps, run_pipeline
from app.pipeline.stages import build_deps
from app.sec.client import SecClient, TickerNotFound

router = APIRouter()

# api/storage, relative to this file (api/app/routes/projects.py).
_DEFAULT_STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"


def _storage_dir() -> Path:
    return Path(os.environ.get("STORAGE_DIR", str(_DEFAULT_STORAGE_DIR)))


class ProjectCreate(BaseModel):
    company: str
    ticker: str
    research_date: str | None = None


@router.post("/api/projects")
async def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    sec: SecClient = Depends(get_sec_client),
) -> dict:
    try:
        cik = await sec.resolve_cik(payload.ticker)
    except TickerNotFound:
        raise HTTPException(
            status_code=422, detail=f"Unknown ticker: {payload.ticker!r}"
        )

    project_id = new_id()
    project = ResearchProject(
        id=project_id,
        company=payload.company,
        ticker=payload.ticker,
        cik=cik,
        research_date=payload.research_date,
        status="created",
    )
    db.add(project)
    db.commit()

    return {"project_id": project_id}


@router.post("/api/projects/{project_id}/transcript")
async def upload_transcript(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    project = db.get(ResearchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(status_code=400, detail="file is required")
        raw = await file.read()
        text = raw.decode("utf-8")
    else:
        body = await request.json()
        text = body.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="text is required")

    document_id = new_id()
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()

    project_dir = _storage_dir() / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    storage_path = project_dir / f"{document_id}.txt"
    storage_path.write_text(text, encoding="utf-8")

    document = Document(
        id=document_id,
        project_id=project_id,
        type="transcript",
        source="upload",
        checksum=checksum,
        storage_ref=str(storage_path),
    )
    db.add(document)

    chunks = chunk_transcript(text)
    for c in chunks:
        db.add(
            DocumentChunk(
                id=new_id(),
                document_id=document_id,
                section_label=c.section_label,
                text=c.text,
                speaker=c.speaker,
            )
        )
    db.commit()

    return {"document_id": document_id, "chunk_count": len(chunks)}


def _run_pipeline_background(project_id: str, deps: PipelineDeps, session_dep) -> None:
    """Runs in FastAPI's BackgroundTasks (a separate thread, after the
    response has been sent). Opens its own DB session via `session_dep` -
    the (possibly test-overridden) get_db generator - rather than importing
    SessionLocal directly, so tests can point this at their in-memory DB.
    """
    gen = session_dep()
    session = next(gen)
    try:
        asyncio.run(run_pipeline(project_id, session, deps))
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@router.post("/api/projects/{project_id}/analyze")
async def analyze_project(
    project_id: str,
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    sec: SecClient = Depends(get_sec_client),
    claude: ClaudeClient = Depends(get_claude_client),
) -> dict:
    project = db.get(ResearchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")

    deps = build_deps(sec, claude)
    # Resolve get_db through the app's own dependency-override table so the
    # background task (which runs after this request's session has closed,
    # and needs its own) honors any test override of get_db.
    session_dep = request.app.dependency_overrides.get(get_db, get_db)
    background.add_task(_run_pipeline_background, project_id, deps, session_dep)

    return {"status": "started"}


@router.get("/api/projects/{project_id}/status")
def get_status(project_id: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id)
    ).all()
    by_stage = {row.stage: row for row in rows}
    return [
        {"stage": s, "status": by_stage[s].status, "error": by_stage[s].error}
        for s in STAGES
        if s in by_stage
    ]

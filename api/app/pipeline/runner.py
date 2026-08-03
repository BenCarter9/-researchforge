from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import AnalysisRun

STAGES = [
    "fetch_filing",
    "fetch_xbrl",
    "chunk",
    "financials",
    "generate_snapshot",
    "generate_business",
    "generate_financials",
    "generate_risks",
    "validate",
]


@dataclass
class PipelineContext:
    project_id: str
    session: Session
    data: dict = field(default_factory=dict)  # scratch space for inter-stage data


# Each stage is an async callable taking the context and doing its work.
StageFn = Callable[[PipelineContext], Awaitable[None]]


@dataclass
class PipelineDeps:
    fetch_filing: StageFn
    fetch_xbrl: StageFn
    chunk: StageFn
    financials: StageFn
    generate_snapshot: StageFn
    generate_business: StageFn
    generate_financials: StageFn
    generate_risks: StageFn
    validate: StageFn


async def run_pipeline(project_id: str, session: Session, deps: PipelineDeps) -> None:
    runs: dict[str, AnalysisRun] = {}
    for stage_name in STAGES:
        run = AnalysisRun(
            id=str(uuid4()),
            project_id=project_id,
            stage=stage_name,
            status="pending",
        )
        session.add(run)
        runs[stage_name] = run
    session.commit()

    ctx = PipelineContext(project_id=project_id, session=session)

    for stage_name in STAGES:
        run = runs[stage_name]
        run.status = "running"
        session.commit()

        stage_fn: StageFn = getattr(deps, stage_name)
        try:
            await stage_fn(ctx)
        except Exception as exc:
            run.status = "error"
            run.error = str(exc)
            session.commit()
            return

        run.status = "done"
        session.commit()

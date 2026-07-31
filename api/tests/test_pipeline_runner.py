from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import ResearchProject, AnalysisRun
from app.pipeline.runner import run_pipeline, PipelineDeps, STAGES


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


async def noop(ctx):
    return None


def _make_project(session):
    proj = ResearchProject(id="p1", company="Acme", ticker="ACME")
    session.add(proj)
    session.commit()
    return proj


def _runs_by_stage(session, project_id):
    rows = session.scalars(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id)
    ).all()
    return {row.stage: row for row in rows}


async def test_all_stages_done():
    session = _session()
    _make_project(session)

    deps = PipelineDeps(**{stage: noop for stage in STAGES})

    await run_pipeline("p1", session, deps)

    rows = session.scalars(
        select(AnalysisRun).where(AnalysisRun.project_id == "p1")
    ).all()
    assert len(rows) == len(STAGES)

    by_stage = {row.stage: row for row in rows}
    assert set(by_stage.keys()) == set(STAGES)
    for stage in STAGES:
        assert by_stage[stage].status == "done", f"{stage} should be done"


async def test_stage_error_stops_and_leaves_later_pending():
    session = _session()
    _make_project(session)

    async def boom(ctx):
        raise ValueError("boom")

    kwargs = {stage: noop for stage in STAGES}
    kwargs["generate_risks"] = boom
    deps = PipelineDeps(**kwargs)

    # Should not raise.
    await run_pipeline("p1", session, deps)

    by_stage = _runs_by_stage(session, "p1")

    error_index = STAGES.index("generate_risks")
    for stage in STAGES[:error_index]:
        assert by_stage[stage].status == "done", f"{stage} should be done"

    assert by_stage["generate_risks"].status == "error"
    assert "boom" in by_stage["generate_risks"].error

    for stage in STAGES[error_index + 1:]:
        assert by_stage[stage].status == "pending", f"{stage} should still be pending"

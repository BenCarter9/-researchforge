import os

from fastapi import FastAPI

from app.routes.desk import router as desk_router
from app.routes.projects import router as projects_router
from app.routes.report import router as report_router

app = FastAPI(title="ResearchForge API")
app.include_router(projects_router)
app.include_router(report_router)
app.include_router(desk_router)

# Dev-only seed route for the Playwright e2e smoke test. Only registered
# when explicitly enabled - never present in a normal run of the API.
if os.environ.get("RESEARCHFORGE_DEV_SEED") == "1":
    from app.db import SessionLocal
    from app.routes.dev import ensure_schema_and_seed, router as dev_router

    app.include_router(dev_router)
    _seed_db = SessionLocal()
    try:
        ensure_schema_and_seed(_seed_db)
    finally:
        _seed_db.close()

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from fastapi import FastAPI

from app.routes.projects import router as projects_router
from app.routes.report import router as report_router

app = FastAPI(title="ResearchForge API")
app.include_router(projects_router)
app.include_router(report_router)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

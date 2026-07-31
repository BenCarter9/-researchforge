from fastapi import FastAPI

from app.routes.projects import router as projects_router

app = FastAPI(title="ResearchForge API")
app.include_router(projects_router)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

"""
FastAPI Main Application Entrypoint for Project 2 (Visual Quality Gate).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.visual_quality_gate.backend.routes import router as qc_router
from apps.visual_quality_gate.backend.config import qc_settings
from apps.visual_quality_gate.inference.model_registry import model_registry

app = FastAPI(
    title=qc_settings.PROJECT_NAME,
    version=qc_settings.VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://enterprise-copilot.pages.dev",
        "https://enterprise-qc.pages.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qc_router, prefix="/api/qc")


@app.get("/api/qc/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Project 2 - Visual Quality Gate",
        "version": qc_settings.VERSION,
        "profile": qc_settings.PROFILE.value,
        "active_model": model_registry.get_active_model()["model_id"],
        "storage_provider": qc_settings.STORAGE_PROVIDER,
        "redpanda_enabled": qc_settings.KAFKA_ENABLED,
        "erpnext_sandbox": qc_settings.ERPNEXT_USE_SANDBOX,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.visual_quality_gate.backend.main:app", host="0.0.0.0", port=8002, reload=True)

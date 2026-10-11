"""FastAPI application entry point for the Manufacturing DSS."""

from fastapi import FastAPI

from app.api.routes import router
from app.config.settings import settings


app = FastAPI(
    title="Manufacturing Hybrid Multi-Agent DSS",
    version="0.1.0",
    description=(
        "Manufacturing decision support for maintenance investigations, "
        "evidence-grounded findings, and human approval workflows."
    ),
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Report API process health."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
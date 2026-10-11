
"""FastAPI application entry point for the Manufacturing DSS."""

import logging
import re
import time
from uuid import uuid4

from fastapi import FastAPI, Request

from app.api.routes import router
from app.config.settings import settings
from app.observability.logging import (
    configure_logging,
    reset_request_id,
    set_request_id,
)
from app.observability.metrics import metrics


configure_logging()
logger = logging.getLogger(__name__)

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")

app = FastAPI(
    title="Manufacturing Hybrid Multi-Agent DSS",
    version="0.1.0",
    description=(
        "Manufacturing decision support for maintenance investigations, "
        "evidence-grounded findings, and human approval workflows."
    ),
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Record request correlation, duration, status, and failures."""

    incoming_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        incoming_request_id
        if REQUEST_ID_PATTERN.fullmatch(incoming_request_id)
        else str(uuid4())
    )

    request.state.request_id = request_id
    request_id_token = set_request_id(request_id)

    start_time = time.perf_counter()
    status_code = 500

    metrics.increment("api.requests")

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        logger.exception(
            "HTTP request failed",
            extra={"request_id": request_id},
        )
        raise

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        metrics.observe("api.request.duration_ms", duration_ms)

        if status_code >= 500:
            metrics.increment("api.errors")

        logger.info(
            "HTTP request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        reset_request_id(request_id_token)


app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Report API process health."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
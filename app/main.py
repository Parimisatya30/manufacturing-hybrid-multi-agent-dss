
"""FastAPI application entry point for the Manufacturing DSS."""

import logging
import re
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from opentelemetry import trace

from app.api.routes import router
from app.config.settings import settings
from app.observability.logging import (
    configure_logging,
    reset_request_id,
    set_request_id,
)
from app.observability.metrics import metrics
from app.observability import tracing as tracing_config  # noqa: F401
from app.api.defect_routes import router as defect_router
from app.api.rca_routes import router as rca_router
configure_logging()

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("manufacturing-dss.api")

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
        with tracer.start_as_current_span("http.request") as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("url.path", request.url.path)
            span.set_attribute("app.request_id", request_id)

            try:
                response = await call_next(request)
                status_code = response.status_code

                response.headers["X-Request-ID"] = request_id
                span.set_attribute(
                    "http.response.status_code",
                    status_code,
                )

                if status_code >= 500:
                    metrics.increment("api.errors")
                    span.set_status(
                        trace.StatusCode.ERROR,
                        description=f"HTTP {status_code} response",
                    )

                return response

            except Exception as exc:
                # Count unexpected exceptions once, and record them on the span.
                metrics.increment("api.errors")

                span.set_attribute("http.response.status_code", 500)
                span.record_exception(exc)
                span.set_status(
                    trace.StatusCode.ERROR,
                    description="HTTP request failed",
                )

                logger.exception(
                    "HTTP request failed",
                    extra={"request_id": request_id},
                )
                raise

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000

        metrics.observe("api.request.duration_ms", duration_ms)

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
app.include_router(defect_router)
app.include_router(rca_router)

@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Report API process health."""

    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
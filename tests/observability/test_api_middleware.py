
"""Tests for FastAPI request observability middleware."""

from fastapi.testclient import TestClient
from opentelemetry import trace
from app.main import app
from app.observability.metrics import metrics


client = TestClient(app)


def test_request_adds_correlation_id_header() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_valid_incoming_request_id_is_preserved() -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_incoming_request_id_is_replaced() -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "invalid request id"
    assert len(response.headers["X-Request-ID"]) == 36


def test_request_metrics_are_recorded() -> None:
    before = metrics.snapshot()
    response = client.get("/health")
    after = metrics.snapshot()

    assert response.status_code == 200
    assert (
        after["counters"].get("api.requests", 0)
        == before["counters"].get("api.requests", 0) + 1
    )
    assert (
        after["timings"]["api.request.duration_ms"]["count"]
        == before["timings"].get(
            "api.request.duration_ms", {"count": 0}
        )["count"] + 1
    )


def test_server_error_increments_error_counter() -> None:
    before = metrics.snapshot()
    errors_before = before["counters"].get("api.errors", 0)

    @app.get("/test-observability-error")
    def test_error_endpoint() -> None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500,
            detail="Simulated test error",
        )

    response = client.get("/test-observability-error")

    after = metrics.snapshot()

    assert response.status_code == 500
    assert (
        after["counters"].get("api.errors", 0)
        == errors_before + 1
    )


def test_request_id_is_available_in_logging_context() -> None:
    from app.observability.logging import request_id_context

    request_id = "correlation-test-123"

    @app.get("/test-observability-correlation")
    def test_correlation_endpoint() -> dict[str, str]:
        return {
            "request_id": request_id_context.get(),
        }

    response = client.get(
        "/test-observability-correlation",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id

def test_downstream_log_record_includes_request_id() -> None:
    import logging

    from app.observability.logging import (
        RequestContextFilter,
        request_id_context,
    )

    request_id = "downstream-correlation-456"
    token = request_id_context.set(request_id)

    try:
        record = logging.LogRecord(
            name="app.test.downstream",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Downstream tool executed",
            args=(),
            exc_info=None,
        )

        log_filter = RequestContextFilter()

        assert log_filter.filter(record) is True
        assert record.request_id == request_id
    finally:
        request_id_context.reset(token)


def test_unexpected_exception_increments_error_counter_once() -> None:
    from fastapi import HTTPException

    before = metrics.snapshot()
    errors_before = before["counters"].get("api.errors", 0)

    @app.get("/test-observability-unexpected-error")
    def unexpected_error_endpoint() -> None:
        raise RuntimeError("Simulated unexpected failure")

    # HTTPException would be handled by FastAPI, so use an unexpected
    # exception and let the test client return the generated HTTP 500.
    with TestClient(app, raise_server_exceptions=False) as error_client:
        response = error_client.get(
            "/test-observability-unexpected-error"
        )

    after = metrics.snapshot()

    assert response.status_code == 500
    assert (
        after["counters"].get("api.errors", 0)
        == errors_before + 1
    )

def test_downstream_span_shares_http_request_trace() -> None:
    @app.get("/test-observability-trace")
    def trace_endpoint() -> dict[str, object]:
        parent_span = trace.get_current_span()
        parent_context = parent_span.get_span_context()

        downstream_tracer = trace.get_tracer("manufacturing-dss.test")

        with downstream_tracer.start_as_current_span(
            "test.downstream"
        ) as downstream_span:
            downstream_context = downstream_span.get_span_context()
            downstream_parent = downstream_span.parent

            return {
                "parent_valid": parent_context.is_valid,
                "parent_trace_id": format(parent_context.trace_id, "032x"),
                "parent_span_id": format(parent_context.span_id, "016x"),
                "downstream_trace_id": format(
                    downstream_context.trace_id, "032x"
                ),
                "downstream_parent_span_id": (
                    format(downstream_parent.span_id, "016x")
                    if downstream_parent is not None
                    else None
                ),
            }

    response = client.get("/test-observability-trace")

    assert response.status_code == 200

    result = response.json()

    assert result["parent_valid"] is True
    assert result["parent_trace_id"] == result["downstream_trace_id"]
    assert result["parent_span_id"] == result["downstream_parent_span_id"]
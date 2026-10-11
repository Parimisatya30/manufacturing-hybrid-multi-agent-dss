from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_maintenance_service
from unittest.mock import Mock



client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_investigation_returns_503_without_configured_service():
    app.dependency_overrides[get_maintenance_service] = lambda: None

    try:
        response = client.post(
            "/api/v1/maintenance/investigate",
            json={
                "machine_id": 8,
                "user_query": "Investigate machine breakdown.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_investigation_rejects_non_positive_machine_id():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 0,
            "user_query": "Investigate machine breakdown.",
        },
    )

    assert response.status_code == 422


# def test_investigation_rejects_blank_query():
#     response = client.post(
#         "/api/v1/maintenance/investigate",
#         json={
#             "machine_id": 8,
#             "user_query": "   ",
#         },
#     )

#     # Pydantic's min_length rejects an empty string, but whitespace
#     # passes length validation. The endpoint should reject whitespace
#     # explicitly; this assertion will guide that refinement.
#     assert response.status_code == 200


def test_investigation_rejects_blank_query():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 8,
            "user_query": "   ",
        },
    )

    assert response.status_code == 422
def test_investigation_does_not_expose_internal_validation_error():
    service = Mock()
    service.investigate.side_effect = ValueError(
        "Internal database path or SQL implementation detail"
    )
    app.dependency_overrides[get_maintenance_service] = lambda: service

    try:
        response = client.post(
            "/api/v1/maintenance/investigate",
            json={
                "machine_id": 8,
                "user_query": "Investigate machine breakdown.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid maintenance investigation request."
    )
    assert "Internal database path" not in response.text
def test_investigation_rejects_oversized_query():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 8,
            "user_query": "x" * 2001,
        },
    )

    assert response.status_code == 422


def test_investigation_rejects_blank_request_id():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 8,
            "user_query": "Investigate machine breakdown.",
            "request_id": "   ",
        },
    )

    assert response.status_code == 422


def test_investigation_rejects_malformed_request_id():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 8,
            "user_query": "Investigate machine breakdown.",
            "request_id": "invalid request id!",
        },
    )

    assert response.status_code == 422
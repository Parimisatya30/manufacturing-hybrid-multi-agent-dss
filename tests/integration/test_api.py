from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import get_maintenance_service


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_investigation_returns_503_without_configured_service():
    response = client.post(
        "/api/v1/maintenance/investigate",
        json={
            "machine_id": 8,
            "user_query": "Investigate machine breakdown.",
        },
    )

    assert response.status_code == 503
    assert "not been configured" in response.json()["detail"]


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
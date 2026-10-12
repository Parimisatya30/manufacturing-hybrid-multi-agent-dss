
"""Integration tests for the human approval API."""

import pytest
from fastapi.testclient import TestClient

from app.api.approval_routes import get_approval_repository
from app.decision.approval_repository import ApprovalRepository
from app.main import app


SUPERVISOR_ID = "123"
INVALID_SUPERVISOR_ID = "999"


@pytest.fixture
def client(tmp_path):
    """Provide an isolated database and use the demo Supervisor ID."""
    repository = ApprovalRepository(tmp_path / "approvals.db")

    app.dependency_overrides[get_approval_repository] = lambda: repository

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_approval_repository, None)


@pytest.fixture
def pending_record(client):
    """Create a pending approval record."""
    repository = app.dependency_overrides[get_approval_repository]()
    return repository.get_or_create_pending(
        request_id="api-approval-test",
        reason="Critical machine condition requires human review.",
    )


def test_get_approval_returns_pending_status(client, pending_record):
    response = client.get(
        "/api/v1/approvals/api-approval-test",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    assert response.json()["id"] == pending_record["id"]


def test_get_approval_returns_404_for_unknown_request(client):
    response = client.get(
        "/api/v1/approvals/unknown-request",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
    )

    assert response.status_code == 404


def test_approve_pending_record(client, pending_record):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={
            "approved": True,
            "reason": "Reviewed the evidence and approved the recommendation.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["approver"] == "supervisor-123"
    assert response.json()["decided_at"] is not None


def test_reject_pending_record(client, pending_record):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={
            "approved": False,
            "reason": "Additional maintenance evidence is required.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    assert response.json()["approver"] == "supervisor-123"


@pytest.mark.parametrize("approved", [True, False])
def test_second_decision_returns_409(client, pending_record, approved):
    first_response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={"approved": True, "reason": "First decision."},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={
            "approved": approved,
            "reason": "Attempted second decision.",
        },
    )

    assert second_response.status_code == 409


def test_decision_returns_404_for_unknown_request(client):
    response = client.post(
        "/api/v1/approvals/unknown-request/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={"approved": True, "reason": "Approval test."},
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"approved": True, "reason": "   "},
        {"approved": True},
        {"approved": "yes", "reason": "Valid reason."},
    ],
)
def test_decision_rejects_invalid_payload(client, pending_record, payload):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json=payload,
    )

    assert response.status_code == 422


def test_missing_supervisor_id_returns_401(client, pending_record):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        json={"approved": True, "reason": "Approval test."},
    )

    assert response.status_code == 401


def test_invalid_supervisor_id_returns_401(client, pending_record):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": INVALID_SUPERVISOR_ID},
        json={"approved": True, "reason": "Approval test."},
    )

    assert response.status_code == 401

def test_invalid_supervisor_id_returns_401(client, pending_record):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": INVALID_SUPERVISOR_ID},
        json={"approved": True, "reason": "Approval test."},
    )

    assert response.status_code == 401


def test_request_body_cannot_override_authenticated_identity(
    client,
    pending_record,
):
    response = client.post(
        "/api/v1/approvals/api-approval-test/decision",
        headers={"X-Supervisor-ID": SUPERVISOR_ID},
        json={
            "approver": "forged-supervisor",
            "approved": True,
            "reason": "Approval test.",
        },
    )

    # The API does not accept an approver identity from the request body.
    assert response.status_code == 200
    assert response.json()["approver"] == "supervisor-123"

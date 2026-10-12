
import pytest

from app.decision.approval_repository import ApprovalRepository


@pytest.fixture
def repository(tmp_path):
    """Use an isolated temporary database for every test."""
    return ApprovalRepository(tmp_path / "approvals.db")


def test_create_pending_approval(repository):
    record = repository.create_pending(
        "request-001",
        "Critical machine finding requires supervisor review.",
    )

    assert record["request_id"] == "request-001"
    assert record["status"] == "PENDING"
    assert record["approver"] is None
    assert record["decided_at"] is None


def test_approve_pending_record(repository):
    pending = repository.create_pending(
        "request-002",
        "Critical machine finding.",
    )

    record = repository.decide(
        pending["id"],
        approver="supervisor-1",
        approved=True,
        reason="Maintenance action reviewed and approved.",
    )

    assert record["status"] == "APPROVED"
    assert record["approver"] == "supervisor-1"
    assert record["reason"] == "Maintenance action reviewed and approved."
    assert record["decided_at"] is not None


def test_reject_pending_record(repository):
    pending = repository.create_pending(
        "request-003",
        "Critical machine finding.",
    )

    record = repository.decide(
        pending["id"],
        approver="supervisor-2",
        approved=False,
        reason="Further inspection is required.",
    )

    assert record["status"] == "REJECTED"
    assert record["approver"] == "supervisor-2"


def test_decision_requires_approver_and_reason(repository):
    pending = repository.create_pending(
        "request-004",
        "Critical machine finding.",
    )

    with pytest.raises(ValueError, match="Approver identity"):
        repository.decide(
            pending["id"],
            approver=" ",
            approved=True,
            reason="Approved.",
        )

    with pytest.raises(ValueError, match="Decision reason"):
        repository.decide(
            pending["id"],
            approver="supervisor-1",
            approved=True,
            reason=" ",
        )


def test_pending_record_cannot_be_decided_twice(repository):
    pending = repository.create_pending(
        "request-005",
        "Critical machine finding.",
    )

    repository.decide(
        pending["id"],
        approver="supervisor-1",
        approved=True,
        reason="Approved after review.",
    )

    with pytest.raises(ValueError, match="no longer pending"):
        repository.decide(
            pending["id"],
            approver="supervisor-2",
            approved=False,
            reason="Attempted second decision.",
        )


def test_get_latest_returns_latest_record(repository):
    repository.create_pending("request-006", "First review.")
    latest = repository.create_pending("request-006", "Second review.")

    result = repository.get_latest("request-006")

    assert result is not None
    assert result["id"] == latest["id"]
    assert result["reason"] == "Second review."


def test_missing_record_returns_none(repository):
    assert repository.get_by_id(9999) is None
    assert repository.get_latest("unknown-request") is None


def test_get_or_create_pending_does_not_duplicate_records(repository):
    first = repository.get_or_create_pending(
        "request-retry-001",
        "Critical machine finding.",
    )
    second = repository.get_or_create_pending(
        "request-retry-001",
        "Updated retry reason.",
    )

    assert first["id"] == second["id"]
    assert second["status"] == "PENDING"
    assert second["reason"] == "Critical machine finding."


def test_get_or_create_pending_preserves_existing_decision(repository):
    pending = repository.get_or_create_pending(
        "request-retry-002",
        "Critical machine finding.",
    )

    approved = repository.decide(
        pending["id"],
        approver="supervisor-1",
        approved=True,
        reason="Reviewed and approved.",
    )

    result = repository.get_or_create_pending(
        "request-retry-002",
        "Another attempt to create a pending record.",
    )

    assert result["id"] == approved["id"]
    assert result["status"] == "APPROVED"
    assert result["approver"] == "supervisor-1"


import pytest

from app.decision.approval_gate import ApprovalGate
from app.decision.approval_policy import (
    ApprovalDecision,
    ApprovalStatus,
)


@pytest.fixture
def pending_approval():
    return ApprovalDecision(
        status=ApprovalStatus.PENDING,
        required=True,
        reason="Critical finding requires human approval.",
    )


def test_authorized_approver_can_approve(pending_approval):
    gate = ApprovalGate()

    record = gate.decide(
        pending_approval,
        approver="maintenance_manager",
        approved=True,
        reason="Inspection completed; intervention authorized.",
        authorized=True,
    )

    assert record.status == ApprovalStatus.APPROVED
    assert record.approver == "maintenance_manager"
    assert record.decided_at is not None


def test_authorized_approver_can_reject(pending_approval):
    gate = ApprovalGate()

    record = gate.decide(
        pending_approval,
        approver="maintenance_manager",
        approved=False,
        reason="Further diagnostic evidence is required.",
        authorized=True,
    )

    assert record.status == ApprovalStatus.REJECTED


def test_unauthorized_user_cannot_approve(pending_approval):
    gate = ApprovalGate()

    with pytest.raises(PermissionError):
        gate.decide(
            pending_approval,
            approver="unauthorized_user",
            approved=True,
            reason="Approve intervention.",
            authorized=False,
        )


def test_approver_identity_is_required(pending_approval):
    gate = ApprovalGate()

    with pytest.raises(ValueError, match="Approver identity"):
        gate.decide(
            pending_approval,
            approver=" ",
            approved=True,
            reason="Approve intervention.",
            authorized=True,
        )


def test_reason_is_required(pending_approval):
    gate = ApprovalGate()

    with pytest.raises(ValueError, match="reason"):
        gate.decide(
            pending_approval,
            approver="maintenance_manager",
            approved=True,
            reason=" ",
            authorized=True,
        )


def test_cannot_decide_when_approval_is_not_required():
    gate = ApprovalGate()

    not_required = ApprovalDecision(
        status=ApprovalStatus.NOT_REQUIRED,
        required=False,
        reason="No approval required.",
    )

    with pytest.raises(ValueError, match="not required"):
        gate.decide(
            not_required,
            approver="maintenance_manager",
            approved=True,
            reason="Approve intervention.",
            authorized=True,
        )
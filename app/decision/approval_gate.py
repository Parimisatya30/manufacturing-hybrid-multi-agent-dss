
from dataclasses import dataclass
from datetime import datetime, timezone

from app.decision.approval_policy import (
    ApprovalDecision,
    ApprovalStatus,
)


@dataclass(frozen=True)
class ApprovalRecord:
    status: ApprovalStatus
    approver: str | None
    reason: str
    decided_at: str | None


class ApprovalGate:
    """Records an explicit human approval or rejection."""

    def decide(
        self,
        approval: ApprovalDecision,
        *,
        approver: str,
        approved: bool,
        reason: str,
        authorized: bool,
    ) -> ApprovalRecord:
        if not approval.required:
            raise ValueError(
                "An approval decision is not required for this finding."
            )

        if not authorized:
            raise PermissionError(
                "The user is not authorized to approve this intervention."
            )

        if not approver or not approver.strip():
            raise ValueError("Approver identity is required.")

        if not reason or not reason.strip():
            raise ValueError("An approval or rejection reason is required.")

        status = (
            ApprovalStatus.APPROVED
            if approved
            else ApprovalStatus.REJECTED
        )

        return ApprovalRecord(
            status=status,
            approver=approver.strip(),
            reason=reason.strip(),
            decided_at=datetime.now(timezone.utc).isoformat(),
        )
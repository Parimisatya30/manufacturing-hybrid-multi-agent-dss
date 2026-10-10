from dataclasses import dataclass
from enum import Enum
from typing import Any


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"


@dataclass(frozen=True)
class ApprovalDecision:
    status: ApprovalStatus
    required: bool
    reason: str


class ApprovalPolicy:
    """Determines whether a decision requires human approval."""

    APPROVAL_REQUIRED_SEVERITIES = {"CRITICAL"}

    def evaluate(
        self,
        decision: dict[str, Any],
    ) -> ApprovalDecision:
        findings = decision.get("findings", [])

        requires_approval = any(
            str(finding.get("severity", "")).upper()
            in self.APPROVAL_REQUIRED_SEVERITIES
            for finding in findings
            if isinstance(finding, dict)
        )

        if requires_approval:
            return ApprovalDecision(
                status=ApprovalStatus.PENDING,
                required=True,
                reason=(
                    "A critical finding requires human approval "
                    "before a maintenance intervention is authorized."
                ),
            )

        return ApprovalDecision(
            status=ApprovalStatus.NOT_REQUIRED,
            required=False,
            reason="No critical findings require approval under this policy.",
        )
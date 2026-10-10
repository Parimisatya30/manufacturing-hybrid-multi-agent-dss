
from app.decision.approval_policy import (
    ApprovalPolicy,
    ApprovalStatus,
)


def test_critical_finding_requires_approval():
    policy = ApprovalPolicy()

    decision = policy.evaluate(
        {
            "overall_status": "CRITICAL",
            "findings": [
                {
                    "finding": "Machine is in breakdown",
                    "severity": "CRITICAL",
                    "source_ids": ["machine_lookup"],
                }
            ],
        }
    )

    assert decision.required is True
    assert decision.status == ApprovalStatus.PENDING
    assert "human approval" in decision.reason


def test_warning_finding_does_not_require_approval():
    policy = ApprovalPolicy()

    decision = policy.evaluate(
        {
            "overall_status": "WARNING",
            "findings": [
                {
                    "finding": "Maintenance inspection recommended",
                    "severity": "WARNING",
                    "source_ids": ["predictive_maintenance"],
                }
            ],
        }
    )

    assert decision.required is False
    assert decision.status == ApprovalStatus.NOT_REQUIRED


def test_empty_findings_do_not_require_approval():
    policy = ApprovalPolicy()

    decision = policy.evaluate(
        {
            "overall_status": "NORMAL",
            "findings": [],
        }
    )

    assert decision.required is False
    assert decision.status == ApprovalStatus.NOT_REQUIRED
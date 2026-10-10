
from app.decision.approval_policy import (
    ApprovalPolicy,
    ApprovalStatus,
)


def test_critical_decision_requires_human_approval():
    policy = ApprovalPolicy()

    decision = {
        "overall_status": "CRITICAL",
        "findings": [
            {
                "finding": "Machine is in breakdown",
                "severity": "CRITICAL",
                "source_ids": ["machine_lookup"],
            }
        ],
    }

    approval = policy.evaluate(decision)

    assert approval.required is True
    assert approval.status == ApprovalStatus.PENDING


def test_approval_metadata_does_not_claim_action_was_executed():
    policy = ApprovalPolicy()

    decision = {
        "overall_status": "CRITICAL",
        "findings": [
            {"finding": "Machine is in breakdown", "severity": "CRITICAL"}
        ],
    }

    approval = policy.evaluate(decision)

    assert approval.status == ApprovalStatus.PENDING
    assert not hasattr(approval, "executed")
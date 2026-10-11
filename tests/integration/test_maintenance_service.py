from unittest.mock import Mock

from app.synthesis.maintenance_service import MaintenanceService


def test_investigation_returns_decision_and_synthesized_response():
    workflow = Mock()
    workflow.run.return_value = {
        "request_id": "request-1",
        "machine_id": 8,
        "overall_status": "CRITICAL",
        "findings": [
            {
                "finding": "Machine is in breakdown",
                "severity": "CRITICAL",
                "reason": "Machine lookup reported breakdown status.",
                "source_ids": ["machine_lookup"],
            }
        ],
        "evidence": [
            {
                "source_id": "machine_lookup",
                "content": "Machine status is breakdown.",
            }
        ],
        "sensor_data_status": "UNAVAILABLE",
        "approval": {
            "required": True,
            "status": "PENDING",
            "reason": "Human approval is required.",
        },
    }

    service = MaintenanceService(workflow)

    result = service.investigate(
        machine_id=8,
        user_query="Investigate the machine breakdown.",
        request_id="request-1",
    )

    assert result["decision"]["overall_status"] == "CRITICAL"
    assert result["response"]["overall_status"] == "CRITICAL"
    assert result["response"]["approval"]["status"] == "PENDING"
    assert result["response"]["findings"][0]["supporting_evidence"] == [
        "machine_lookup"
    ]

    workflow.run.assert_called_once_with(
        machine_id=8,
        user_query="Investigate the machine breakdown.",
        request_id="request-1",
    )


def test_investigation_preserves_original_decision():
    workflow = Mock()
    decision = {
        "machine_id": 8,
        "overall_status": "WARNING",
        "findings": [],
        "evidence": [],
    }
    workflow.run.return_value = decision

    service = MaintenanceService(workflow)
    result = service.investigate(
        machine_id=8,
        user_query="Check maintenance risk.",
    )

    assert result["decision"] is decision
    assert result["response"]["overall_status"] == "WARNING"
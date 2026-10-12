
from unittest.mock import Mock

import pytest

from app.decision.decision_engine import DecisionEngine
from app.evidence.collector import EvidenceCollector
from app.tools.rag_tool import RAGTool
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool
from app.workflows.maintenance_workflow import MaintenanceWorkflow


@pytest.fixture
def workflow():
    sql_tool = Mock(spec=SQLTool)
    rag_tool = Mock(spec=RAGTool)

    sql_tool.execute.return_value = []
    rag_tool.search.return_value = []

    return MaintenanceWorkflow(
        sql_tool=sql_tool,
        rag_tool=rag_tool,
        rules_tool=RulesTool(),
        evidence_collector=EvidenceCollector(),
        decision_engine=DecisionEngine(),
    )


def test_run_queries_all_three_sources(workflow):
    result = workflow.run(
        machine_id=10,
        user_query="Assess maintenance risk",
        request_id="test-1",
    )

    assert result["machine_id"] == 10
    assert workflow.sql_tool.execute.call_count == 3
    workflow.rag_tool.search.assert_called_once()


def test_run_rejects_invalid_machine_id(workflow):
    with pytest.raises(ValueError):
        workflow.run(0, "Assess maintenance risk")


def test_run_rejects_blank_query(workflow):
    with pytest.raises(ValueError):
        workflow.run(10, "   ")


def test_vibration_rule_uses_actual_reading(workflow):
    workflow.sql_tool.execute.side_effect = [
        [],
        [],
        [{"RMS_Velocity": 11.0}],
    ]

    result = workflow.run(10, "Check vibration")

    assert result["overall_status"] == "CRITICAL"
    assert result["vibration_readings"][0]["RMS_Velocity"] == 11.0
    assert result["sensor_data_status"] == "AVAILABLE"


def test_alerts_are_classified_by_recorded_status(workflow):
    workflow.sql_tool.execute.side_effect = [
        [{"MachineID": 8, "Status": "breakdown"}],
        [
            {"PredictionID": 1, "Status": "active"},
            {"PredictionID": 2, "Status": "resolved"},
            {"PredictionID": 3, "Status": "false_positive"},
            {"PredictionID": 4, "Status": "active"},
            {"PredictionID": 5, "Status": "resolved"},
        ],
        [],
    ]

    result = workflow.run(8, "Investigate maintenance alerts")

    assert len(result["active_alerts"]) == 2
    assert len(result["resolved_alerts"]) == 2
    assert len(result["false_positive_alerts"]) == 1

    assert all(
        alert["Status"] == "active"
        for alert in result["active_alerts"]
    )
    assert all(
        alert["Status"] == "resolved"
        for alert in result["resolved_alerts"]
    )
    assert all(
        alert["Status"] == "false_positive"
        for alert in result["false_positive_alerts"]
    )


def test_missing_vibration_data_is_unavailable(workflow):
    workflow.sql_tool.execute.side_effect = [
        [{"MachineID": 8, "Status": "breakdown"}],
        [],
        [],
    ]

    result = workflow.run(8, "Investigate machine breakdown")

    assert result["sensor_data_status"] == "UNAVAILABLE"
    assert result["vibration_readings"] == []
    assert result["overall_status"] == "CRITICAL"


def test_vibration_data_with_missing_rms_is_incomplete(workflow):
    workflow.sql_tool.execute.side_effect = [
        [{"MachineID": 1, "Status": "operational"}],
        [],
        [{"RMS_Velocity": None}],
    ]

    result = workflow.run(1, "Check sensor data")

    assert result["sensor_data_status"] == "INCOMPLETE"


def test_critical_finding_persists_pending_approval(workflow, tmp_path):
    from app.decision.approval_repository import ApprovalRepository

    repository = ApprovalRepository(tmp_path / "approvals.db")
    workflow.approval_repository = repository

    workflow.sql_tool.execute.side_effect = [
        [{"MachineID": 8, "Status": "breakdown"}],
        [],
        [],
    ]

    result = workflow.run(
        8,
        "Investigate machine breakdown",
        request_id="approval-test-critical",
    )

    approval = result["approval"]
    record = repository.get_latest("approval-test-critical")

    assert approval["required"] is True
    assert approval["status"] == "PENDING"
    assert approval["record_id"] is not None
    assert record is not None
    assert record["status"] == "PENDING"


def test_non_critical_finding_does_not_create_approval(workflow, tmp_path):
    from app.decision.approval_repository import ApprovalRepository

    repository = ApprovalRepository(tmp_path / "approvals.db")
    workflow.approval_repository = repository

    result = workflow.run(
        10,
        "Assess maintenance risk",
        request_id="approval-test-normal",
    )

    assert result["approval"]["required"] is False
    assert result["approval"]["status"] == "NOT_REQUIRED"
    assert result["approval"]["record_id"] is None
    assert repository.get_latest("approval-test-normal") is None

"""Tests for the defect-monitoring workflow."""

from unittest.mock import Mock

from app.tools.rules_tool import RulesTool
from app.workflows.defect_monitoring_workflow import (
    DefectMonitoringWorkflow,
)


def build_workflow(sql_responses):
    sql_tool = Mock()
    sql_tool.execute.side_effect = sql_responses

    return DefectMonitoringWorkflow(
        sql_tool=sql_tool,
        rules_tool=RulesTool(),
        evidence_collector=Mock(),
    ), sql_tool


def test_defect_monitoring_evaluates_average_rate_in_percent():
    workflow, sql_tool = build_workflow(
        [
            [{
                "quality_check_count": 10,
                "failed_checks": 1,
                "rework_checks": 2,
                "avg_defect_rate": 0.03,
                "avg_rework_rate": 0.04,
                "avg_yield_rate": 0.93,
            }],
            [{
                "defect_type": "Cable Routing",
                "defect_records": 5,
                "affected_quantity": 7,
                "average_severity": 3.0,
            }],
            [{
                "root_cause": "Tooling Wear",
                "defect_records": 4,
                "affected_quantity": 6,
            }],
        ]
    )

    result = workflow.run(request_id="defect-test-1")

    assert result["request_id"] == "defect-test-1"
    assert result["use_case"] == "defect_monitoring"
    assert result["metrics"]["average_defect_rate_percent"] == 3.0
    assert result["overall_status"] == "WARNING"
    assert result["evidence_count"] == 4
    assert sql_tool.execute.call_count == 3

    finding = result["findings"][0]
    assert finding["severity"] == "WARNING"
    assert finding["source_ids"] == [
        "SQL:quality_control_summary",
        "RULE:average_defect_rate",
    ]


def test_defect_monitoring_returns_unavailable_without_quality_data():
    workflow, _ = build_workflow(
        [
            [{
                "quality_check_count": 0,
                "failed_checks": 0,
                "rework_checks": 0,
                "avg_defect_rate": None,
                "avg_rework_rate": None,
                "avg_yield_rate": None,
            }],
            [],
            [],
        ]
    )

    result = workflow.run()

    assert result["overall_status"] == "DATA_UNAVAILABLE"
    assert result["metrics"]["average_defect_rate_percent"] is None
    assert result["findings"][0]["severity"] == "UNKNOWN"
    assert result["evidence_count"] == 3


def test_defect_monitoring_uses_critical_threshold():
    workflow, _ = build_workflow(
        [
            [{
                "quality_check_count": 10,
                "failed_checks": 3,
                "rework_checks": 2,
                "avg_defect_rate": 0.06,
                "avg_rework_rate": 0.04,
                "avg_yield_rate": 0.90,
            }],
            [],
            [],
        ]
    )

    result = workflow.run()

    assert result["metrics"]["average_defect_rate_percent"] == 6.0
    assert result["overall_status"] == "CRITICAL"
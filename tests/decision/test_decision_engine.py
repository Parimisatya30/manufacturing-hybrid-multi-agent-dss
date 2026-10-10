
"""Tests for the manufacturing decision engine."""

from app.context.models import Evidence, RequestContext, ToolResult
from app.decision.decision_engine import DecisionEngine


def test_critical_status_takes_priority_over_warning():
    context = RequestContext(
        request_id="req-1",
        user_query="Check machine health",
    )
    context.tool_results.extend([
        ToolResult(
            tool_name="rules_tool",
            success=True,
            data={"metric": "vibration", "status": "WARNING"},
        ),
        ToolResult(
            tool_name="rules_tool",
            success=True,
            data={"metric": "temperature", "status": "CRITICAL"},
        ),
    ])

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "CRITICAL"


def test_warning_status_is_preserved():
    context = RequestContext(
        request_id="req-2",
        user_query="Check machine health",
    )
    context.tool_results.append(
        ToolResult(
            tool_name="rules_tool",
            success=True,
            data={"metric": "vibration", "status": "WARNING"},
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "WARNING"


def test_successful_results_without_status_are_normal():
    context = RequestContext(
        request_id="req-3",
        user_query="Look up a machine",
    )
    context.tool_results.append(
        ToolResult(
            tool_name="sql_tool",
            success=True,
            data=[{"machine_id": "M1", "name": "Machine 1"}],
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "NORMAL"


def test_no_successful_results_returns_insufficient_data():
    context = RequestContext(
        request_id="req-4",
        user_query="Check machine health",
    )
    context.tool_results.append(
        ToolResult(
            tool_name="sql_tool",
            success=False,
            error="Database unavailable",
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "INSUFFICIENT_DATA"
    assert result["failed_tools"] == 1
    assert result["failed_tool_errors"] == [
        {
            "tool_name": "sql_tool",
            "error": "Database unavailable",
        }
    ]


def test_evidence_is_included_in_result():
    context = RequestContext(
        request_id="req-5",
        user_query="Investigate machine health",
    )
    context.evidence.append(
        Evidence(
            source_id="SQL:machine:1",
            content="Machine status is operational",
            metadata={"source_type": "sql"},
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["evidence_count"] == 1
    assert result["evidence"][0]["source_id"] == "SQL:machine:1"
    assert result["evidence"][0]["content"] == (
        "Machine status is operational"
    )


def test_machine_breakdown_is_critical_without_vibration_data():
    context = RequestContext(
        request_id="req-breakdown",
        user_query="Investigate machine breakdown",
    )
    context.tool_results.extend([
        ToolResult(
            tool_name="machine_lookup",
            success=True,
            data=[
                {
                    "MachineID": 8,
                    "Name": "Machine Whe-40",
                    "Status": "breakdown",
                }
            ],
        ),
        ToolResult(
            tool_name="vibration_analysis",
            success=True,
            data=[],
        ),
    ])

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "CRITICAL"


def test_machine_in_maintenance_is_warning_without_critical_rules():
    context = RequestContext(
        request_id="req-maintenance",
        user_query="Check machine status",
    )
    context.tool_results.append(
        ToolResult(
            tool_name="machine_lookup",
            success=True,
            data=[
                {
                    "MachineID": 1,
                    "Status": "maintenance",
                }
            ],
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "WARNING"



def test_empty_successful_result_returns_insufficient_data():
    """An empty result must not be treated as a healthy assessment."""
    context = RequestContext(
        request_id="req-empty",
        user_query="Check machine health",
    )
    context.tool_results.append(
        ToolResult(
            tool_name="vibration_analysis",
            success=True,
            data=[],
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "INSUFFICIENT_DATA"

def test_empty_sensor_data_does_not_imply_normal_machine_health():
    """Machine records alone do not establish normal sensor health."""
    context = RequestContext(
        request_id="req-partial-sensor-data",
        user_query="Check machine health",
    )
    context.tool_results.extend([
        ToolResult(
            tool_name="machine_lookup",
            success=True,
            data=[
                {
                    "MachineID": 1,
                    "Name": "Machine 1",
                    "Status": "operational",
                }
            ],
        ),
        ToolResult(
            tool_name="vibration_analysis",
            success=True,
            data=[],
        ),
    ])

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "INSUFFICIENT_DATA"


def test_critical_finding_references_supporting_evidence():
    context = RequestContext(
        request_id="req-traceability",
        user_query="Investigate machine breakdown",
    )

    context.tool_results.append(
        ToolResult(
            tool_name="machine_lookup",
            success=True,
            data=[
                {
                    "MachineID": 8,
                    "Name": "Machine Whe-40",
                    "Status": "breakdown",
                }
            ],
        )
    )

    context.evidence.append(
        Evidence(
            source_id="MES:Machines",
            content="Machine Whe-40 has status breakdown",
            metadata={"source_type": "sql"},
        )
    )

    result = DecisionEngine().evaluate(context)

    assert result["overall_status"] == "CRITICAL"
    assert "findings" in result

    breakdown_finding = next(
        finding
        for finding in result["findings"]
        if "breakdown" in finding["finding"].lower()
    )

    assert breakdown_finding["severity"] == "CRITICAL"
    assert "MES:Machines" in breakdown_finding["source_ids"]

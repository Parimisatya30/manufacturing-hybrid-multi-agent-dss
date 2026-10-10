
"""Tests for the bounded ReAct investigation agent."""

import pytest

from app.agents.react_agent import (
    InvestigationAction,
    ReActAgent,
)
from app.context.models import RequestContext


@pytest.fixture
def context():
    return RequestContext(
        request_id="react-test-1",
        user_query="Investigate machine maintenance risk",
    )


def test_executes_allowlisted_action_and_records_result(context):
    action = InvestigationAction(
        name="inspect_machine",
        tool_name="machine_lookup",
        execute=lambda ctx: {"MachineID": 8, "Status": "breakdown"},
    )
    agent = ReActAgent(actions=[action], max_iterations=3)

    result = agent.run(context, ["inspect_machine"])

    assert result.iterations == 1
    assert result.actions_executed == ["inspect_machine"]
    assert result.stop_reason == "requested_actions_processed"
    assert context.tool_results[-1].success is True
    assert context.tool_results[-1].data["Status"] == "breakdown"


def test_rejects_unknown_action_without_execution(context):
    agent = ReActAgent(actions=[], max_iterations=3)

    result = agent.run(context, ["delete_machine"])

    assert result.actions_executed == []
    assert context.tool_results[-1].success is False
    assert context.tool_results[-1].error == "Action is not allowlisted"


def test_continues_after_action_exception(context):
    def failing_action(ctx):
        raise RuntimeError("Database unavailable")

    action = InvestigationAction(
        name="inspect_machine",
        tool_name="machine_lookup",
        execute=failing_action,
    )
    agent = ReActAgent(actions=[action])

    result = agent.run(context, ["inspect_machine"])

    assert result.actions_executed == []
    assert context.tool_results[-1].success is False
    assert context.tool_results[-1].error == "Database unavailable"


def test_enforces_maximum_iterations(context):
    action = InvestigationAction(
        name="inspect_machine",
        tool_name="machine_lookup",
        execute=lambda ctx: {"Status": "operational"},
    )
    agent = ReActAgent(actions=[action], max_iterations=2)

    result = agent.run(
        context,
        ["inspect_machine", "inspect_machine", "inspect_machine"],
    )

    assert result.iterations == 2
    assert len(result.actions_executed) == 2
    assert result.stop_reason == "max_iterations_reached"


def test_rejects_invalid_iteration_limit():
    with pytest.raises(ValueError):
        ReActAgent(max_iterations=0)

    with pytest.raises(TypeError):
        ReActAgent(max_iterations=True)


def test_rejects_duplicate_action_names():
    action = InvestigationAction(
        name="inspect_machine",
        tool_name="machine_lookup",
        execute=lambda ctx: {},
    )

    with pytest.raises(ValueError):
        ReActAgent(actions=[action, action])


def test_policy_stops_when_all_required_tools_succeed():
    from app.agents.react_agent import (
        InvestigationAction,
        MaintenanceInvestigationPolicy,
        ReActAgent,
    )
    from app.context.models import RequestContext, ToolResult

    context = RequestContext(
        request_id="test-sufficient",
        user_query="Investigate machine health",
        tool_results=[
            ToolResult(tool_name="machine_lookup", success=True, data={}),
            ToolResult(
                tool_name="predictive_maintenance",
                success=True,
                data=[],
            ),
            ToolResult(
                tool_name="vibration_analysis",
                success=True,
                data=[],
            ),
            ToolResult(tool_name="rag_search", success=True, data=[]),
        ],
    )

    agent = ReActAgent(
        actions=[
            InvestigationAction(
                name=tool_name,
                tool_name=tool_name,
                execute=lambda context: {},
            )
            for tool_name in (
                "machine_lookup",
                "predictive_maintenance",
                "vibration_analysis",
                "rag_search",
            )
        ]
    )

    result = agent.run_with_policy(context, MaintenanceInvestigationPolicy())

    assert result.iterations == 0
    assert result.stop_reason == "sufficient_evidence"
    assert result.actions_executed == []


def test_policy_reports_blocked_when_no_action_is_available():
    from app.agents.react_agent import ReActAgent
    from app.context.models import RequestContext

    context = RequestContext(
        request_id="test-blocked",
        user_query="Investigate machine health",
    )

    agent = ReActAgent(actions=[])

    result = agent.run_with_policy(context)

    assert result.iterations == 0
    assert result.stop_reason == "investigation_blocked"
    assert result.actions_executed == []


def test_policy_respects_iteration_limit():
    from app.agents.react_agent import InvestigationAction, ReActAgent
    from app.context.models import RequestContext

    context = RequestContext(
        request_id="test-limit",
        user_query="Investigate machine health",
    )

    agent = ReActAgent(
        actions=[
            InvestigationAction(
                name=tool_name,
                tool_name=tool_name,
                execute=lambda context: {"checked": True},
            )
            for tool_name in (
                "machine_lookup",
                "predictive_maintenance",
                "vibration_analysis",
                "rag_search",
            )
        ],
        max_iterations=2,
    )

    result = agent.run_with_policy(context)

    assert result.iterations == 2
    assert result.stop_reason == "max_iterations_reached"
    assert result.actions_executed == [
        "machine_lookup",
        "predictive_maintenance",
    ]


from unittest.mock import Mock

import pytest

from app.agents.react_agent import InvestigationResult
from app.router.dispatcher import RequestDispatcher
from app.router.task_router import ExecutionPath, RoutingDecision, TaskRouter


@pytest.fixture
def router():
    mock_router = Mock(spec=TaskRouter)
    return mock_router


@pytest.fixture
def dispatcher(router):
    return RequestDispatcher(router=router)


def configure_route(router, path, intent="test_intent"):
    router.route.return_value = RoutingDecision(
        intent=intent,
        execution_path=path,
        reason="Test routing decision",
    )


def test_dispatch_executes_approved_sql_operation(router):
    configure_route(router, ExecutionPath.DIRECT_SQL)
    sql_operation = Mock(return_value=[{"MachineID": 8}])

    dispatcher = RequestDispatcher(
        router=router,
        sql_operations={"get_machine_details": sql_operation},
    )

    result = dispatcher.dispatch("Show machine 8 details")

    sql_operation.assert_called_once_with(machine_id=8)
    assert result["execution_path"] == "direct_sql"
    assert result["result"] == [{"MachineID": 8}]


def test_dispatch_calls_rag_tool(router):
    configure_route(router, ExecutionPath.DIRECT_RAG)
    rag_tool = Mock()
    rag_tool.search.return_value = ["retrieved passage"]

    dispatcher = RequestDispatcher(router=router, rag_tool=rag_tool)
    result = dispatcher.dispatch("What causes excessive vibration?")

    rag_tool.search.assert_called_once_with(
        "What causes excessive vibration?",
        top_k=3,
    )
    assert result["result"] == ["retrieved passage"]


def test_dispatch_calls_maintenance_workflow(router):
    configure_route(router, ExecutionPath.WORKFLOW)
    workflow = Mock()
    workflow.run.return_value = {"overall_status": "WARNING"}

    dispatcher = RequestDispatcher(
        router=router,
        maintenance_workflow=workflow,
    )
    result = dispatcher.dispatch(
        "Assess maintenance risk for machine 8",
        machine_id=8,
        request_id="test-8",
    )

    workflow.run.assert_called_once_with(
        machine_id=8,
        user_query="Assess maintenance risk for machine 8",
        request_id="test-8",
    )
    assert result["result"]["overall_status"] == "WARNING"


def test_dispatch_requires_machine_id_for_workflow(router):
    configure_route(router, ExecutionPath.WORKFLOW)
    workflow = Mock()

    dispatcher = RequestDispatcher(
        router=router,
        maintenance_workflow=workflow,
    )

    with pytest.raises(ValueError, match="machine_id is required"):
        dispatcher.dispatch("Assess maintenance risk")

    workflow.run.assert_not_called()


def test_dispatch_rejects_unapproved_sql_operation(router):
    configure_route(router, ExecutionPath.DIRECT_SQL)
    dispatcher = RequestDispatcher(router=router)

    with pytest.raises(ValueError, match="No approved SQL operation"):
        dispatcher.dispatch("Show machine 8 details")


def test_dispatch_calls_react_agent(router):
    configure_route(router, ExecutionPath.REACT)
    react_agent = Mock()
    react_agent.run_with_policy.return_value = InvestigationResult(
        request_id="test-react",
        iterations=1,
        stop_reason="sufficient_evidence",
        actions_executed=["machine_lookup"],
    )

    dispatcher = RequestDispatcher(
        router=router,
        react_agent=react_agent,
    )
    result = dispatcher.dispatch(
        "Investigate why machine 8 broke down",
        request_id="test-react",
    )

    react_agent.run_with_policy.assert_called_once()
    context = react_agent.run_with_policy.call_args.args[0]
    assert context.request_id == "test-react"
    assert context.user_query == "Investigate why machine 8 broke down"
    assert result["execution_path"] == "react"
    assert result["result"].stop_reason == "sufficient_evidence"


def test_dispatch_reports_missing_rag_configuration(router):
    configure_route(router, ExecutionPath.DIRECT_RAG)
    dispatcher = RequestDispatcher(router=router)

    with pytest.raises(RuntimeError, match="RAG tool is not configured"):
        dispatcher.dispatch("What causes excessive vibration?")



def test_dispatch_rejects_machine_details_query_without_machine_id(router):
    configure_route(router, ExecutionPath.DIRECT_SQL)
    sql_operation = Mock()

    dispatcher = RequestDispatcher(
        router=router,
        sql_operations={"get_machine_details": sql_operation},
    )

    with pytest.raises(ValueError, match="machine ID is required"):
        dispatcher.dispatch("Show machine details")

    sql_operation.assert_not_called()


def test_dispatch_rejects_non_positive_machine_id(router):
    configure_route(router, ExecutionPath.DIRECT_SQL)
    sql_operation = Mock()

    dispatcher = RequestDispatcher(
        router=router,
        sql_operations={"get_machine_details": sql_operation},
    )

    with pytest.raises(ValueError, match="machine_id must be positive"):
        dispatcher.dispatch("Show machine 0 details")

    sql_operation.assert_not_called()

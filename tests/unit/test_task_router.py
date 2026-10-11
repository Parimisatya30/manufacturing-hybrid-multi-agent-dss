
import pytest

from app.router.task_router import ExecutionPath, TaskRouter


@pytest.fixture
def router():
    return TaskRouter()


def test_routes_root_cause_investigation_to_rca_workflow(router):
    result = router.route(
        "Investigate why machine 8 broke down and identify possible causes"
    )

    assert result.execution_path == ExecutionPath.RCA_WORKFLOW
    assert result.intent == "root_cause_analysis"


def test_routes_unmatched_complex_request_to_react(router):
    result = router.route(
        "Correlate production delays with supplier delivery issues"
    )

    assert result.execution_path == ExecutionPath.REACT


def test_routes_simple_database_query_to_sql(router):
    result = router.route("Show machine 8 details")

    assert result.execution_path == ExecutionPath.DIRECT_SQL
    assert result.intent == "database_query"


def test_routes_manufacturing_knowledge_to_rag(router):
    result = router.route("What causes excessive vibration?")

    assert result.execution_path == ExecutionPath.DIRECT_RAG
    assert result.intent == "manufacturing_knowledge"


def test_routes_known_maintenance_assessment_to_workflow(router):
    result = router.route("Assess maintenance risk for machine 8")

    assert result.execution_path == ExecutionPath.WORKFLOW
    assert result.intent == "maintenance_assessment"


def test_routes_unknown_request_to_react_fallback(router):
    result = router.route("Help me understand this manufacturing issue")

    assert result.execution_path == ExecutionPath.REACT
    assert result.intent == "unknown"


def test_routes_defect_rate_to_defect_workflow(router):
    result = router.route("Show the defect rate")

    assert result.execution_path == ExecutionPath.DEFECT_WORKFLOW
    assert result.intent == "defect_monitoring"


@pytest.mark.parametrize("query", ["", " ", "\t\n"])
def test_router_rejects_blank_queries(router, query):
    with pytest.raises(ValueError, match="must not be blank"):
        router.route(query)

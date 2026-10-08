from app.context.manager import (
    ContextManager,
    create_request_context,
)
from app.context.models import Evidence, ToolResult


def test_create_request_context() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    assert context.request_id == "REQ-001"
    assert context.user_query == "Show machine downtime"
    assert context.semantic_entities == []
    assert context.semantic_attributes == []
    assert context.tool_results == []
    assert context.evidence == []
    assert context.conversation == []


def test_add_conversation_turn() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    manager.add_conversation_turn(
        role="user",
        content="Show machine downtime",
    )

    manager.add_conversation_turn(
        role="assistant",
        content="I will investigate machine downtime.",
    )

    assert len(context.conversation) == 2
    assert context.conversation[0].role == "user"
    assert context.conversation[1].role == "assistant"


def test_add_semantic_entity_without_duplicates() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    manager.add_semantic_entity("Machine")
    manager.add_semantic_entity("Machine")

    assert context.semantic_entities == ["Machine"]


def test_add_semantic_attribute_without_duplicates() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine efficiency",
    )

    manager = ContextManager(context)

    manager.add_semantic_attribute("EfficiencyFactor")
    manager.add_semantic_attribute("EfficiencyFactor")

    assert context.semantic_attributes == [
        "EfficiencyFactor"
    ]


def test_add_tool_result() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    result = ToolResult(
        tool_name="sql_tool",
        success=True,
        data=[
            {
                "MachineID": "M001",
                "Downtime": 12,
            }
        ],
    )

    manager.add_tool_result(result)

    assert len(context.tool_results) == 1
    assert context.tool_results[0].tool_name == "sql_tool"
    assert context.tool_results[0].success is True


def test_add_evidence() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    evidence = Evidence(
        source_id="MES_SCHEMA",
        content="Downtime is stored in the Downtimes table.",
    )

    manager.add_evidence(evidence)

    assert len(context.evidence) == 1
    assert context.evidence[0].source_id == "MES_SCHEMA"


def test_metadata() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    manager.set_metadata(
        "intent",
        "downtime_analysis",
    )

    assert manager.get_metadata("intent") == "downtime_analysis"
    assert manager.get_metadata("missing") is None
    assert manager.get_metadata("missing", "default") == "default"


def test_clear_context() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Show machine downtime",
    )

    manager = ContextManager(context)

    manager.add_semantic_entity("Machine")
    manager.add_semantic_attribute("Downtime")
    manager.add_conversation_turn(
        "user",
        "Show downtime",
    )

    manager.set_metadata(
        "intent",
        "downtime_analysis",
    )

    manager.clear()

    assert context.semantic_entities == []
    assert context.semantic_attributes == []
    assert context.conversation == []
    assert context.metadata == {}
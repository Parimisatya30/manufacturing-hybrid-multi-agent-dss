from app.context.manager import create_request_context
from app.context.models import Evidence
from app.memory.manager import MemoryManager
from app.memory.short_term import ShortTermMemory


def test_remember_investigation() -> None:
    context = create_request_context(
        request_id="REQ-001",
        user_query="Why did Machine M001 have repeated downtime?",
    )

    context.semantic_entities.extend(
        ["Machine", "M001", "Downtime"]
    )

    context.semantic_attributes.extend(
        ["Duration", "Reason"]
    )

    context.evidence.append(
        Evidence(
            source_id="MES_SCHEMA",
            content="Machine and downtime schema information.",
        )
    )

    memory_store = ShortTermMemory(
        session_id="SESSION-001"
    )

    manager = MemoryManager(memory_store)

    memory = manager.remember_investigation(
        context=context,
        summary="Machine M001 experienced repeated downtime.",
    )

    assert memory.session_id == "SESSION-001"
    assert memory.memory_type == "investigation"

    assert memory.summary == (
        "Machine M001 experienced repeated downtime."
    )

    assert memory.entities == [
        "Machine",
        "M001",
        "Downtime",
    ]

    assert memory.attributes == [
        "Duration",
        "Reason",
    ]

    assert memory.evidence_refs == [
        "MES_SCHEMA",
    ]

    assert memory.metadata["request_id"] == "REQ-001"

    assert manager.get_memory(memory.memory_id) == memory


def test_evidence_references_are_deduplicated() -> None:
    context = create_request_context(
        request_id="REQ-002",
        user_query="Investigate Machine M002.",
    )

    context.evidence.extend(
        [
            Evidence(
                source_id="MES_SCHEMA",
                content="Schema evidence.",
            ),
            Evidence(
                source_id="MES_SCHEMA",
                content="Another schema reference.",
            ),
            Evidence(
                source_id="REQ-002",
                content="Request evidence.",
            ),
        ]
    )

    memory_store = ShortTermMemory(
        session_id="SESSION-001"
    )

    manager = MemoryManager(memory_store)

    memory = manager.remember_investigation(
        context=context,
        summary="Machine M002 investigation started.",
    )

    assert memory.evidence_refs == [
        "MES_SCHEMA",
        "REQ-002",
    ]


def test_list_memories() -> None:
    context = create_request_context(
        request_id="REQ-003",
        user_query="Investigate downtime.",
    )

    memory_store = ShortTermMemory(
        session_id="SESSION-001"
    )

    manager = MemoryManager(memory_store)

    manager.remember_investigation(
        context=context,
        summary="First investigation.",
    )

    manager.remember_investigation(
        context=context,
        summary="Second investigation.",
    )

    memories = manager.list_memories()

    assert len(memories) == 2


def test_list_memories_by_type() -> None:
    context = create_request_context(
        request_id="REQ-004",
        user_query="Investigate downtime.",
    )

    memory_store = ShortTermMemory(
        session_id="SESSION-001"
    )

    manager = MemoryManager(memory_store)

    manager.remember_investigation(
        context=context,
        summary="Investigation memory.",
    )

    memories = manager.list_memories_by_type(
        "investigation"
    )

    assert len(memories) == 1
    assert memories[0].memory_type == "investigation"


def test_clear_memories() -> None:
    context = create_request_context(
        request_id="REQ-005",
        user_query="Investigate downtime.",
    )

    memory_store = ShortTermMemory(
        session_id="SESSION-001"
    )

    manager = MemoryManager(memory_store)

    manager.remember_investigation(
        context=context,
        summary="Investigation memory.",
    )

    assert len(manager.list_memories()) == 1

    manager.clear()

    assert manager.list_memories() == []
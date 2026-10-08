import pytest

from app.memory.models import create_memory
from app.memory.short_term import ShortTermMemory


def test_add_and_get_memory() -> None:
    memory_store = ShortTermMemory("SESSION-001")

    memory = create_memory(
        memory_id="MEM-001",
        session_id="SESSION-001",
        memory_type="investigation",
        summary="Machine M001 experienced downtime.",
        entities=["Machine", "M001"],
    )

    memory_store.add(memory)

    result = memory_store.get("MEM-001")

    assert result is not None
    assert result.memory_id == "MEM-001"
    assert result.summary == (
        "Machine M001 experienced downtime."
    )


def test_list_memories() -> None:
    memory_store = ShortTermMemory("SESSION-001")

    memory_store.add(
        create_memory(
            memory_id="MEM-001",
            session_id="SESSION-001",
            memory_type="investigation",
            summary="Investigation one.",
        )
    )

    memory_store.add(
        create_memory(
            memory_id="MEM-002",
            session_id="SESSION-001",
            memory_type="decision",
            summary="Decision one.",
        )
    )

    memories = memory_store.list()

    assert len(memories) == 2


def test_list_by_type() -> None:
    memory_store = ShortTermMemory("SESSION-001")

    memory_store.add(
        create_memory(
            memory_id="MEM-001",
            session_id="SESSION-001",
            memory_type="investigation",
            summary="Investigation one.",
        )
    )

    memory_store.add(
        create_memory(
            memory_id="MEM-002",
            session_id="SESSION-001",
            memory_type="decision",
            summary="Decision one.",
        )
    )

    investigations = memory_store.list_by_type(
        "investigation"
    )

    assert len(investigations) == 1
    assert investigations[0].memory_id == "MEM-001"


def test_reject_memory_from_different_session() -> None:
    memory_store = ShortTermMemory("SESSION-001")

    memory = create_memory(
        memory_id="MEM-001",
        session_id="SESSION-002",
        memory_type="investigation",
        summary="Wrong session.",
    )

    with pytest.raises(ValueError):
        memory_store.add(memory)


def test_clear_memory() -> None:
    memory_store = ShortTermMemory("SESSION-001")

    memory_store.add(
        create_memory(
            memory_id="MEM-001",
            session_id="SESSION-001",
            memory_type="investigation",
            summary="Investigation.",
        )
    )

    assert len(memory_store) == 1

    memory_store.clear()

    assert len(memory_store) == 0
    assert memory_store.list() == []
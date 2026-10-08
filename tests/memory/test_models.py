from app.memory.models import Memory, create_memory


def test_create_memory() -> None:
    memory = create_memory(
        memory_id="MEM-001",
        session_id="SESSION-001",
        memory_type="investigation",
        summary="Machine M001 experienced repeated downtime.",
        entities=["Machine", "M001", "Downtime"],
        attributes=["Duration", "Reason"],
        evidence_refs=["MES_SCHEMA", "REQ-001"],
    )

    assert memory.memory_id == "MEM-001"
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
        "REQ-001",
    ]


def test_memory_defaults() -> None:
    memory = Memory(
        memory_id="MEM-002",
        session_id="SESSION-001",
        memory_type="decision",
        summary="Maintenance inspection recommended.",
    )

    assert memory.memory_id == "MEM-002"
    assert memory.session_id == "SESSION-001"
    assert memory.memory_type == "decision"
    assert memory.summary == (
        "Maintenance inspection recommended."
    )

    assert memory.entities == []
    assert memory.attributes == []
    assert memory.evidence_refs == []
    assert memory.metadata == {}
    assert memory.created_at is not None


def test_memory_metadata() -> None:
    memory = create_memory(
        memory_id="MEM-003",
        session_id="SESSION-001",
        memory_type="investigation",
        summary="Machine investigation completed.",
        metadata={
            "request_id": "REQ-001",
            "confidence": 0.92,
        },
    )

    assert memory.memory_id == "MEM-003"
    assert memory.session_id == "SESSION-001"
    assert memory.memory_type == "investigation"

    assert memory.metadata["request_id"] == "REQ-001"
    assert memory.metadata["confidence"] == 0.92
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Memory:
    """
    Short-term semantic memory retained within a session.

    This memory is not persistent. It is intended to help the
    system maintain continuity across multiple turns of the
    same investigation/session.
    """

    memory_id: str
    session_id: str
    memory_type: str
    summary: str

    entities: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)

    evidence_refs: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


def create_memory(
    memory_id: str,
    session_id: str,
    memory_type: str,
    summary: str,
    entities: list[str] | None = None,
    attributes: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Memory:
    """Create a short-term semantic memory record."""

    return Memory(
        memory_id=memory_id,
        session_id=session_id,
        memory_type=memory_type,
        summary=summary,
        entities=entities or [],
        attributes=attributes or [],
        evidence_refs=evidence_refs or [],
        metadata=metadata or {},
    )
from __future__ import annotations

from uuid import uuid4

from app.context.models import RequestContext
from app.memory.models import Memory, create_memory
from app.memory.short_term import ShortTermMemory
from app.observability.logging import get_logger
from app.observability.metrics import metrics


logger = get_logger(__name__)


class MemoryManager:
    """
    Manages semantic short-term memory for a session.

    The MemoryManager selectively extracts useful information from
    RequestContext and stores it in ShortTermMemory.

    It does not persist memory beyond the lifetime of the
    ShortTermMemory instance.
    """

    def __init__(self, short_term_memory: ShortTermMemory) -> None:
        self._memory = short_term_memory

    @property
    def session_id(self) -> str:
        """Return the session associated with this memory manager."""
        return self._memory.session_id

    def remember_investigation(
        self,
        context: RequestContext,
        summary: str,
    ) -> Memory:
        """
        Extract useful semantic information from a request context
        and store it as an investigation memory.
        """

        evidence_refs = list(
            dict.fromkeys(
                evidence.source_id
                for evidence in context.evidence
            )
        )

        metadata = {
            "request_id": context.request_id,
        }

        memory = create_memory(
            memory_id=f"MEM-{uuid4()}",
            session_id=self.session_id,
            memory_type="investigation",
            summary=summary,
            entities=list(context.semantic_entities),
            attributes=list(context.semantic_attributes),
            evidence_refs=evidence_refs,
            metadata=metadata,
        )

        self._memory.add(memory)

        metrics.increment("memory_manager_investigations_total")

        logger.info(
            "Investigation memory created",
            extra={
                "session_id": self.session_id,
                "request_id": context.request_id,
                "memory_id": memory.memory_id,
            },
        )

        return memory

    def get_memory(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID."""
        return self._memory.get(memory_id)

    def list_memories(self) -> list[Memory]:
        """Return all memories for the current session."""
        return self._memory.list()

    def list_memories_by_type(
        self,
        memory_type: str,
    ) -> list[Memory]:
        """Return memories matching a memory type."""
        return self._memory.list_by_type(memory_type)

    def clear(self) -> None:
        """Clear all short-term memories for the current session."""
        self._memory.clear()

        metrics.increment("memory_manager_cleared_total")

        logger.info(
            "Session memories cleared",
            extra={"session_id": self.session_id},
        )
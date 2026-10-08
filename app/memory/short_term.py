from __future__ import annotations

from app.memory.models import Memory
from app.observability.logging import get_logger
from app.observability.metrics import metrics


logger = get_logger(__name__)


class ShortTermMemory:
    """
    In-memory store for session-scoped semantic memories.

    Data is intentionally not persisted to disk or a database.
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._memories: list[Memory] = []

        metrics.increment("short_term_memory_sessions_total")

        logger.debug(
            "Short-term memory initialized",
            extra={
                "session_id": session_id,
            },
        )

    @property
    def session_id(self) -> str:
        """Return the current session identifier."""
        return self._session_id

    def add(self, memory: Memory) -> None:
        """Add a memory to the current session."""

        if memory.session_id != self._session_id:
            raise ValueError(
                "Memory session_id does not match "
                "the current session."
            )

        self._memories.append(memory)

        metrics.increment("short_term_memory_added_total")

        logger.debug(
            "Short-term memory added",
            extra={
                "session_id": self._session_id,
                "memory_id": memory.memory_id,
                "memory_type": memory.memory_type,
            },
        )

    def get(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID."""

        for memory in self._memories:
            if memory.memory_id == memory_id:
                return memory

        return None

    def list(self) -> list[Memory]:
        """Return all memories for the current session."""

        return list(self._memories)

    def list_by_type(
        self,
        memory_type: str,
    ) -> list[Memory]:
        """Return memories matching a memory type."""

        return [
            memory
            for memory in self._memories
            if memory.memory_type == memory_type
        ]

    def clear(self) -> None:
        """Clear all memories for the current session."""

        count = len(self._memories)

        self._memories.clear()

        metrics.increment(
            "short_term_memory_cleared_total"
        )

        logger.debug(
            "Short-term memory cleared",
            extra={
                "session_id": self._session_id,
                "memory_count": count,
            },
        )

    def __len__(self) -> int:
        """Return the number of memories in the session."""

        return len(self._memories)
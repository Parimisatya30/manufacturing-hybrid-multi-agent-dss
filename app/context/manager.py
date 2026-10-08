from __future__ import annotations

from app.context.models import (
    ConversationTurn,
    Evidence,
    RequestContext,
    ToolResult,
)
from app.observability.logging import get_logger
from app.observability.metrics import metrics


logger = get_logger(__name__)


class ContextManager:
    """
    Manages request-scoped context for a single investigation.

    The ContextManager is intentionally domain-agnostic.
    It stores information produced by other components without
    deciding how that information was generated.
    """

    def __init__(self, context: RequestContext) -> None:
        self._context = context

    @property
    def context(self) -> RequestContext:
        """Return the current request context."""
        return self._context

    def add_conversation_turn(
        self,
        role: str,
        content: str,
    ) -> None:
        """Add a user or assistant conversation turn."""

        self._context.conversation.append(
            ConversationTurn(
                role=role,
                content=content,
            )
        )

        metrics.increment("context_conversation_turns_total")

        logger.debug(
            "Conversation turn added",
            extra={
                "request_id": self._context.request_id,
                "role": role,
            },
        )

    def add_semantic_entity(self, entity: str) -> None:
        """Add a resolved semantic entity if it is not already present."""

        if entity not in self._context.semantic_entities:
            self._context.semantic_entities.append(entity)

            metrics.increment(
                "context_semantic_entities_total"
            )

    def add_semantic_attribute(self, attribute: str) -> None:
        """Add a resolved semantic attribute if it is not already present."""

        if attribute not in self._context.semantic_attributes:
            self._context.semantic_attributes.append(attribute)

            metrics.increment(
                "context_semantic_attributes_total"
            )

    def add_tool_result(
        self,
        result: ToolResult,
    ) -> None:
        """Add a tool execution result to the context."""

        self._context.tool_results.append(result)

        metrics.increment("context_tool_results_total")

        logger.debug(
            "Tool result added",
            extra={
                "request_id": self._context.request_id,
                "tool_name": result.tool_name,
                "success": result.success,
            },
        )

    def add_evidence(
        self,
        evidence: Evidence,
    ) -> None:
        """Add evidence supporting the current investigation."""

        self._context.evidence.append(evidence)

        metrics.increment("context_evidence_total")

        logger.debug(
            "Evidence added",
            extra={
                "request_id": self._context.request_id,
                "source_id": evidence.source_id,
            },
        )

    def set_metadata(
        self,
        key: str,
        value: object,
    ) -> None:
        """Store request-scoped metadata."""

        self._context.metadata[key] = value

        metrics.increment("context_metadata_updates_total")

    def get_metadata(
        self,
        key: str,
        default: object = None,
    ) -> object:
        """Retrieve request-scoped metadata."""

        return self._context.metadata.get(
            key,
            default,
        )

    def clear(self) -> None:
        """Clear accumulated request context."""

        self._context.semantic_entities.clear()
        self._context.semantic_attributes.clear()
        self._context.tool_results.clear()
        self._context.evidence.clear()
        self._context.conversation.clear()
        self._context.metadata.clear()

        metrics.increment("context_cleared_total")

        logger.debug(
            "Request context cleared",
            extra={
                "request_id": self._context.request_id,
            },
        )


def create_request_context(
    request_id: str,
    user_query: str,
) -> RequestContext:
    """
    Create a new request-scoped context.

    This factory keeps context construction in one place and
    makes future changes to RequestContext easier to manage.
    """

    metrics.increment("contexts_created_total")

    logger.debug(
        "Request context created",
        extra={
            "request_id": request_id,
        },
    )

    return RequestContext(
        request_id=request_id,
        user_query=user_query,
    )
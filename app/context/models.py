from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result returned by a tool execution."""

    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class Evidence:
    """Evidence that supports a decision or response."""

    source_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """A single user/assistant conversation turn."""

    role: str
    content: str


@dataclass
class RequestContext:
    """Context accumulated during the lifetime of a single request."""

    request_id: str
    user_query: str
    semantic_entities: list[str] = field(default_factory=list)
    semantic_attributes: list[str] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    conversation: list[ConversationTurn] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
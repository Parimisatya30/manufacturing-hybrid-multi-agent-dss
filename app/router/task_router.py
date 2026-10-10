
"""Deterministic intent and task routing for the manufacturing DSS."""

from dataclasses import dataclass
from enum import Enum


class ExecutionPath(str, Enum):
    """Supported execution paths for incoming requests."""

    DIRECT_SQL = "direct_sql"
    DIRECT_RAG = "direct_rag"
    WORKFLOW = "workflow"
    REACT = "react"


@dataclass(frozen=True)
class RoutingDecision:
    """The routing outcome for a user request."""

    intent: str
    execution_path: ExecutionPath
    reason: str


class TaskRouter:
    """Route requests using simple, deterministic rules."""

    def route(self, user_query: str) -> RoutingDecision:
        """Classify a request without executing any tools."""
        if not user_query or not user_query.strip():
            raise ValueError("user_query must not be blank")

        query = user_query.strip().lower()

        complex_indicators = (
            "investigate",
            "root cause",
            "why did",
            "why is",
            "identify possible causes",
            "correlate",
        )

        workflow_indicators = (
            "assess maintenance",
            "maintenance risk",
            "predictive maintenance assessment",
        )

        sql_indicators = (
            "show machine",
            "list machines",
            "machine details",
            "work orders",
            "production count",
            "oee",
        )

        knowledge_indicators = (
            "what causes",
            "explain",
            "how does",
            "maintenance procedure",
            "troubleshooting",
            "vibration",
            "defect",
        )

        if any(term in query for term in complex_indicators):
            return RoutingDecision(
                intent="complex_investigation",
                execution_path=ExecutionPath.REACT,
                reason="The request indicates multi-step investigation.",
            )

        if any(term in query for term in workflow_indicators):
            return RoutingDecision(
                intent="maintenance_assessment",
                execution_path=ExecutionPath.WORKFLOW,
                reason="The request matches a predefined maintenance workflow.",
            )

        if any(term in query for term in sql_indicators):
            return RoutingDecision(
                intent="database_query",
                execution_path=ExecutionPath.DIRECT_SQL,
                reason="The request appears to ask for structured manufacturing data.",
            )

        if any(term in query for term in knowledge_indicators):
            return RoutingDecision(
                intent="manufacturing_knowledge",
                execution_path=ExecutionPath.DIRECT_RAG,
                reason="The request appears to ask for manufacturing knowledge.",
            )

        return RoutingDecision(
            intent="unknown",
            execution_path=ExecutionPath.REACT,
            reason="No specific rule matched; use bounded investigation as the fallback.",
        )

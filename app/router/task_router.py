
"""Deterministic intent and task routing for the manufacturing DSS."""

from dataclasses import dataclass
from enum import Enum



class ExecutionPath(str, Enum):
    """Supported execution paths for incoming requests."""

    DIRECT_SQL = "direct_sql"
    DIRECT_RAG = "direct_rag"
    WORKFLOW = "workflow"
    RCA_WORKFLOW = "rca_workflow"
    DEFECT_WORKFLOW = "defect_workflow"
    REACT = "react"

@dataclass(frozen=True)
class RoutingDecision:
    """The routing outcome for a user request."""

    intent: str
    execution_path: ExecutionPath
    reason: str

class TaskRouter:
    """Route requests using deterministic rules."""

    def route(self, user_query: str) -> RoutingDecision:
        if not user_query or not user_query.strip():
            raise ValueError("user_query must not be blank")

        query = user_query.strip().lower()

        # 1. Predictive maintenance: use the existing workflow.

        maintenance_indicators = (
            "assess maintenance",
            "maintenance risk",
            "predictive maintenance assessment",
        )

        if any(term in query for term in maintenance_indicators):
            return RoutingDecision(
                intent="maintenance_assessment",
                execution_path=ExecutionPath.WORKFLOW,
                reason="The request matches the predictive maintenance workflow.",
            )

        # 2. RCA: investigate causes of a manufacturing problem.
        rca_indicators = (
            "root cause",
            "investigate",
            "why did",
            "why is",
            "identify possible causes",
            "corrective action",
            "preventive action",
        )
        if any(term in query for term in rca_indicators):
            return RoutingDecision(
                intent="root_cause_analysis",
                execution_path=ExecutionPath.RCA_WORKFLOW,
                reason="The request requires root-cause investigation.",
            )

        # 3. Defect monitoring: inspect rates, trends, and defect breakdowns.
        defect_indicators = (
            "defect rate",
            "defect monitoring",
            "defect trend",
            "defect trends",
            "common defects",
            "top defects",
            "defect breakdown",
            "quality failure rate",
        )
        if any(term in query for term in defect_indicators):
            return RoutingDecision(
                intent="defect_monitoring",
                execution_path=ExecutionPath.DEFECT_WORKFLOW,
                reason="The request matches the defect monitoring workflow.",
            )

        # 4. Simple structured database queries.
        sql_indicators = (
            "show machine",
            "list machines",
            "machine details",
            "work orders",
            "production count",
            "oee",
        )
        if any(term in query for term in sql_indicators):
            return RoutingDecision(
                intent="database_query",
                execution_path=ExecutionPath.DIRECT_SQL,
                reason="The request asks for structured manufacturing data.",
            )

        # 5. Manufacturing knowledge retrieval.
        knowledge_indicators = (
            "what causes",
            "explain",
            "how does",
            "maintenance procedure",
            "troubleshooting",
            "vibration",
            "defect",
        )
        if any(term in query for term in knowledge_indicators):
            return RoutingDecision(
                intent="manufacturing_knowledge",
                execution_path=ExecutionPath.DIRECT_RAG,
                reason="The request asks for manufacturing knowledge.",
            )

        # 6. Fallback for requests without a specific match.
        return RoutingDecision(
            intent="unknown",
            execution_path=ExecutionPath.REACT,
            reason="No specific rule matched; use bounded investigation as the fallback.",
        )

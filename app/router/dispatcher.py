
"""Dispatch routed manufacturing DSS requests to approved components."""

import re
from collections.abc import Callable
from typing import Any

from app.agents.react_agent import ReActAgent
from app.context.manager import create_request_context
from app.router.task_router import ExecutionPath, TaskRouter


class RequestDispatcher:
    """Route requests to approved manufacturing DSS execution components."""

    def __init__(
        self,
        router: TaskRouter,
        sql_operations: dict[str, Callable[..., Any]] | None = None,
        rag_tool: Any | None = None,
        maintenance_workflow: Any | None = None,
        react_agent: ReActAgent | None = None,
        rca_workflow: Any | None = None,
        defect_workflow: Any | None = None,
    ) -> None:
        self.router = router
        self.sql_operations = sql_operations or {}
        self.rag_tool = rag_tool
        self.maintenance_workflow = maintenance_workflow
        self.react_agent = react_agent
        self.rca_workflow = rca_workflow
        self.defect_workflow = defect_workflow

    @staticmethod
    def _resolve_sql_operation(user_query: str) -> str:
        """Resolve a database request to an approved operation identifier."""
        query = user_query.strip().lower()

        if (
            "machine" in query
            and any(
                term in query
                for term in ("details", "information", "status")
            )
        ):
            return "get_machine_details"

        if "list machines" in query or "all machines" in query:
            return "list_machines"

        if "work orders" in query:
            return "get_work_orders"

        return "unsupported"

    @staticmethod
    def _extract_sql_parameters(
        user_query: str,
        operation_id: str,
    ) -> dict[str, Any]:
        """Extract and validate parameters for an approved SQL operation."""
        if operation_id == "get_machine_details":
            match = re.search(
                r"\bmachine\s+#?(\d+)\b",
                user_query,
                re.IGNORECASE,
            )

            if not match:
                raise ValueError(
                    "A machine ID is required for this SQL operation"
                )

            machine_id = int(match.group(1))

            if machine_id <= 0:
                raise ValueError("machine_id must be positive")

            return {"machine_id": machine_id}

        return {}

    def dispatch(
        self,
        user_query: str,
        machine_id: int | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Route a request and invoke its configured execution component."""
        if not user_query or not user_query.strip():
            raise ValueError("user_query must not be blank")

        decision = self.router.route(user_query)

        if decision.execution_path == ExecutionPath.DIRECT_SQL:
            operation_id = self._resolve_sql_operation(user_query)
            operation = self.sql_operations.get(operation_id)

            if operation is None:
                raise ValueError(
                    f"No approved SQL operation configured for: {operation_id}"
                )

            parameters = self._extract_sql_parameters(
                user_query,
                operation_id,
            )
            result = operation(**parameters)

        elif decision.execution_path == ExecutionPath.DIRECT_RAG:
            if self.rag_tool is None:
                raise RuntimeError("RAG tool is not configured")

            result = self.rag_tool.search(user_query, top_k=3)

        elif decision.execution_path == ExecutionPath.WORKFLOW:
            if self.maintenance_workflow is None:
                raise RuntimeError("Maintenance workflow is not configured")

            if machine_id is None:
                match = re.search(
                    r"\bmachine\s+#?(\d+)\b",
                    user_query,
                    re.IGNORECASE,
                )
                if match:
                    machine_id = int(match.group(1))

            if machine_id is None:
                raise ValueError(
                    "machine_id is required for maintenance workflow"
                )

            if machine_id <= 0:
                raise ValueError("machine_id must be positive")

            result = self.maintenance_workflow.run(
                machine_id=machine_id,
                user_query=user_query,
                request_id=request_id,
            )

        elif decision.execution_path == ExecutionPath.RCA_WORKFLOW:
            if self.rca_workflow is None:
                raise RuntimeError("RCA workflow is not configured")

            result = self.rca_workflow.run(
                user_query=user_query,
                request_id=request_id,
            )

        elif decision.execution_path == ExecutionPath.DEFECT_WORKFLOW:
            if self.defect_workflow is None:
                raise RuntimeError(
                    "Defect monitoring workflow is not configured"
                )

            result = self.defect_workflow.run(
                user_query=user_query,
                request_id=request_id,
            )

        elif decision.execution_path == ExecutionPath.REACT:
            if self.react_agent is None:
                raise RuntimeError("ReAct agent is not configured")

            context = create_request_context(
                request_id=request_id or "dispatch-request",
                user_query=user_query,
            )
            result = self.react_agent.run_with_policy(context)

        else:
            raise ValueError(
                f"Unsupported execution path: {decision.execution_path}"
            )

        return {
            "intent": decision.intent,
            "execution_path": decision.execution_path.value,
            "reason": decision.reason,
            "result": result,
        }
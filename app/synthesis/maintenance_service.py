"""Application service for maintenance investigation and response synthesis."""

from typing import Any

from app.synthesis.response_generator import ResponseGenerator
from app.workflows.maintenance_workflow import MaintenanceWorkflow


class MaintenanceService:
    """Run a maintenance investigation and synthesize its response."""

    def __init__(
        self,
        workflow: MaintenanceWorkflow,
        response_generator: ResponseGenerator | None = None,
    ) -> None:
        self.workflow = workflow
        self.response_generator = (
            response_generator or ResponseGenerator()
        )

    def investigate(
        self,
        machine_id: int,
        user_query: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Return both the original decision and its synthesized response."""
        decision = self.workflow.run(
            machine_id=machine_id,
            user_query=user_query,
            request_id=request_id,
        )

        response = self.response_generator.generate(decision)

        return {
            "decision": decision,
            "response": response,
        }
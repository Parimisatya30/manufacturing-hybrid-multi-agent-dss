
"""Bounded ReAct-style investigation agent."""

from dataclasses import dataclass, field
from typing import Any, Callable

from app.context.manager import ContextManager
from app.context.models import RequestContext, ToolResult


@dataclass(frozen=True)
class InvestigationAction:
    """A single approved investigation action."""

    name: str
    tool_name: str
    execute: Callable[[RequestContext], Any]


@dataclass
class InvestigationResult:
    """Outcome of a bounded investigation."""

    request_id: str
    iterations: int
    stop_reason: str
    actions_executed: list[str] = field(default_factory=list)


class MaintenanceInvestigationPolicy:
    """Select the next investigation action from missing tool results."""

    REQUIRED_ACTIONS = (
        ("machine_lookup", "machine_lookup"),
        ("predictive_maintenance", "predictive_maintenance"),
        ("vibration_analysis", "vibration_analysis"),
        ("rag_search", "rag_search"),
    )

    def select_next_action(
        self,
        context: RequestContext,
        available_action_names: list[str],
    ) -> str | None:
        """Return the next missing, available action or None."""
        attempted_tools = {
            result.tool_name
            for result in context.tool_results
        }
        available = set(available_action_names)

        for required_tool, action_name in self.REQUIRED_ACTIONS:
            if required_tool not in attempted_tools and action_name in available:
                return action_name

        return None

    def is_evidence_sufficient(self, context: RequestContext) -> bool:
        """Check whether every required tool completed successfully."""
        successful_tools = {
            result.tool_name
            for result in context.tool_results
            if result.success
        }
        return all(
            required_tool in successful_tools
            for required_tool, _ in self.REQUIRED_ACTIONS
        )

class ReActAgent:
    """Run approved investigation actions with a strict iteration limit."""

    def __init__(
        self,
        actions: list[InvestigationAction] | None = None,
        max_iterations: int = 3,
    ) -> None:
        if isinstance(max_iterations, bool) or not isinstance(
            max_iterations, int
        ):
            raise TypeError("max_iterations must be an integer")

        if max_iterations <= 0:
            raise ValueError("max_iterations must be positive")

        self.max_iterations = max_iterations
        self.actions = {action.name: action for action in (actions or [])}

        if len(self.actions) != len(actions or []):
            raise ValueError("Action names must be unique")

    def run_with_policy(
        self,
        context: RequestContext,
        policy: MaintenanceInvestigationPolicy | None = None,
    ) -> InvestigationResult:
        """Execute policy-selected actions within the configured limit."""
        policy = policy or MaintenanceInvestigationPolicy()
        actions_executed: list[str] = []
        iterations = 0

        while iterations < self.max_iterations:
            if policy.is_evidence_sufficient(context):
                return InvestigationResult(
                    request_id=context.request_id,
                    iterations=iterations,
                    stop_reason="sufficient_evidence",
                    actions_executed=actions_executed,
                )

            action_name = policy.select_next_action(
                context,
                list(self.actions.keys()),
            )

            if action_name is None:
                return InvestigationResult(
                    request_id=context.request_id,
                    iterations=iterations,
                    stop_reason="investigation_blocked",
                    actions_executed=actions_executed,
                )

            result = self.run(context, [action_name])
            iterations += result.iterations
            actions_executed.extend(result.actions_executed)

        if policy.is_evidence_sufficient(context):
            stop_reason = "sufficient_evidence"
        elif policy.select_next_action(
            context,
            list(self.actions.keys()),
        ) is not None:
            stop_reason = "max_iterations_reached"
        else:
            stop_reason = "investigation_blocked"

        return InvestigationResult(
            request_id=context.request_id,
            iterations=iterations,
            stop_reason=stop_reason,
            actions_executed=actions_executed,
        )

    def run(
        self,
        context: RequestContext,
        action_names: list[str],
    ) -> InvestigationResult:
        """Execute explicitly selected actions up to the configured limit."""
        context_manager = ContextManager(context)
        actions_executed: list[str] = []

        for action_name in action_names[: self.max_iterations]:
            action = self.actions.get(action_name)

            if action is None:
                context_manager.add_tool_result(
                    ToolResult(
                        tool_name=f"react:{action_name}",
                        success=False,
                        error="Action is not allowlisted",
                    )
                )
                continue

            try:
                output = action.execute(context)

                context_manager.add_tool_result(
                    ToolResult(
                        tool_name=action.tool_name,
                        success=True,
                        data=output,
                    )
                )
                actions_executed.append(action.name)

            except Exception as exc:
                context_manager.add_tool_result(
                    ToolResult(
                        tool_name=action.tool_name,
                        success=False,
                        error=str(exc),
                    )
                )

        if len(action_names) > self.max_iterations:
            stop_reason = "max_iterations_reached"
        elif not action_names:
            stop_reason = "no_actions_requested"
        else:
            stop_reason = "requested_actions_processed"

        return InvestigationResult(
            request_id=context.request_id,
            iterations=min(len(action_names), self.max_iterations),
            stop_reason=stop_reason,
            actions_executed=actions_executed,
        )

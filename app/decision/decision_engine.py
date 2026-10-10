
"""Decision engine for aggregating manufacturing tool results."""

from typing import Any

from app.context.models import RequestContext


class DecisionEngine:
    """Combine tool results, machine status, and evidence into a summary."""

    def evaluate(self, context: RequestContext) -> dict[str, Any]:
        """Build a deterministic summary from the current request context."""
        successful_results = [
            result for result in context.tool_results if result.success
        ]
        failed_results = [
            result for result in context.tool_results if not result.success
        ]

        statuses: list[str] = []
        for result in successful_results:
            statuses.extend(self._extract_statuses(result.data))

            # Operational state is authoritative for the machine lookup.
            if result.tool_name == "machine_lookup":
                statuses.extend(
                    self._extract_machine_statuses(result.data)
                )



        # Missing sensor readings mean machine health cannot be fully assessed.
        incomplete_health_data = any(
            result.tool_name in {"vibration_analysis", "sensor_data"}
            and (
                result.data is None
                or result.data == []
                or result.data == {}
            )
            for result in successful_results
        )

        if "CRITICAL" in statuses:
            overall_status = "CRITICAL"
        elif "WARNING" in statuses:
            overall_status = "WARNING"
        elif incomplete_health_data:
            overall_status = "INSUFFICIENT_DATA"
        elif not successful_results:
            overall_status = "INSUFFICIENT_DATA"
        elif all(
            result.data is None
            or result.data == []
            or result.data == {}
            for result in successful_results
        ):
            overall_status = "INSUFFICIENT_DATA"
        else:
            overall_status = "NORMAL"

        return {
            "request_id": context.request_id,
            "user_query": context.user_query,
            "overall_status": overall_status,
            "tool_results": len(context.tool_results),
            "successful_tools": len(successful_results),
            "failed_tools": len(failed_results),
            "evidence_count": len(context.evidence),
            "evidence": [
                {
                    "source_id": item.source_id,
                    "content": item.content,
                    "metadata": item.metadata,
                }
                for item in context.evidence
            ],
            "failed_tool_errors": [
                {
                    "tool_name": result.tool_name,
                    "error": result.error,
                }
                for result in failed_results
            ],
        }

    @staticmethod
    def _extract_statuses(data: Any) -> list[str]:
        """Extract known rule statuses from supported result structures."""
        if isinstance(data, dict):
            statuses = []
            status = data.get("status")
            if isinstance(status, str) and status in {
                "NORMAL",
                "WARNING",
                "CRITICAL",
            }:
                statuses.append(status)

            for value in data.values():
                if isinstance(value, (dict, list, tuple)):
                    statuses.extend(DecisionEngine._extract_statuses(value))

            return statuses

        if isinstance(data, (list, tuple)):
            statuses = []
            for item in data:
                statuses.extend(DecisionEngine._extract_statuses(item))
            return statuses

        return []

    @staticmethod
    def _extract_machine_statuses(data: Any) -> list[str]:
        """Map explicit machine operational states to decision severity."""
        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, (list, tuple)):
            rows = [row for row in data if isinstance(row, dict)]
        else:
            return []

        statuses = []

        for row in rows:
            value = row.get("Status", row.get("status"))
            if not isinstance(value, str):
                continue

            machine_status = value.strip().lower()

            if machine_status == "breakdown":
                statuses.append("CRITICAL")
            elif machine_status == "maintenance":
                statuses.append("WARNING")

        return statuses

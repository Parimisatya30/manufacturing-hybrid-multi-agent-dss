
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

            if result.tool_name == "machine_lookup":
                statuses.extend(
                    self._extract_machine_statuses(result.data)
                )

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
            "findings": self._build_findings(context),
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
    def _build_findings(
        context: RequestContext,
    ) -> list[dict[str, Any]]:
        """Build findings from machine states and rule evaluations."""
        findings: list[dict[str, Any]] = []

        for result in context.tool_results:
            if not result.success:
                continue

            if result.tool_name == "machine_lookup":
                findings.extend(
                    DecisionEngine._build_machine_findings(
                        result.data,
                        context,
                    )
                )

            elif result.tool_name.endswith("_rule"):
                findings.extend(
                    DecisionEngine._build_rule_findings(
                        result.data,
                        context,
                    )
                )

        return findings

    @staticmethod
    def _build_machine_findings(
        data: Any,
        context: RequestContext,
    ) -> list[dict[str, Any]]:
        """Build findings for explicit machine operational states."""
        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, (list, tuple)):
            rows = [row for row in data if isinstance(row, dict)]
        else:
            return []

        findings = []

        for row in rows:
            status_value = row.get("Status", row.get("status"))
            if not isinstance(status_value, str):
                continue

            machine_status = status_value.strip().lower()

            if machine_status == "breakdown":
                severity = "CRITICAL"
                finding_text = "Machine is in breakdown"
                reason = "Machine lookup reported breakdown status."
            elif machine_status == "maintenance":
                severity = "WARNING"
                finding_text = "Machine is under maintenance"
                reason = "Machine lookup reported maintenance status."
            else:
                continue

            machine_name = row.get("Name", row.get("name"))
            machine_id = row.get("MachineID", row.get("machine_id"))
            source_ids = []

            for evidence in context.evidence:
                content = evidence.content.lower()
                metadata = evidence.metadata

                content_matches = (
                    machine_status in content
                    and (
                        machine_name is None
                        or str(machine_name).lower() in content
                    )
                )

                evidence_rows = metadata.get("rows", [])
                metadata_matches = (
                    isinstance(evidence_rows, list)
                    and any(
                        isinstance(item, dict)
                        and str(
                            item.get("Status", item.get("status", ""))
                        ).strip().lower() == machine_status
                        and (
                            machine_id is None
                            or str(
                                item.get(
                                    "MachineID",
                                    item.get("machine_id", ""),
                                )
                            ) == str(machine_id)
                        )
                        and (
                            machine_name is None
                            or str(
                                item.get("Name", item.get("name", ""))
                            ).strip().lower()
                            == str(machine_name).strip().lower()
                        )
                        for item in evidence_rows
                    )
                )

                if content_matches or metadata_matches:
                    source_ids.append(evidence.source_id)

            findings.append(
                {
                    "finding": finding_text,
                    "severity": severity,
                    "source_ids": list(dict.fromkeys(source_ids)),
                    "reason": reason,
                }
            )

        return findings

    @staticmethod
    def _build_rule_findings(
        data: Any,
        context: RequestContext,
    ) -> list[dict[str, Any]]:
        """Build findings from rule results and link matching rule evidence."""
        if not isinstance(data, dict):
            return []

        metric = data.get("metric")
        status = data.get("status")

        if (
            not isinstance(metric, str)
            or not isinstance(status, str)
            or status not in {"WARNING", "CRITICAL"}
        ):
            return []

        value = data.get("value")
        unit = data.get("unit", "")
        reason = data.get("reason") or (
            f"{metric} evaluated as {status}."
        )

        findings = []

        for evidence in context.evidence:
            metadata = evidence.metadata

            if metadata.get("source_type") != "rule":
                continue
            if metadata.get("metric") != metric:
                continue
            if metadata.get("status") != status:
                continue

            # If both sides contain a measured value, require it to match.
            evidence_value = metadata.get("value")
            if evidence_value is not None and value is not None:
                if evidence_value != value:
                    continue

            findings.append(
                {
                    "finding": (
                        f"{metric.replace('_', ' ').title()} "
                        f"is {status.lower()}"
                    ),
                    "severity": status,
                    "source_ids": [evidence.source_id],
                    "reason": reason,
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                }
            )

        # Don't claim a source supports a finding when no matching
        # rule evidence exists in the request context.
        if not findings:
            findings.append(
                {
                    "finding": (
                        f"{metric.replace('_', ' ').title()} "
                        f"is {status.lower()}"
                    ),
                    "severity": status,
                    "source_ids": [],
                    "reason": reason,
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                }
            )

        return findings

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
                    statuses.extend(
                        DecisionEngine._extract_statuses(value)
                    )

            return statuses

        if isinstance(data, (list, tuple)):
            statuses = []
            for item in data:
                statuses.extend(
                    DecisionEngine._extract_statuses(item)
                )
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
"""Generate evidence-grounded responses from manufacturing decisions."""

from typing import Any


class ResponseGenerator:
    """Convert structured maintenance decisions into readable responses."""

    def generate(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Generate a response while preserving findings and evidence references."""
        findings = decision.get("findings", [])
        evidence = decision.get("evidence", [])
        approval = decision.get("approval", {})

        evidence_by_id = {
            item["source_id"]: item
            for item in evidence
            if isinstance(item, dict) and item.get("source_id")
        }

        finding_summaries = []

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            source_ids = finding.get("source_ids", [])
            supporting_evidence = [
                source_id
                for source_id in source_ids
                if source_id in evidence_by_id
            ]

            finding_summaries.append(
                {
                    "finding": finding.get(
                        "finding", "Unspecified finding"
                    ),
                    "severity": finding.get("severity", "UNKNOWN"),
                    "reason": finding.get("reason", ""),
                    "source_ids": source_ids,
                    "supporting_evidence": supporting_evidence,
                    "traceability_complete": (
                        bool(source_ids)
                        and len(supporting_evidence) == len(source_ids)
                    ),
                }
            )

        sensor_data_status = decision.get(
            "sensor_data_status", "UNKNOWN"
        )

        if sensor_data_status == "UNAVAILABLE":
            data_gaps = [
                "Vibration readings are unavailable; "
                "vibration-based assessment cannot be confirmed."
            ]
        elif sensor_data_status == "INCOMPLETE":
            data_gaps = [
                "Vibration data is incomplete; "
                "a complete vibration-based assessment is unavailable."
            ]
        else:
            data_gaps = []

        overall_status = decision.get("overall_status", "UNKNOWN")

        if not finding_summaries:
            summary = (
                f"Maintenance assessment status: {overall_status}. "
                "No findings were provided by the decision engine."
            )
        else:
            summary = (
                f"Maintenance assessment status: {overall_status}. "
                f"{len(finding_summaries)} finding(s) were identified."
            )

        return {
            "request_id": decision.get("request_id"),
            "machine_id": decision.get("machine_id"),
            "overall_status": overall_status,
            "summary": summary,
            "findings": finding_summaries,
            "data_gaps": data_gaps,
            "approval": {
                "required": approval.get("required", False),
                "status": approval.get("status", "NOT_EVALUATED"),
                "reason": approval.get("reason", ""),
            },
            "evidence_count": len(evidence),
        }

"""Evidence-grounded defect monitoring for manufacturing quality data."""

from typing import Any

from app.evidence.collector import EvidenceCollector
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool


class DefectMonitoringWorkflow:
    """Calculate defect metrics and evaluate them against configured rules."""

    def __init__(
        self,
        sql_tool: SQLTool,
        rules_tool: RulesTool,
        evidence_collector: EvidenceCollector,
    ) -> None:
        self.sql_tool = sql_tool
        self.rules_tool = rules_tool
        self.evidence_collector = evidence_collector

    def run(
        self,
        user_query: str = "Monitor manufacturing defects",
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a bounded, read-only defect-monitoring investigation."""

        # Keep evidence request-scoped to prevent cross-request leakage.
        collector = EvidenceCollector(
            traceability_registry=(
                self.evidence_collector._traceability_registry
            )
        )

        # Calculate quality metrics independently of the Defects join.
        # DefectRate is stored as a fraction, e.g. 0.027 = 2.7%.
        quality_rows = self.sql_tool.execute(
            """
            SELECT
                COUNT(*) AS quality_check_count,
                SUM(CASE WHEN LOWER(Result) = 'fail' THEN 1 ELSE 0 END)
                    AS failed_checks,
                SUM(CASE WHEN LOWER(Result) = 'rework' THEN 1 ELSE 0 END)
                    AS rework_checks,
                AVG(DefectRate) AS avg_defect_rate,
                AVG(ReworkRate) AS avg_rework_rate,
                AVG(YieldRate) AS avg_yield_rate
            FROM QualityControl
            """
        )
        collector.add_sql_evidence(
            "SQL:quality_control_summary", quality_rows
        )

        # Aggregate defects separately to avoid multiplying quality rows.
        defect_rows = self.sql_tool.execute(
            """
            SELECT
                DefectType AS defect_type,
                COUNT(*) AS defect_records,
                COALESCE(SUM(Quantity), 0) AS affected_quantity,
                AVG(Severity) AS average_severity
            FROM Defects
            GROUP BY DefectType
            ORDER BY defect_records DESC, defect_type
            LIMIT 10
            """
        )
        collector.add_sql_evidence(
            "SQL:defect_type_breakdown", defect_rows
        )

        cause_rows = self.sql_tool.execute(
            """
            SELECT
                RootCause AS root_cause,
                COUNT(*) AS defect_records,
                COALESCE(SUM(Quantity), 0) AS affected_quantity
            FROM Defects
            WHERE RootCause IS NOT NULL
              AND TRIM(RootCause) <> ''
            GROUP BY RootCause
            ORDER BY defect_records DESC, root_cause
            LIMIT 10
            """
        )
        collector.add_sql_evidence(
            "SQL:recorded_root_causes", cause_rows
        )

        quality = quality_rows[0] if quality_rows else {}
        quality_count = quality.get("quality_check_count") or 0

        metrics: dict[str, Any] = {
            "quality_check_count": quality_count,
            "failed_checks": quality.get("failed_checks") or 0,
            "rework_checks": quality.get("rework_checks") or 0,
            "average_defect_rate_percent": None,
            "average_rework_rate_percent": None,
            "average_yield_rate_percent": None,
        }

        findings: list[dict[str, Any]] = []
        overall_status = "DATA_UNAVAILABLE"

        if quality_count > 0 and quality.get("avg_defect_rate") is not None:
            # Stored rates are fractions; rules use percentage points.
            defect_rate_percent = float(
                quality["avg_defect_rate"]
            ) * 100.0

            metrics["average_defect_rate_percent"] = round(
                defect_rate_percent, 2
            )

            if quality.get("avg_rework_rate") is not None:
                metrics["average_rework_rate_percent"] = round(
                    float(quality["avg_rework_rate"]) * 100.0, 2
                )

            if quality.get("avg_yield_rate") is not None:
                metrics["average_yield_rate_percent"] = round(
                    float(quality["avg_yield_rate"]) * 100.0, 2
                )

            rule_result = self.rules_tool.evaluate(
                "defect_rate", defect_rate_percent
            )
            collector.add_rule_evidence(
                rule_result, source_id="RULE:average_defect_rate"
            )

            overall_status = rule_result["status"]

            findings.append(
                {
                    "finding": "Average quality-control defect rate",
                    "value": metrics["average_defect_rate_percent"],
                    "unit": "%",
                    "severity": overall_status,
                    "reason": rule_result["reason"],
                    "source_ids": [
                        "SQL:quality_control_summary",
                        "RULE:average_defect_rate",
                    ],
                }
            )
        else:
            findings.append(
                {
                    "finding": "Quality metrics unavailable",
                    "severity": "UNKNOWN",
                    "reason": (
                        "No usable QualityControl defect-rate data "
                        "was returned; a threshold assessment was not made."
                    ),
                    "source_ids": ["SQL:quality_control_summary"],
                }
            )

        if defect_rows:
            findings.append(
                {
                    "finding": "Most frequently recorded defect types",
                    "severity": "INFORMATIONAL",
                    "reason": (
                        "The list ranks defect records by type. "
                        "It is not a time-based trend or a defect rate."
                    ),
                    "source_ids": ["SQL:defect_type_breakdown"],
                }
            )

        evidence = [
            {
                "source_id": item.source_id,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in collector.collect()
        ]

        summary = (
            "Defect monitoring status: "
            f"{overall_status}. "
            f"Evaluated {quality_count} quality-control record(s)."
        )

        return {
            "request_id": request_id,
            "use_case": "defect_monitoring",
            "user_query": user_query,
            "overall_status": overall_status,
            "summary": summary,
            "metrics": metrics,
            "top_defect_types": defect_rows,
            "recorded_root_causes": cause_rows,
            "findings": findings,
            "evidence": evidence,
            "evidence_count": len(evidence),
        }
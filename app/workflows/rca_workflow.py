
"""Evidence-grounded root cause analysis for manufacturing quality issues."""

from typing import Any
from uuid import uuid4

from app.evidence.collector import EvidenceCollector
from app.tools.rag_tool import RAGTool
from app.tools.sql_tool import SQLTool


class RCAWorkflow:
    """Investigate a manufacturing quality issue using SQL and RAG."""

    def __init__(
        self,
        sql_tool: SQLTool,
        rag_tool: RAGTool,
        evidence_collector: EvidenceCollector,
    ) -> None:
        self.sql_tool = sql_tool
        self.rag_tool = rag_tool
        self.evidence_collector = evidence_collector

    def run(
        self,
        user_query: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        if not user_query or not user_query.strip():
            raise ValueError("user_query must not be blank")

        query = user_query.strip()
        collector = EvidenceCollector(
            traceability_registry=(
                self.evidence_collector._traceability_registry
            )
        )

        # Find likely context identifiers explicitly mentioned by the user.
        # Avoid guessing an order or machine when the query doesn't specify one.
        machine_id = self._extract_id(query, ("machine",))
        order_id = self._extract_id(query, ("order", "work order"))
        check_id = self._extract_id(query, ("check", "inspection"))

        context_rows: dict[str, list[dict[str, Any]]] = {}

        context_rows["defects"] = self.sql_tool.execute(
            """
            SELECT DefectID, CheckID, DefectType, Severity, Quantity,
                   Location, RootCause, ActionTaken
            FROM Defects
            WHERE (? IS NULL OR CheckID = ?)
              AND (? IS NULL OR Severity >= ?)
            ORDER BY Severity DESC, DefectID DESC
            LIMIT 100
            """,
            (check_id, check_id, 5 if "critical" in query.lower() else None,
             5 if "critical" in query.lower() else None),
        )
        collector.add_sql_evidence("SQL:rca_defects", context_rows["defects"])

        if check_id is not None:
            context_rows["quality_checks"] = self.sql_tool.execute(
                """
                SELECT CheckID, OrderID, Date, Result, Comments,
                       DefectRate, ReworkRate, YieldRate
                FROM QualityControl
                WHERE CheckID = ?
                LIMIT 20
                """,
                (check_id,),
            )
        else:
            context_rows["quality_checks"] = self.sql_tool.execute(
                """
                SELECT CheckID, OrderID, Date, Result, Comments,
                       DefectRate, ReworkRate, YieldRate
                FROM QualityControl
                WHERE LOWER(Result) IN ('fail', 'rework')
                ORDER BY Date DESC
                LIMIT 20
                """
            )
        collector.add_sql_evidence(
            "SQL:rca_quality_checks", context_rows["quality_checks"]
        )

        if order_id is not None:
            context_rows["work_orders"] = self.sql_tool.execute(
                """
                SELECT OrderID, ProductID, WorkCenterID, MachineID, Status,
                       Priority, Quantity, Scrap, LotNumber
                FROM WorkOrders
                WHERE OrderID = ?
                LIMIT 20
                """,
                (order_id,),
            )
        else:
            context_rows["work_orders"] = []

        collector.add_sql_evidence(
            "SQL:rca_work_orders", context_rows["work_orders"]
        )

        if machine_id is not None:
            context_rows["machine_conditions"] = self.sql_tool.execute(
                """
                SELECT MachineID, Timestamp, RMS_Velocity,
                       Peak_Acceleration, Temperature, Health_Score,
                       Anomaly_Flag, OrderID
                FROM VibrationAnalysis
                WHERE MachineID = ?
                ORDER BY Timestamp DESC
                LIMIT 10
                """,
                (machine_id,),
            )
        else:
            context_rows["machine_conditions"] = []

        collector.add_sql_evidence(
            "SQL:rca_machine_conditions",
            context_rows["machine_conditions"],
        )

        rag_results = self.rag_tool.search(
            query=(
                "Root cause analysis guide, corrective and preventive "
                f"actions for this manufacturing issue: {query}"
            ),
            top_k=4,
        )
        for result in rag_results:
            collector.add_rag_evidence(result)

        evidence = [
            {
                "source_id": item.source_id,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in collector.collect()
        ]

        defects = context_rows["defects"]
        recorded_causes: dict[str, int] = {}
        for defect in defects:
            cause = defect.get("RootCause")
            if cause:
                recorded_causes[str(cause)] = (
                    recorded_causes.get(str(cause), 0) + 1
                )

        ranked_causes = sorted(
            recorded_causes.items(),
            key=lambda item: (-item[1], item[0]),
        )

        if defects:
            status = "EVIDENCE_AVAILABLE"
            summary = (
                f"Retrieved {len(defects)} defect record(s) for the RCA "
                "investigation. Recorded causes are historical labels, "
                "not proof of causation."
            )
        else:
            status = "INSUFFICIENT_EVIDENCE"
            summary = (
                "No defect records matched the supplied filters. "
                "The investigation cannot establish a root cause from "
                "the available matching defect data."
            )

        return {
            "request_id": request_id or str(uuid4()),
            "use_case": "root_cause_analysis",
            "user_query": query,
            "overall_status": status,
            "summary": summary,
            "context": {
                "machine_id": machine_id,
                "order_id": order_id,
                "check_id": check_id,
                "record_counts": {
                    name: len(rows) for name, rows in context_rows.items()
                },
            },
            "candidate_recorded_causes": [
                {"cause": cause, "record_count": count}
                for cause, count in ranked_causes
            ],
            "corrective_preventive_guidance": [
                {
                    "source_id": item.source_id,
                    "document_id": item.metadata.get("document_id"),
                    "chunk_id": item.metadata.get("chunk_id"),
                    "content": item.content,
                }
                for item in collector.collect()
                if item.metadata.get("source_type") == "rag"
            ],
            "findings": [
                {
                    "finding": (
                        "Historical root-cause labels are candidate evidence"
                    ),
                    "severity": "INFORMATIONAL",
                    "reason": (
                        "Correlate these labels with the matching quality, "
                        "work-order and machine records before concluding."
                    ),
                    "source_ids": ["SQL:rca_defects"],
                }
            ] if defects else [],
            "evidence": evidence,
            "evidence_count": len(evidence),
        }

    @staticmethod
    def _extract_id(query: str, labels: tuple[str, ...]) -> int | None:
        import re

        for label in sorted(labels, key=len, reverse=True):
            match = re.search(
                rf"\b{re.escape(label)}\s*#?\s*(\d+)\b",
                query,
                re.IGNORECASE,
            )
            if match:
                return int(match.group(1))
        return None

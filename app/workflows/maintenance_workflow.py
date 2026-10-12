
"""Predefined predictive-maintenance investigation workflow."""

from typing import Any
from uuid import uuid4

from app.context.manager import ContextManager, create_request_context
from app.context.models import ToolResult
from app.decision.approval_policy import ApprovalPolicy
from app.decision.approval_repository import ApprovalRepository
from app.decision.decision_engine import DecisionEngine
from app.evidence.collector import EvidenceCollector
from app.tools.rag_tool import RAGTool
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool


class MaintenanceWorkflow:
    """Investigate a machine using SQL, RAG, rules, and evidence."""

    def __init__(
        self,
        sql_tool: SQLTool,
        rag_tool: RAGTool,
        rules_tool: RulesTool,
        evidence_collector: EvidenceCollector,
        decision_engine: DecisionEngine,
        approval_repository: ApprovalRepository | None = None,
    ) -> None:
        self.sql_tool = sql_tool
        self.rag_tool = rag_tool
        self.rules_tool = rules_tool
        self.evidence_collector = evidence_collector
        self.decision_engine = decision_engine
        self.approval_repository = approval_repository

    def run(
        self,
        machine_id: int,
        user_query: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Run a bounded, deterministic maintenance investigation."""
        if isinstance(machine_id, bool) or not isinstance(machine_id, int):
            raise TypeError("machine_id must be an integer")

        if machine_id <= 0:
            raise ValueError("machine_id must be positive")

        if not user_query or not user_query.strip():
            raise ValueError("user_query must not be blank")

        context = create_request_context(
            request_id=request_id or str(uuid4()),
            user_query=user_query.strip(),
        )
        context_manager = ContextManager(context)

        # The collector is request-scoped to avoid cross-request evidence leaks.
        collector = EvidenceCollector(
            traceability_registry=self.evidence_collector._traceability_registry
        )

        queries = [
            (
                "machine_lookup",
                """
                SELECT MachineID, Name, Type, Status,
                       LastMaintenanceDate, NextMaintenanceDate
                FROM Machines
                WHERE MachineID = ?
                """,
            ),
            (
                "predictive_maintenance",
                """
                SELECT PredictionID, MachineID, PredictionDate,
                       FailureMode, PredictedFailureDate, Confidence,
                       RemainingUsefulLife, RecommendedAction,
                       Priority, Status
                FROM PredictiveMaintenance
                WHERE MachineID = ?
                ORDER BY PredictionDate DESC
                """,
            ),
            (
                "vibration_analysis",
                """
                SELECT AnalysisID, MachineID, Timestamp,
                       RMS_Velocity, Peak_Acceleration,
                       Frequency_Dominant, Temperature,
                       Health_Score, Anomaly_Flag
                FROM VibrationAnalysis
                WHERE MachineID = ?
                ORDER BY Timestamp DESC
                LIMIT 10
                """,
            ),
        ]

        query_rows: dict[str, list[dict[str, Any]]] = {}

        for source_id, query in queries:
            try:
                rows = self.sql_tool.execute(query, (machine_id,))
                query_rows[source_id] = rows

                context_manager.add_tool_result(
                    ToolResult(
                        tool_name=source_id,
                        success=True,
                        data=rows,
                    )
                )
                collector.add_sql_evidence(source_id, rows)

            except Exception as exc:
                query_rows[source_id] = []
                context_manager.add_tool_result(
                    ToolResult(
                        tool_name=source_id,
                        success=False,
                        error=str(exc),
                    )
                )

        # Evaluate only measurements actually returned by the database.
        latest_vibration = query_rows["vibration_analysis"]
        if latest_vibration:
            reading = latest_vibration[0].get("RMS_Velocity")

            if reading is not None:
                try:
                    rule_result = self.rules_tool.evaluate(
                        "vibration",
                        reading,
                    )
                    context_manager.add_tool_result(
                        ToolResult(
                            tool_name="vibration_rule",
                            success=True,
                            data=rule_result,
                        )
                    )
                    collector.add_rule_evidence(rule_result)

                except Exception as exc:
                    context_manager.add_tool_result(
                        ToolResult(
                            tool_name="vibration_rule",
                            success=False,
                            error=str(exc),
                        )
                    )

        try:
            rag_results = self.rag_tool.search(
                query=(
                    f"Maintenance procedures and troubleshooting "
                    f"for machine {machine_id}: {user_query}"
                ),
                top_k=3,
            )
            context_manager.add_tool_result(
                ToolResult(
                    tool_name="rag_search",
                    success=True,
                    data=[
                        {
                            "source_id": result.chunk.source_id,
                            "document_id": result.chunk.document_id,
                            "chunk_id": result.chunk.chunk_id,
                            "score": result.score,
                        }
                        for result in rag_results
                    ],
                )
            )

            for result in rag_results:
                collector.add_rag_evidence(result)

        except Exception as exc:
            context_manager.add_tool_result(
                ToolResult(
                    tool_name="rag_search",
                    success=False,
                    error=str(exc),
                )
            )

        collector.add_to_context(context_manager)

        decision = self.decision_engine.evaluate(context)

        # Determine whether human approval is required.
        approval_decision = ApprovalPolicy().evaluate(decision)

        approval: dict[str, Any] = {
            "required": approval_decision.required,
            "status": approval_decision.status.value,
            "reason": approval_decision.reason,
            "record_id": None,
            "approver": None,
            "decided_at": None,
        }

        # Persist approval only when required and a repository is configured.
        if approval_decision.required and self.approval_repository is not None:
            approval_record = self.approval_repository.get_or_create_pending(
                request_id=context.request_id,
                reason=approval_decision.reason,
            )

            approval.update(
                {
                    "record_id": approval_record["id"],
                    "status": approval_record["status"],
                    "reason": approval_record["reason"],
                    "approver": approval_record["approver"],
                    "decided_at": approval_record["decided_at"],
                }
            )

        decision["approval"] = approval

        decision["machine_id"] = machine_id
        decision["data_availability"] = {
            name: bool(rows) for name, rows in query_rows.items()
        }

        decision["maintenance_records"] = query_rows["predictive_maintenance"]
        decision["vibration_readings"] = query_rows["vibration_analysis"]
        decision["machine_records"] = query_rows["machine_lookup"]

        # Classify predictive-maintenance records by their recorded status.
        maintenance_records = query_rows["predictive_maintenance"]

        decision["active_alerts"] = [
            record
            for record in maintenance_records
            if str(record.get("Status", "")).strip().lower() == "active"
        ]

        decision["resolved_alerts"] = [
            record
            for record in maintenance_records
            if str(record.get("Status", "")).strip().lower() == "resolved"
        ]

        decision["false_positive_alerts"] = [
            record
            for record in maintenance_records
            if str(record.get("Status", "")).strip().lower()
            == "false_positive"
        ]

        # Missing sensor readings mean unknown, not normal.
        vibration_readings = query_rows["vibration_analysis"]

        if not vibration_readings:
            sensor_data_status = "UNAVAILABLE"
        elif vibration_readings[0].get("RMS_Velocity") is None:
            sensor_data_status = "INCOMPLETE"
        else:
            sensor_data_status = "AVAILABLE"

        decision["sensor_data_status"] = sensor_data_status

        return decision

"""Factory for the defect-monitoring workflow."""

from app.config.settings import settings
from app.evidence.collector import EvidenceCollector
from app.observability.traceability import TraceabilityRegistry
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool
from app.workflows.defect_monitoring_workflow import (
    DefectMonitoringWorkflow,
)


def create_defect_monitoring_workflow() -> DefectMonitoringWorkflow:
    """Build a defect-monitoring workflow using the configured MES database."""

    if not settings.MES_DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"MES database not found: {settings.MES_DATABASE_PATH}"
        )

    return DefectMonitoringWorkflow(
        sql_tool=SQLTool(settings.MES_DATABASE_PATH),
        rules_tool=RulesTool(),
        evidence_collector=EvidenceCollector(
            traceability_registry=TraceabilityRegistry()
        ),
    )
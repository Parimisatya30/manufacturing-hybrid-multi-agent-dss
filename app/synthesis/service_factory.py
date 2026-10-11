
"""Build the maintenance service and its dependencies."""

from app.config.settings import PROJECT_ROOT, settings
from app.decision.decision_engine import DecisionEngine
from app.evidence.collector import EvidenceCollector
from app.observability.traceability import TraceabilityRegistry
from app.rag.knowledge_base import KnowledgeBaseService
from app.synthesis.maintenance_service import MaintenanceService
from app.tools.rag_tool import RAGTool
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool
from app.workflows.maintenance_workflow import MaintenanceWorkflow


def create_maintenance_service() -> MaintenanceService:
    """Initialize the components required for maintenance investigations."""

    if not settings.MES_DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"MES database not found: {settings.MES_DATABASE_PATH}"
        )

    knowledge_base = KnowledgeBaseService()
    documents_dir = PROJECT_ROOT / "data" / "raw" / "documents"

    if documents_dir.is_dir():
        pdf_files = sorted(documents_dir.glob("*.pdf"))

        for pdf_path in pdf_files:
            knowledge_base.index_pdf(pdf_path)

    traceability_registry = TraceabilityRegistry()

    workflow = MaintenanceWorkflow(
        sql_tool=SQLTool(settings.MES_DATABASE_PATH),
        rag_tool=RAGTool(knowledge_base),
        rules_tool=RulesTool(),
        evidence_collector=EvidenceCollector(
            traceability_registry=traceability_registry
        ),
        decision_engine=DecisionEngine(),
    )

    return MaintenanceService(workflow=workflow)
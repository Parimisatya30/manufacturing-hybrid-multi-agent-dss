
"""Factory for the RCA workflow and its dependencies."""

from app.config.settings import PROJECT_ROOT, settings
from app.evidence.collector import EvidenceCollector
from app.observability.traceability import TraceabilityRegistry
from app.rag.knowledge_base import KnowledgeBaseService
from app.tools.rag_tool import RAGTool
from app.tools.sql_tool import SQLTool
from app.workflows.rca_workflow import RCAWorkflow


def create_rca_workflow() -> RCAWorkflow:
    """Build an RCA workflow using the configured MES database and PDFs."""

    if not settings.MES_DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"MES database not found: {settings.MES_DATABASE_PATH}"
        )

    knowledge_base = KnowledgeBaseService()
    documents_dir = PROJECT_ROOT / "data" / "raw" / "documents"

    if documents_dir.is_dir():
        for pdf_path in sorted(documents_dir.glob("*.pdf")):
            knowledge_base.index_pdf(pdf_path)

    return RCAWorkflow(
        sql_tool=SQLTool(settings.MES_DATABASE_PATH),
        rag_tool=RAGTool(knowledge_base),
        evidence_collector=EvidenceCollector(
            traceability_registry=TraceabilityRegistry()
        ),
    )
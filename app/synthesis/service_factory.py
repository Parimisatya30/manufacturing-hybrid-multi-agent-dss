
"""Build the maintenance service and its dependencies."""

from app.config.settings import PROJECT_ROOT, settings
from app.decision.decision_engine import DecisionEngine
from app.evidence.collector import EvidenceCollector
from app.llm import OllamaProvider
from app.observability.traceability import TraceabilityRegistry
from app.rag.knowledge_base import KnowledgeBaseService
from app.synthesis.maintenance_service import MaintenanceService
from app.synthesis.response_generator import ResponseGenerator
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

    # Initialize the RAG knowledge base and index available PDFs.
    knowledge_base = KnowledgeBaseService()
    documents_dir = PROJECT_ROOT / "data" / "raw" / "documents"

    if documents_dir.is_dir():
        pdf_files = sorted(documents_dir.glob("*.pdf"))

        for pdf_path in pdf_files:
            knowledge_base.index_pdf(pdf_path)

    # Configure the LLM provider. Provider construction does not invoke
    # the model; inference happens when a response explanation is requested.
    llm_provider = None

    if settings.LLM_PROVIDER.lower() == "ollama":
        llm_provider = OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )

    # Set up request evidence traceability.
    traceability_registry = TraceabilityRegistry()
    evidence_collector = EvidenceCollector(
        traceability_registry=traceability_registry
    )

    # Build the deterministic maintenance workflow.
    workflow = MaintenanceWorkflow(
        sql_tool=SQLTool(settings.MES_DATABASE_PATH),
        rag_tool=RAGTool(knowledge_base),
        rules_tool=RulesTool(),
        evidence_collector=evidence_collector,
        decision_engine=DecisionEngine(),
    )

    # Inject the optional LLM into response synthesis.
    response_generator = ResponseGenerator(
        llm_provider=llm_provider,
    )

    return MaintenanceService(
        workflow=workflow,
        response_generator=response_generator,
    )
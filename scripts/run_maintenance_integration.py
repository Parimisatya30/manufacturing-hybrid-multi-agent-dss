from pathlib import Path
import json

from app.config.settings import settings
from app.context.manager import create_request_context
from app.decision.decision_engine import DecisionEngine
from app.evidence.collector import EvidenceCollector
from app.rag.knowledge_base import KnowledgeBaseService
from app.tools.rag_tool import RAGTool
from app.tools.rules_tool import RulesTool
from app.tools.sql_tool import SQLTool
from app.workflows.maintenance_workflow import MaintenanceWorkflow


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    pdf_dir = project_root / "data" / "raw" / "documents"

    sql_tool = SQLTool(settings.MES_DATABASE_PATH)

    knowledge_base = KnowledgeBaseService()
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"No PDF documents found in {pdf_dir}")

    for pdf_path in pdf_files:
        chunks = knowledge_base.index_pdf(pdf_path)
        print(f"Indexed {pdf_path.name}: {chunks} chunks")

    workflow = MaintenanceWorkflow(
        sql_tool=sql_tool,
        rag_tool=RAGTool(knowledge_base),
        rules_tool=RulesTool(),
        evidence_collector=EvidenceCollector(),
        decision_engine=DecisionEngine(),
    )

    result = workflow.run(
        machine_id=8,
        user_query="Investigate the machine breakdown and assess maintenance risk.",
        request_id="integration-machine-8",
    )

    print("\n=== Maintenance Workflow Result ===")
    print(json.dumps(result, indent=2, default=str))

    print("\n=== Validation Summary ===")
    print(f"Machine found: {bool(result['machine_records'])}")
    print(f"Maintenance data available: {result['data_availability']['predictive_maintenance']}")
    print(f"Vibration data available: {result['data_availability']['vibration_analysis']}")
    print(f"Evidence count: {result['evidence_count']}")
    print(f"Overall status: {result['overall_status']}")


if __name__ == "__main__":
    main()

from pathlib import Path
import json

from app.config.settings import settings
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
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / "maintenance_integration_result.json"

    # Ensure the output directory exists.
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize the SQL tool.
    sql_tool = SQLTool(settings.MES_DATABASE_PATH)

    # Index the manufacturing knowledge-base documents.
    knowledge_base = KnowledgeBaseService()
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF documents found in {pdf_dir}"
        )

    indexed_documents = []

    for pdf_path in pdf_files:
        chunks = knowledge_base.index_pdf(pdf_path)

        indexed_documents.append(
            {
                "document": pdf_path.name,
                "chunks_indexed": chunks,
            }
        )

        print(f"Indexed {pdf_path.name}: {chunks} chunks")

    # Construct the maintenance workflow.
    workflow = MaintenanceWorkflow(
        sql_tool=sql_tool,
        rag_tool=RAGTool(knowledge_base),
        rules_tool=RulesTool(),
        evidence_collector=EvidenceCollector(),
        decision_engine=DecisionEngine(),
    )

    # Execute the investigation.
    result = workflow.run(
        machine_id=8,
        user_query=(
            "Investigate the machine breakdown and "
            "assess maintenance risk."
        ),
        request_id="integration-machine-8",
    )

    # Build a report containing the full workflow result
    # and the validation summary.
    report = {
        "request_id": "integration-machine-8",
        "machine_id": 8,
        "indexed_documents": indexed_documents,
        "validation_summary": {
            "machine_found": bool(result.get("machine_records")),
            "maintenance_data_available": result.get(
                "data_availability", {}
            ).get("predictive_maintenance", False),
            "vibration_data_available": result.get(
                "data_availability", {}
            ).get("vibration_analysis", False),
            "evidence_count": result.get("evidence_count", 0),
            "overall_status": result.get("overall_status"),
            "sensor_data_status": result.get("sensor_data_status"),
        },
        "workflow_result": result,
    }

    # Save the complete report to JSON.
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    # Print the validation summary.
    summary = report["validation_summary"]

    print("\n=== Validation Summary ===")
    print(f"Machine found: {summary['machine_found']}")
    print(
        "Maintenance data available: "
        f"{summary['maintenance_data_available']}"
    )
    print(
        "Vibration data available: "
        f"{summary['vibration_data_available']}"
    )
    print(f"Evidence count: {summary['evidence_count']}")
    print(f"Overall status: {summary['overall_status']}")
    print(f"Sensor data status: {summary['sensor_data_status']}")

    print("\n=== Detailed Report ===")
    print(f"Saved to: {output_file.resolve()}")
    print("Open this JSON file in VS Code to inspect the findings.")


if __name__ == "__main__":
    main()
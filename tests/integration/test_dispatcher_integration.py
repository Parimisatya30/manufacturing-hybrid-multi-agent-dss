"""Integration tests for dispatcher routing with the real MES database."""

from pathlib import Path

import pytest

from app.router.dispatcher import RequestDispatcher
from app.router.sql_operations import SQLOperationRegistry
from app.router.task_router import ExecutionPath, TaskRouter
from app.tools.sql_tool import SQLTool
from app.rag.knowledge_base import KnowledgeBaseService
from app.tools.rag_tool import RAGTool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "raw" / "MES.db"


@pytest.fixture
def dispatcher() -> RequestDispatcher:
    """Build a dispatcher backed by the real, read-only MES database."""
    if not DATABASE_PATH.exists():
        pytest.skip(f"MES database not found: {DATABASE_PATH}")

    sql_tool = SQLTool(DATABASE_PATH)
    registry = SQLOperationRegistry(sql_tool)

    return RequestDispatcher(
        router=TaskRouter(),
        sql_operations=registry.operations(),
    )


def test_dispatch_machine_details_uses_real_database(dispatcher):
    response = dispatcher.dispatch("Show machine 8 details")

    assert response["execution_path"] == ExecutionPath.DIRECT_SQL.value
    assert response["intent"]
    assert response["result"]

    machine = response["result"][0]
    assert machine["MachineID"] == 8
    assert machine["Name"] == "Machine Whe-40"
    assert machine["Type"] == "Wheel Assembly"


def test_dispatch_list_machines_uses_real_database(dispatcher):
    response = dispatcher.dispatch("List machines")

    assert response["execution_path"] == ExecutionPath.DIRECT_SQL.value
    assert isinstance(response["result"], list)
    assert response["result"]

    machine_ids = [machine["MachineID"] for machine in response["result"]]
    assert machine_ids == sorted(machine_ids)

def test_dispatch_knowledge_query_uses_real_rag(dispatcher):
    """Verify that a knowledge query reaches the indexed manufacturing PDFs."""
    knowledge_base = KnowledgeBaseService()
    pdf_dir = PROJECT_ROOT / "data" / "raw" / "documents"
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        pytest.skip(f"No manufacturing PDFs found in {pdf_dir}")

    for pdf_path in pdf_files:
        knowledge_base.index_pdf(pdf_path)

    dispatcher.rag_tool = RAGTool(knowledge_base)

    response = dispatcher.dispatch(
        "Explain vibration monitoring and predictive maintenance."
    )

    assert response["execution_path"] == ExecutionPath.DIRECT_RAG.value
    assert isinstance(response["result"], list)
    assert response["result"]

def test_dispatch_work_orders_uses_real_database(dispatcher):
    response = dispatcher.dispatch("Show work orders")

    assert response["execution_path"] == ExecutionPath.DIRECT_SQL.value
    assert isinstance(response["result"], list)
    assert len(response["result"]) <= 100

    if response["result"]:
        assert "OrderID" in response["result"][0]

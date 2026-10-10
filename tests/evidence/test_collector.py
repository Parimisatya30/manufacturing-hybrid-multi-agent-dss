from app.context.models import Evidence
from app.evidence.collector import EvidenceCollector
from app.rag.models import DocumentChunk
from app.rag.vector_store import SearchResult
from app.context.manager import ContextManager
from app.context.models import RequestContext
from app.observability.traceability import TraceabilityRegistry

def test_add_to_context_registers_traceability_sources():
    registry = TraceabilityRegistry()
    collector = EvidenceCollector(traceability_registry=registry)

    collector.add_sql_evidence(
        "MES:VibrationAnalysis",
        [{"machine_id": "M-01", "vibration": 11.2}],
    )

    context_manager = ContextManager(
        RequestContext(
            request_id="REQ-TRACE-001",
            user_query="Investigate machine vibration",
        )
    )

    count = collector.add_to_context(context_manager)

    assert count == 1
    assert len(context_manager.context.evidence) == 1

    source = registry.get_source("MES:VibrationAnalysis")
    assert source is not None
    assert source.source_type == "sql"
    assert source.locator == "MES:VibrationAnalysis"
    

def test_add_to_context_transfers_collected_evidence():
    collector = EvidenceCollector()
    collector.add_sql_evidence(
        "MES:Machines",
        [{"machine_id": "M-01"}],
    )
    collector.add_rule_evidence({
        "metric": "vibration",
        "value": 11.2,
        "status": "CRITICAL",
        "reason": "Vibration exceeded the critical threshold.",
    })

    context_manager = ContextManager(
        RequestContext(
            request_id="REQ-001",
            user_query="Investigate machine M-01",
        )
    )

    count = collector.add_to_context(context_manager)

    assert count == 2
    assert len(context_manager.context.evidence) == 2
    assert context_manager.context.evidence[0].source_id == "MES:Machines"
    assert context_manager.context.evidence[1].source_id == "RULE:vibration"


def test_add_sql_evidence():
    collector = EvidenceCollector()
    rows = [{"machine_id": "M-01", "vibration": 11.2}]

    evidence = collector.add_sql_evidence("MES:VibrationAnalysis", rows)

    assert isinstance(evidence, Evidence)
    assert evidence.metadata["source_type"] == "sql"
    assert evidence.metadata["row_count"] == 1
    assert evidence.metadata["rows"] == rows


def test_add_rule_evidence():
    collector = EvidenceCollector()
    result = {
        "metric": "vibration",
        "value": 11.2,
        "status": "CRITICAL",
        "reason": "Vibration reached the critical threshold.",
    }

    evidence = collector.add_rule_evidence(result)

    assert evidence.source_id == "RULE:vibration"
    assert evidence.metadata["source_type"] == "rule"
    assert evidence.metadata["status"] == "CRITICAL"


def test_add_rag_evidence_preserves_provenance():
    collector = EvidenceCollector()
    chunk = DocumentChunk(
        chunk_id="CHUNK-001",
        document_id="DOC-001",
        content="Inspect the machine bearings.",
        chunk_index=0,
        page_numbers=[2],
        sections=["Predictive Maintenance"],
        source_id="MAINTENANCE_GUIDE",
    )

    evidence = collector.add_rag_evidence(
        SearchResult(chunk=chunk, score=0.91)
    )

    assert evidence.source_id == "MAINTENANCE_GUIDE"
    assert evidence.content == "Inspect the machine bearings."
    assert evidence.metadata["source_type"] == "rag"
    assert evidence.metadata["page_numbers"] == [2]
    assert evidence.metadata["relevance_score"] == 0.91


def test_collect_returns_evidence_and_clear_resets_it():
    collector = EvidenceCollector()
    collector.add_sql_evidence("MES:Machines", [{"machine_id": "M-01"}])

    collected = collector.collect()

    assert len(collected) == 1
    assert collected[0].source_id == "MES:Machines"

    collected.clear()
    assert len(collector.collect()) == 1

    collector.clear()
    assert collector.collect() == []
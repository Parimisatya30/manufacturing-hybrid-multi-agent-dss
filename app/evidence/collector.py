"""Collect evidence from SQL, rules, and RAG sources."""

from typing import Any

from app.context.models import Evidence
from app.rag.vector_store import SearchResult


class EvidenceCollector:
    """Normalize evidence from different DSS tools."""

    def __init__(self) -> None:
        self._evidence: list[Evidence] = []

    def add_to_context(self, context_manager) -> int:
        """Transfer collected evidence into the request context."""
        evidence_items = self.collect()

        for evidence in evidence_items:
            context_manager.add_evidence(evidence)

        return len(evidence_items)

    def add_sql_evidence(
        self,
        source_id: str,
        rows: list[dict[str, Any]],
    ) -> Evidence:
        """Add evidence produced by a SQL query."""
        evidence = Evidence(
            source_id=source_id,
            content=f"SQL query returned {len(rows)} row(s).",
            metadata={
                "source_type": "sql",
                "rows": rows,
                "row_count": len(rows),
            },
        )
        self._evidence.append(evidence)
        return evidence

    def add_rule_evidence(
        self,
        result: dict[str, Any],
        source_id: str | None = None,
    ) -> Evidence:
        """Add a deterministic rules-engine result."""
        metric = result.get("metric", "unknown")
        resolved_source_id = source_id or f"RULE:{metric}"

        evidence = Evidence(
            source_id=resolved_source_id,
            content=str(result.get("reason", result)),
            metadata={
                "source_type": "rule",
                "rule_result": dict(result),
                "status": result.get("status"),
                "metric": metric,
            },
        )
        self._evidence.append(evidence)
        return evidence

    def add_rag_evidence(
        self,
        result: SearchResult,
    ) -> Evidence:
        """Add a retrieved passage with document provenance."""
        chunk = result.chunk
        source_id = (
            chunk.source_id
            or chunk.document_id
        )

        evidence = Evidence(
            source_id=source_id,
            content=chunk.content,
            metadata={
                "source_type": "rag",
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "page_numbers": list(chunk.page_numbers),
                "sections": list(chunk.sections),
                "relevance_score": result.score,
            },
        )
        self._evidence.append(evidence)
        return evidence

    def collect(self) -> list[Evidence]:
        """Return all collected evidence in insertion order."""
        return list(self._evidence)

    def clear(self) -> None:
        """Clear evidence for the next collection."""
        self._evidence.clear()
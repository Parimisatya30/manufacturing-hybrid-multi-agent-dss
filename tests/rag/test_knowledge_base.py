from unittest.mock import MagicMock

import pytest

from app.rag.knowledge_base import KnowledgeBaseService
from app.rag.models import DocumentChunk
from app.rag.vector_store import SearchResult


@pytest.fixture
def service():
    pipeline = MagicMock()

    chunk = DocumentChunk(
        chunk_id="CHUNK-001",
        document_id="DOC-001",
        content="Check vibration levels",
        chunk_index=0,
    )
    pipeline.index_pdf.return_value = [chunk]

    return KnowledgeBaseService(pipeline=pipeline), pipeline, chunk


def test_index_pdf_returns_chunk_count(service, tmp_path):
    instance, pipeline, chunk = service
    pdf_path = tmp_path / "maintenance.pdf"
    pdf_path.touch()

    count = instance.index_pdf(pdf_path)

    assert count == 1
    assert instance.indexed_document_count == 1
    pipeline.index_pdf.assert_called_once()


def test_index_pdf_rejects_duplicate_file(service, tmp_path):
    instance, pipeline, _ = service
    pdf_path = tmp_path / "maintenance.pdf"
    pdf_path.touch()

    instance.index_pdf(pdf_path)

    with pytest.raises(ValueError, match="already indexed"):
        instance.index_pdf(pdf_path)

    assert pipeline.index_pdf.call_count == 1


def test_search_delegates_to_pipeline(service):
    instance, pipeline, chunk = service
    expected = [SearchResult(chunk=chunk, score=0.95)]
    pipeline.retrieve.return_value = expected

    results = instance.search("vibration maintenance", top_k=2)

    pipeline.retrieve.assert_called_once_with(
        query="vibration maintenance",
        top_k=2,
    )
    assert results == expected


def test_failed_index_does_not_register_document(service, tmp_path):
    instance, pipeline, _ = service
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.touch()
    pipeline.index_pdf.side_effect = ValueError("Invalid PDF")

    with pytest.raises(ValueError, match="Invalid PDF"):
        instance.index_pdf(pdf_path)

    assert instance.indexed_document_count == 0

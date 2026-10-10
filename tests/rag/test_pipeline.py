from sympy import python
from unittest.mock import MagicMock

import pytest

from app.rag.models import Document, DocumentChunk
from app.rag.pipeline import RAGPipeline
from app.rag.vector_store import SearchResult


@pytest.fixture
def pipeline():
    loader = MagicMock()
    chunker = MagicMock()
    embedding_service = MagicMock()

    instance = RAGPipeline(
        loader=loader,
        chunker=chunker,
        embedding_service=embedding_service,
    )

    document = Document(
        document_id="DOC-001",
        source="maintenance.pdf",
        content="Maintenance guidance",
    )

    chunk = DocumentChunk(
        chunk_id="CHUNK-001",
        document_id="DOC-001",
        content="Check vibration levels",
        chunk_index=0,
    )

    loader.load.return_value = document
    chunker.chunk.return_value = [chunk]

    return instance, loader, chunker, document, chunk


def test_index_pdf_adds_chunks(pipeline):
    instance, loader, chunker, document, chunk = pipeline

    instance.vector_store.add_chunks = MagicMock()

    chunks = instance.index_pdf("maintenance.pdf")

    loader.load.assert_called_once_with(
        file_path="maintenance.pdf",
        document_id=None,
    )
    chunker.chunk.assert_called_once_with(document)
    instance.vector_store.add_chunks.assert_called_once_with([chunk])

    assert chunks == [chunk]


def test_index_pdf_rejects_duplicate_document(pipeline):
    instance, loader, chunker, document, chunk = pipeline

    instance.vector_store.add_chunks = MagicMock()

    instance.index_pdf("maintenance.pdf")

    with pytest.raises(ValueError, match="already indexed"):
        instance.index_pdf("maintenance.pdf")

    assert loader.load.call_count == 2
    assert chunker.chunk.call_count == 1
    assert instance.vector_store.add_chunks.call_count == 1


def test_retrieve_delegates_to_retrieval_service(pipeline):
    instance, _, _, _, chunk = pipeline

    expected = [SearchResult(chunk=chunk, score=0.95)]
    instance.retrieval_service.retrieve = MagicMock(
        return_value=expected
    )

    results = instance.retrieve(
        query="How do I check vibration?",
        top_k=2,
    )

    instance.retrieval_service.retrieve.assert_called_once_with(
        query="How do I check vibration?",
        top_k=2,
    )
    assert results == expected

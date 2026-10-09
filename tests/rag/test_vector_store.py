
from unittest.mock import MagicMock

from app.rag.models import DocumentChunk
from app.rag.vector_store import VectorStore


def make_chunk(chunk_id: str, content: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        content=content,
        chunk_index=0,
    )


def test_add_chunks_stores_embeddings():
    embedding_service = MagicMock()
    embedding_service.embed_chunks.return_value = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]
    store = VectorStore(embedding_service)
    chunks = [
        make_chunk("chunk-1", "Machine vibration"),
        make_chunk("chunk-2", "Quality inspection"),
    ]

    store.add_chunks(chunks)

    assert len(store._entries) == 2
    assert store._entries[0][0] is chunks[0]
    assert store._entries[1][1] == [0.0, 1.0]


def test_search_returns_most_similar_chunk_first():
    embedding_service = MagicMock()
    embedding_service.embed_chunks.return_value = [
        [0.0, 1.0],
        [1.0, 0.0],
    ]
    embedding_service.embed_text.return_value = [1.0, 0.0]
    store = VectorStore(embedding_service)
    chunks = [
        make_chunk("chunk-1", "Quality inspection"),
        make_chunk("chunk-2", "Machine vibration"),
    ]

    store.add_chunks(chunks)
    results = store.search("machine vibration", top_k=2)

    assert [result.chunk.chunk_id for result in results] == [
        "chunk-2",
        "chunk-1",
    ]
    assert results[0].score == 1.0
    assert results[1].score == 0.0


def test_search_returns_empty_list_when_store_is_empty():
    embedding_service = MagicMock()
    store = VectorStore(embedding_service)

    assert store.search("machine vibration") == []
    embedding_service.embed_text.assert_not_called()


def test_search_respects_top_k():
    embedding_service = MagicMock()
    embedding_service.embed_chunks.return_value = [
        [1.0, 0.0],
        [0.0, 1.0],
        [-1.0, 0.0],
    ]
    embedding_service.embed_text.return_value = [1.0, 0.0]
    store = VectorStore(embedding_service)
    chunks = [
        make_chunk("chunk-1", "A"),
        make_chunk("chunk-2", "B"),
        make_chunk("chunk-3", "C"),
    ]

    store.add_chunks(chunks)
    results = store.search("query", top_k=2)

    assert len(results) == 2
    assert [result.chunk.chunk_id for result in results] == [
        "chunk-1",
        "chunk-2",
    ]


def test_add_empty_chunks_does_not_call_embedding_service():
    embedding_service = MagicMock()
    store = VectorStore(embedding_service)

    store.add_chunks([])

    embedding_service.embed_chunks.assert_not_called()
    assert store._entries == []

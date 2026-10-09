from unittest.mock import MagicMock, patch

from app.rag.embeddings import EmbeddingService


@patch("app.rag.embeddings.SentenceTransformer")
def test_embed_chunks_returns_empty_list(model_class):
    service = EmbeddingService()
    assert service.embed_chunks([]) == []


@patch("app.rag.embeddings.SentenceTransformer")
def test_embed_chunks_returns_one_vector_per_chunk(model_class):
    model = MagicMock()
    model.encode.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]
    model_class.return_value = model

    service = EmbeddingService()
    chunks = [
        MagicMock(content="Machine vibration"),
        MagicMock(content="Quality inspection"),
    ]

    result = service.embed_chunks(chunks)

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert len(result) == len(chunks)

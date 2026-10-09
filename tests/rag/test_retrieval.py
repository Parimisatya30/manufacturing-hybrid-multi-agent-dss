
from unittest.mock import MagicMock

from app.rag.retrieval import RetrievalService


def test_retrieve_delegates_query_to_vector_store():
    vector_store = MagicMock()
    expected_results = [MagicMock()]
    vector_store.search.return_value = expected_results
    service = RetrievalService(vector_store)

    results = service.retrieve("machine vibration", top_k=2)

    assert results == expected_results
    vector_store.search.assert_called_once_with(
        "machine vibration",
        top_k=2,
    )


def test_retrieve_rejects_blank_query():
    vector_store = MagicMock()
    service = RetrievalService(vector_store)

    assert service.retrieve("   ") == []
    vector_store.search.assert_not_called()


def test_retrieve_returns_empty_for_nonpositive_top_k():
    vector_store = MagicMock()
    service = RetrievalService(vector_store)

    assert service.retrieve("machine vibration", top_k=0) == []
    vector_store.search.assert_not_called()

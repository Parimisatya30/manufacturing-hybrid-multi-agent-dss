from unittest.mock import Mock

from app.rag.vector_store import SearchResult
from app.tools.rag_tool import RAGTool


def test_search_delegates_to_knowledge_base():
    knowledge_base = Mock()
    expected_results = [Mock(spec=SearchResult)]
    knowledge_base.search.return_value = expected_results

    tool = RAGTool(knowledge_base)
    results = tool.search("  bearing maintenance  ", top_k=2)

    assert results == expected_results
    knowledge_base.search.assert_called_once_with(
        query="bearing maintenance",
        top_k=2,
    )


def test_search_returns_empty_for_blank_query():
    knowledge_base = Mock()
    tool = RAGTool(knowledge_base)

    assert tool.search("   ") == []
    knowledge_base.search.assert_not_called()


def test_search_returns_empty_for_non_positive_top_k():
    knowledge_base = Mock()
    tool = RAGTool(knowledge_base)

    assert tool.search("machine vibration", top_k=0) == []
    assert tool.search("machine vibration", top_k=-1) == []
    knowledge_base.search.assert_not_called()

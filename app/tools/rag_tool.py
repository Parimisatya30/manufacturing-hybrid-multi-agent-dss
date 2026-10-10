
"""RAG tool for retrieving manufacturing knowledge."""

from app.rag.knowledge_base import KnowledgeBaseService
from app.rag.vector_store import SearchResult


class RAGTool:
    """Expose manufacturing knowledge retrieval to DSS workflows."""

    def __init__(self, knowledge_base: KnowledgeBaseService) -> None:
        self.knowledge_base = knowledge_base


    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """Retrieve relevant manufacturing knowledge passages."""
        if not query or not query.strip():
            return []

        if top_k <= 0:
            return []

        return self.knowledge_base.search(
            query=query.strip(),
            top_k=top_k,
        )
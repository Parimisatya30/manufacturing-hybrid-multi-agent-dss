from app.rag.vector_store import SearchResult, VectorStore


class RetrievalService:
    """Retrieve relevant document chunks for a user query."""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """Return the most relevant chunks for a query."""
        if not query or not query.strip():
            return []

        if top_k <= 0:
            return []

        return self.vector_store.search(query.strip(), top_k=top_k)

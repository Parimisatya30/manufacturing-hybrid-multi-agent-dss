
from dataclasses import dataclass

from app.rag.embeddings import EmbeddingService
from app.rag.models import DocumentChunk


@dataclass
class SearchResult:
    """A retrieved chunk and its similarity score."""

    chunk: DocumentChunk
    score: float


class VectorStore:
    """Store chunk embeddings and retrieve similar chunks."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service
        self._entries: list[tuple[DocumentChunk, list[float]]] = []

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Embed and store document chunks."""
        if not chunks:
            return

        vectors = self.embedding_service.embed_chunks(chunks)

        if len(vectors) != len(chunks):
            raise ValueError("Each chunk must have exactly one embedding.")

        for chunk, vector in zip(chunks, vectors):
            self._entries.append((chunk, vector))

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """Return the most similar chunks for a query."""
        if top_k <= 0:
            return []

        if not self._entries:
            return []

        query_vector = self.embedding_service.embed_text(query)

        results = []
        for chunk, vector in self._entries:
            if len(query_vector) != len(vector):
                raise ValueError("Query and chunk embedding dimensions must match.")

            score = sum(
                query_value * chunk_value
                for query_value, chunk_value in zip(query_vector, vector)
            )
            results.append(SearchResult(chunk=chunk, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

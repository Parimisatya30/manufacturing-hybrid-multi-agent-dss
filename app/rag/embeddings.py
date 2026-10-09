
from sentence_transformers import SentenceTransformer

from app.rag.models import DocumentChunk


class EmbeddingService:
    """Generate semantic embeddings for document chunks."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.model = SentenceTransformer(model_name)

    @staticmethod
    def _to_list(vector) -> list[float]:
        """Convert a model vector to a regular Python list."""
        if hasattr(vector, "tolist"):
            return vector.tolist()
        return list(vector)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        return self._to_list(vector)

    def embed_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> list[list[float]]:
        """Generate one embedding per document chunk."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return [self._to_list(vector) for vector in vectors]

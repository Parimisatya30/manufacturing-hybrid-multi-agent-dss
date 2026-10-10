"""Manage manufacturing knowledge documents and retrieval."""

from pathlib import Path

from app.rag.models import DocumentChunk
from app.rag.pipeline import RAGPipeline
from app.rag.vector_store import SearchResult


class KnowledgeBaseService:
    """Provide a simple interface for indexing and querying PDFs."""

    def __init__(self, pipeline: RAGPipeline | None = None) -> None:
        self.pipeline = pipeline or RAGPipeline()
        self._indexed_files: dict[str, list[DocumentChunk]] = {}

    def index_pdf(
        self,
        file_path: str | Path,
        document_id: str | None = None,
    ) -> int:
        """Index a PDF and return the number of indexed chunks."""
        path = Path(file_path).resolve()
        key = str(path)

        if key in self._indexed_files:
            raise ValueError(f"PDF already indexed: {path}")

        chunks = self.pipeline.index_pdf(
            file_path=path,
            document_id=document_id,
        )

        self._indexed_files[key] = chunks
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """Search indexed manufacturing knowledge."""
        return self.pipeline.retrieve(query=query, top_k=top_k)

    @property
    def indexed_document_count(self) -> int:
        """Return the number of successfully indexed PDF files."""
        return len(self._indexed_files)

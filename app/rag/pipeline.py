
"""Orchestrate PDF ingestion, chunking, indexing, and retrieval."""

from pathlib import Path

from app.rag.chunking import SemanticChunker
from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import PDFDocumentLoader
from app.rag.models import DocumentChunk
from app.rag.retrieval import RetrievalService
from app.rag.vector_store import SearchResult, VectorStore


class RAGPipeline:
    """Minimal in-memory RAG retrieval pipeline."""

    def __init__(
        self,
        loader: PDFDocumentLoader | None = None,
        chunker: SemanticChunker | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.loader = loader or PDFDocumentLoader()
        self.chunker = chunker or SemanticChunker()

        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

        self.vector_store = VectorStore(self.embedding_service)
        self.retrieval_service = RetrievalService(self.vector_store)
        self._indexed_document_ids: set[str] = set()

    def index_pdf(
        self,
        file_path: str | Path,
        document_id: str | None = None,
    ) -> list[DocumentChunk]:
        """Load a PDF, chunk it, and add its chunks to the index."""
        document = self.loader.load(
            file_path=file_path,
            document_id=document_id,
        )

        if document.document_id in self._indexed_document_ids:
            raise ValueError(
                f"Document already indexed: {document.document_id}"
            )

        chunks = self.chunker.chunk(document)

        if not chunks:
            raise ValueError(
                f"No retrievable chunks found in PDF: {file_path}"
            )

        self.vector_store.add_chunks(chunks)
        self._indexed_document_ids.add(document.document_id)

        return chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """Retrieve relevant chunks for a question."""
        return self.retrieval_service.retrieve(
            query=query,
            top_k=top_k,
        )

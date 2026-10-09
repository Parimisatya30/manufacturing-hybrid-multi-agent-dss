from __future__ import annotations
from uuid import uuid4

from app.rag.models import Document, DocumentBlock, DocumentChunk


class SemanticChunker:
    """
    Convert structural document blocks into retrieval-oriented chunks.

    Current strategy:
    - Headings define semantic sections.
    - Paragraphs accumulate within a section.
    - A table remains attached to the current section.
    - Content after a table starts a new chunk.
    - Provenance is preserved in every chunk.

    Semantic similarity and size-based splitting will be added
    in later iterations.
    """

    def chunk(self, document: Document) -> list[DocumentChunk]:
        if not document.blocks:
            return []

        chunks: list[DocumentChunk] = []
        current_blocks: list[DocumentBlock] = []
        table_seen = False

        for block in document.blocks:

            # A heading always starts a new semantic section.
            if block.block_type == "heading":
                if current_blocks:
                    chunks.append(
                        self._build_chunk(
                            document=document,
                            blocks=current_blocks,
                            chunk_index=len(chunks),
                        )
                    )

                current_blocks = [block]
                table_seen = False
                continue

            # A table stays with the current section.
            if block.block_type == "table":
                current_blocks.append(block)
                table_seen = True
                continue

            # If content appears after a table, start a new chunk.
            if table_seen and current_blocks:
                chunks.append(
                    self._build_chunk(
                        document=document,
                        blocks=current_blocks,
                        chunk_index=len(chunks),
                    )
                )

                current_blocks = [block]
                table_seen = False
                continue

            current_blocks.append(block)

        if current_blocks:
            chunks.append(
                self._build_chunk(
                    document=document,
                    blocks=current_blocks,
                    chunk_index=len(chunks),
                )
            )

        return chunks

    @staticmethod
    def _build_chunk(
        document: Document,
        blocks: list[DocumentBlock],
        chunk_index: int,
    ) -> DocumentChunk:
        content_parts = [
            block.content.strip()
            for block in blocks
            if block.content.strip()
        ]

        page_numbers = sorted(
            {
                block.page_number
                for block in blocks
                if block.page_number is not None
            }
        )

        sections: list[str] = []

        for block in blocks:
            if block.section and block.section not in sections:
                sections.append(block.section)

        block_types: list[str] = []

        for block in blocks:
            if block.block_type not in block_types:
                block_types.append(block.block_type)

        return DocumentChunk(
            chunk_id=f"CHUNK-{uuid4()}",
            document_id=document.document_id,
            content="\n\n".join(content_parts),
            chunk_index=chunk_index,
            block_ids=[block.block_id for block in blocks],
            page_numbers=page_numbers,
            sections=sections,
            block_types=block_types,
            source_id=document.metadata.get("source_id"),
        )

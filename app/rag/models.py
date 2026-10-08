from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """
    A source knowledge document.

    Represents the original document together with the structural
    blocks extracted from it.
    """

    document_id: str
    source: str
    content: str = ""
    blocks: list["DocumentBlock"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentBlock:
    """
    A structural block extracted from a document.

    A block can represent a heading, paragraph, table, or figure.
    Blocks are the intermediate representation between document
    ingestion and semantic chunking.
    """

    block_id: str
    document_id: str
    block_type: str
    content: str
    page_number: int | None = None
    section: str | None = None
    block_index: int = 0
    table_data: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """
    A semantically meaningful retrieval unit.

    A chunk preserves provenance back to the source document and
    structural blocks from which it was created.
    """

    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    block_ids: list[str] = field(default_factory=list)

    page_numbers: list[int] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)

    block_types: list[str] = field(default_factory=list)

    topics: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)

    source_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
from app.rag.chunking import SemanticChunker
from app.rag.models import Document, DocumentBlock


def test_chunker_groups_paragraphs_under_heading():
    document = Document(
        document_id="DOC-001",
        source="test.pdf",
        blocks=[
            DocumentBlock(
                block_id="B1",
                document_id="DOC-001",
                block_type="heading",
                content="Overall Equipment Effectiveness",
                page_number=1,
                section="1. OEE",
            ),
            DocumentBlock(
                block_id="B2",
                document_id="DOC-001",
                block_type="paragraph",
                content="OEE measures equipment effectiveness.",
                page_number=1,
                section="1. OEE",
            ),
            DocumentBlock(
                block_id="B3",
                document_id="DOC-001",
                block_type="paragraph",
                content="It combines availability, performance, and quality.",
                page_number=1,
                section="1. OEE",
            ),
        ],
    )

    chunks = SemanticChunker().chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.document_id == "DOC-001"
    assert chunk.block_ids == ["B1", "B2", "B3"]
    assert chunk.page_numbers == [1]
    assert chunk.sections == ["1. OEE"]
    assert chunk.block_types == ["heading", "paragraph"]

    assert "Overall Equipment Effectiveness" in chunk.content
    assert "OEE measures equipment effectiveness." in chunk.content


def test_table_stays_with_section_context():
    document = Document(
        document_id="DOC-001",
        source="test.pdf",
        blocks=[
            DocumentBlock(
                block_id="B1",
                document_id="DOC-001",
                block_type="heading",
                content="OEE Components",
                page_number=1,
                section="2. Components",
            ),
            DocumentBlock(
                block_id="B2",
                document_id="DOC-001",
                block_type="paragraph",
                content="The following table defines the components.",
                page_number=1,
                section="2. Components",
            ),
            DocumentBlock(
                block_id="B3",
                document_id="DOC-001",
                block_type="table",
                content="Availability | Performance | Quality",
                page_number=1,
                section="2. Components",
            ),
            DocumentBlock(
                block_id="B4",
                document_id="DOC-001",
                block_type="paragraph",
                content="These values are used to calculate OEE.",
                page_number=1,
                section="2. Components",
            ),
        ],
    )

    chunks = SemanticChunker().chunk(document)

    assert len(chunks) == 2

    assert chunks[0].block_ids == ["B1", "B2", "B3"]
    assert chunks[0].block_types == ["heading", "paragraph", "table"]

    assert chunks[1].block_ids == ["B4"]
    assert chunks[1].block_types == ["paragraph"]

def test_empty_document_returns_no_chunks():
    document = Document(
        document_id="DOC-001",
        source="empty.pdf",
    )

    chunks = SemanticChunker().chunk(document)

    assert chunks == []
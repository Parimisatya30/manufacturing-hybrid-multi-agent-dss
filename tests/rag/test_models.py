from app.rag.models import (
    Document,
    DocumentBlock,
    DocumentChunk,
)


def test_document() -> None:
    document = Document(
        document_id="DOC-001",
        source="Predictive_Maintenance.pdf",
        content="Predictive maintenance reference.",
    )

    assert document.document_id == "DOC-001"
    assert document.source == "Predictive_Maintenance.pdf"
    assert document.content == (
        "Predictive maintenance reference."
    )
    assert document.metadata == {}


def test_document_block_for_text() -> None:
    block = DocumentBlock(
        block_id="DOC-001-BLOCK-001",
        document_id="DOC-001",
        block_type="paragraph",
        content="Machine temperature should remain below the limit.",
        page_number=1,
        section="Operating Limits",
        block_index=0,
    )

    assert block.block_id == "DOC-001-BLOCK-001"
    assert block.document_id == "DOC-001"
    assert block.block_type == "paragraph"
    assert block.page_number == 1
    assert block.section == "Operating Limits"
    assert block.table_data == []


def test_document_block_for_table() -> None:
    block = DocumentBlock(
        block_id="DOC-001-BLOCK-002",
        document_id="DOC-001",
        block_type="table",
        content=(
            "Temperature | <70 | 70-85 | >=85"
        ),
        page_number=1,
        section="Operating Limits",
        block_index=1,
        table_data=[
            {
                "signal": "Temperature",
                "normal": "<70",
                "warning": "70-85",
                "critical": ">=85",
            }
        ],
    )

    assert block.block_type == "table"
    assert block.page_number == 1
    assert block.section == "Operating Limits"

    assert block.table_data[0]["signal"] == "Temperature"
    assert block.table_data[0]["critical"] == ">=85"


def test_document_chunk_preserves_provenance() -> None:
    chunk = DocumentChunk(
        chunk_id="DOC-001-CHUNK-001",
        document_id="DOC-001",
        content=(
            "Operating limits for machine temperature."
        ),
        chunk_index=0,
        block_ids=[
            "DOC-001-BLOCK-001",
            "DOC-001-BLOCK-002",
        ],
        page_numbers=[1],
        sections=["Operating Limits"],
        block_types=["paragraph", "table"],
        topics=["temperature", "operating limits"],
        entities=["Machine"],
        attributes=["Temperature"],
        metrics=[],
        source_id="PREDICTIVE_MAINTENANCE_PDF",
    )

    assert chunk.chunk_id == "DOC-001-CHUNK-001"
    assert chunk.document_id == "DOC-001"

    assert chunk.block_ids == [
        "DOC-001-BLOCK-001",
        "DOC-001-BLOCK-002",
    ]

    assert chunk.page_numbers == [1]
    assert chunk.sections == ["Operating Limits"]

    assert chunk.block_types == [
        "paragraph",
        "table",
    ]

    assert chunk.topics == [
        "temperature",
        "operating limits",
    ]

    assert chunk.entities == ["Machine"]
    assert chunk.attributes == ["Temperature"]
    assert chunk.source_id == (
        "PREDICTIVE_MAINTENANCE_PDF"
    )
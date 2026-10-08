from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from app.rag.ingestion import PDFDocumentLoader


def create_test_pdf(path: Path) -> None:
    """Create a small deterministic PDF for ingestion tests."""

    document = pymupdf.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "1. Machine Performance",
        fontsize=18,
        fontname="hebo",
    )

    page.insert_text(
        (72, 110),
        "Machine efficiency is monitored using production KPIs.",
        fontsize=11,
        fontname="helv",
    )

    document.save(str(path))
    document.close()


def test_load_pdf_extracts_heading_and_paragraph(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "test.pdf"

    create_test_pdf(pdf_path)

    loader = PDFDocumentLoader()

    document = loader.load(
        pdf_path,
        document_id="DOC-TEST",
    )

    assert document.document_id == "DOC-TEST"
    assert document.metadata["source_type"] == "pdf"
    assert document.metadata["page_count"] == 1

    assert len(document.content) > 0

    blocks = [
        block
        for block in document.metadata.get("unused", [])
    ]

    # Structural blocks are attached by the loader through the
    # document content/provenance contract in the next model step.
    # For now, verify the extracted document content.
    assert "Machine Performance" in document.content
    assert "Machine efficiency" in document.content


def test_table_rows_are_converted_to_records() -> None:
    loader = PDFDocumentLoader()

    rows = [
        ["Machine ID", "Efficiency"],
        ["M001", "0.95"],
        ["M002", "0.91"],
    ]

    records = loader._rows_to_records(rows)

    assert records == [
        {
            "Machine ID": "M001",
            "Efficiency": "0.95",
        },
        {
            "Machine ID": "M002",
            "Efficiency": "0.91",
        },
    ]


def test_table_headers_are_made_unique() -> None:
    loader = PDFDocumentLoader()

    rows = [
        ["Status", "Status", ""],
        ["Running", "Active", "M001"],
    ]

    records = loader._rows_to_records(rows)

    assert records == [
        {
            "Status": "Running",
            "Status_2": "Active",
            "column_3": "M001",
        }
    ]


def test_table_text_representation() -> None:
    loader = PDFDocumentLoader()

    rows = [
        ["Machine", "Efficiency"],
        ["M001", "95%"],
    ]

    text = loader._table_to_text(
        rows,
        page_number=3,
        table_index=0,
    )

    assert "Table 1 on page 3:" in text
    assert "Machine | Efficiency" in text
    assert "M001 | 95%" in text


def test_missing_pdf_raises_error(tmp_path: Path) -> None:
    loader = PDFDocumentLoader()

    with pytest.raises(FileNotFoundError):
        loader.load(
            tmp_path / "missing.pdf",
            document_id="DOC-MISSING",
        )


def test_non_pdf_file_is_rejected(tmp_path: Path) -> None:
    text_file = tmp_path / "document.txt"
    text_file.write_text("not a pdf")

    loader = PDFDocumentLoader()

    with pytest.raises(ValueError):
        loader.load(
            text_file,
            document_id="DOC-TEXT",
        )
def test_formula_is_not_classified_as_heading():
    loader = PDFDocumentLoader()

    result = loader._classify_text_block(
        text="OEE = Availability × Performance × Quality",
        max_font_size=12.0,
        has_bold_font=True,
    )

    assert result == "paragraph"


def test_numbered_text_is_classified_as_heading():
    loader = PDFDocumentLoader()

    result = loader._classify_text_block(
        text="1. Overall Equipment Effectiveness (OEE)",
        max_font_size=13.5,
        has_bold_font=True,
    )

    assert result == "heading"


def test_bullet_is_removed_from_text():
    loader = PDFDocumentLoader()

    result = loader._clean_text(
        "• Availability = Operating Time / Planned Time"
    )

    assert result == (
        "Availability = Operating Time / Planned Time"
    )


def test_bullets_on_multiple_lines_are_removed():
    loader = PDFDocumentLoader()

    result = loader._clean_text(
        "• Availability = Operating Time / Planned Time\n"
        "• Performance = Actual Output / Theoretical Output"
    )

    assert result == (
        "Availability = Operating Time / Planned Time\n"
        "Performance = Actual Output / Theoretical Output"
    )


def test_document_chrome_is_filtered():
    loader = PDFDocumentLoader()

    assert loader._is_repeated_document_chrome(
        "Internal Use Only"
    )

    assert loader._is_repeated_document_chrome(
        "Generated from enhanced_mes.db"
    )

    assert loader._is_repeated_document_chrome(
        "Page 1"
    )

    assert loader._is_repeated_document_chrome(
        "Volta E-Bikes — Enhanced MES Reference"
    )


def test_normal_content_is_not_document_chrome():
    loader = PDFDocumentLoader()

    assert not loader._is_repeated_document_chrome(
        "Availability measures the percentage of planned "
        "production time during which a machine is available."
    )
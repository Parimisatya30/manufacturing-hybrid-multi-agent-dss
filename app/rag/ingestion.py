from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf

from app.observability.logging import get_logger
from app.observability.metrics import metrics
from app.rag.models import Document, DocumentBlock


logger = get_logger(__name__)


class PDFDocumentLoader:
    """
    Loads a PDF into a structural document representation.

    This loader is responsible only for document ingestion.

    It does NOT perform:
    - semantic chunking
    - embeddings
    - vector storage
    - retrieval
    - LLM-based interpretation

    The output is a Document containing structural DocumentBlock
    objects such as headings, paragraphs, tables, and figures.
    """

    def load(
        self,
        file_path: str | Path,
        document_id: str | None = None,
    ) -> Document:
        """
        Load a PDF and convert it into a structural Document.

        Parameters
        ----------
        file_path:
            Path to the PDF file.

        document_id:
            Optional stable identifier. If omitted, the filename stem
            is used.

        Returns
        -------
        Document
            Document containing extracted structural blocks.
        """

        path = Path(file_path)

        self._validate_path(path)

        resolved_document_id = document_id or path.stem

        logger.info(
            "Starting PDF ingestion",
            extra={
                "document_id": resolved_document_id,
                "file_name": path.name,
            },
        )

        pdf = pymupdf.open(str(path))

        try:
            blocks: list[DocumentBlock] = []
            block_index = 0

            # Keep the section state across pages.
            #
            # A section can start on one page and continue on the
            # next page without another heading appearing.
            current_section: str | None = None

            for page_number, page in enumerate(pdf, start=1):
                page_candidates = self._extract_page_candidates(
                    page=page,
                    page_number=page_number,
                )

                for candidate in page_candidates:
                    block_type = candidate["block_type"]
                    content = candidate["content"].strip()

                    if not content and block_type != "figure":
                        continue

                    if block_type == "heading":
                        current_section = content

                    block = DocumentBlock(
                        block_id=(
                            f"{resolved_document_id}"
                            f"-BLOCK-{block_index:04d}"
                        ),
                        document_id=resolved_document_id,
                        block_type=block_type,
                        content=content,
                        page_number=page_number,
                        section=current_section,
                        block_index=block_index,
                        table_data=candidate.get("table_data", []),
                        metadata=candidate.get("metadata", {}),
                    )

                    blocks.append(block)
                    block_index += 1

            content_parts = [
                block.content
                for block in blocks
                if block.content
            ]

            document = Document(
                document_id=resolved_document_id,
                source=str(path),
                content="\n\n".join(content_parts),
                blocks=blocks,
                metadata={
                    "file_name": path.name,
                    "file_path": str(path),
                    "source_type": "pdf",
                    "page_count": len(pdf),
                    "block_count": len(blocks),
                },
            )

            metrics.increment("rag_documents_loaded_total")
            metrics.increment(
                "rag_document_blocks_total",
                value=len(blocks),
            )

            logger.info(
                "PDF ingestion completed",
                extra={
                    "document_id": resolved_document_id,
                    "page_count": len(pdf),
                    "block_count": len(blocks),
                },
            )

            return document

        finally:
            pdf.close()

    @staticmethod
    def _validate_path(path: Path) -> None:
        """Validate that the input path is an existing PDF."""

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"PDF path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, received: {path.suffix}"
            )

    def _extract_page_candidates(
        self,
        page: Any,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Extract structural candidates from one PDF page.

        Candidates are sorted by their vertical/horizontal position
        so the original document reading order is approximately
        preserved.
        """

        candidates: list[dict[str, Any]] = []

        table_candidates = self._extract_tables(
            page=page,
            page_number=page_number,
        )

        table_bboxes = [
            candidate["metadata"]["bbox"]
            for candidate in table_candidates
            if candidate.get("metadata", {}).get("bbox")
        ]

        candidates.extend(table_candidates)

        text_candidates = self._extract_text_blocks(
            page=page,
            page_number=page_number,
            table_bboxes=table_bboxes,
        )

        candidates.extend(text_candidates)

        figure_candidates = self._extract_figures(
            page=page,
            page_number=page_number,
        )

        candidates.extend(figure_candidates)

        candidates.sort(
            key=lambda candidate: (
                candidate["metadata"].get(
                    "bbox",
                    (0, 0, 0, 0),
                )[1],
                candidate["metadata"].get(
                    "bbox",
                    (0, 0, 0, 0),
                )[0],
            )
        )

        metrics.increment("rag_pdf_pages_total")

        return candidates

    def _extract_text_blocks(
        self,
        page: Any,
        page_number: int,
        table_bboxes: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Extract text blocks and classify headings vs paragraphs.

        Text normalization and document-chrome filtering happen
        before structural classification.
        """

        page_dict = page.get_text("dict")

        candidates: list[dict[str, Any]] = []

        for raw_block in page_dict.get("blocks", []):
            if raw_block.get("type") != 0:
                continue

            bbox = tuple(
                raw_block.get(
                    "bbox",
                    (0, 0, 0, 0),
                )
            )

            # Avoid adding table text a second time as normal
            # paragraph text.
            if any(
                self._overlap_ratio(bbox, table_bbox) >= 0.50
                for table_bbox in table_bboxes
            ):
                continue

            text, max_font_size, has_bold_font = (
                self._extract_block_text(raw_block)
            )

            text = self._clean_text(text)

            if not text:
                continue

            # Remove repeated document header/footer noise.
            if self._is_repeated_document_chrome(text):
                metrics.increment(
                    "rag_pdf_document_chrome_filtered_total"
                )
                continue

            block_type = self._classify_text_block(
                text=text,
                max_font_size=max_font_size,
                has_bold_font=has_bold_font,
            )

            candidates.append(
                {
                    "block_type": block_type,
                    "content": text,
                    "table_data": [],
                    "metadata": {
                        "bbox": bbox,
                        "page_number": page_number,
                        "max_font_size": max_font_size,
                        "bold": has_bold_font,
                    },
                }
            )

        return candidates

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Normalize extracted PDF text.

        PDF extraction can place bullet characters on their own
        line or directly before the text. Remove those markers
        while preserving the actual content.
        """

        text = text.strip()

        # Remove a bullet at the beginning of a block.
        text = re.sub(
            r"^\s*[•●▪◦]\s*",
            "",
            text,
        )

        # Remove bullet characters that occur at the beginning
        # of subsequent extracted lines.
        text = re.sub(
            r"\n\s*[•●▪◦]\s*",
            "\n",
            text,
        )

        # Normalize excessive whitespace around lines while
        # preserving paragraph line boundaries.
        text = "\n".join(
            line.strip()
            for line in text.splitlines()
            if line.strip()
        )

        return text.strip()

    @staticmethod
    def _extract_block_text(
        raw_block: dict[str, Any],
    ) -> tuple[str, float, bool]:
        """
        Extract text, maximum font size, and bold-font information.
        """

        lines: list[str] = []
        max_font_size = 0.0
        has_bold_font = False

        for line in raw_block.get("lines", []):
            spans = line.get("spans", [])

            line_text = "".join(
                span.get("text", "")
                for span in spans
            )

            if line_text.strip():
                lines.append(line_text.strip())

            for span in spans:
                max_font_size = max(
                    max_font_size,
                    float(span.get("size", 0.0)),
                )

                font_name = span.get(
                    "font",
                    "",
                ).lower()

                if "bold" in font_name:
                    has_bold_font = True

        return (
            "\n".join(lines),
            max_font_size,
            has_bold_font,
        )

    @staticmethod
    def _classify_text_block(
        text: str,
        max_font_size: float,
        has_bold_font: bool,
    ) -> str:
        """
        Classify a text block.

        This is intentionally heuristic.

        We do not use an LLM to determine structural boundaries.

        Heading detection uses:
        - numbered heading patterns
        - sufficiently large font
        - short bold text

        Formula-like text is explicitly prevented from being
        classified as a heading.
        """

        numbered_heading = re.match(
            r"^\s*\d+(?:\.\d+)*[.)]?\s+\S+",
            text,
        )

        large_font = max_font_size >= 15.0

        looks_like_formula = (
            " = " in text
            or "×" in text
        )

        short_bold_heading = (
            has_bold_font
            and len(text) <= 120
            and max_font_size >= 10.5
            and not looks_like_formula
        )

        if (
            large_font
            or numbered_heading
            or short_bold_heading
        ):
            return "heading"

        return "paragraph"

    @staticmethod
    def _is_repeated_document_chrome(
        text: str,
    ) -> bool:
        """
        Detect known document header/footer noise.

        PDF extraction may combine multiple footer lines into a
        single text block, so each extracted line is checked
        independently.
        """

        normalized_lines = [
            " ".join(line.split()).lower()
            for line in text.splitlines()
            if line.strip()
        ]

        if not normalized_lines:
            return False

        known_chrome = {
            "internal use only",
            "generated from enhanced_mes.db",
        }

        for line in normalized_lines:
            if line in known_chrome:
                return True

            if (
                line.startswith("page ")
                and line[5:].isdigit()
            ):
                return True

            if (
                "volta e-bikes" in line
                and "enhanced mes reference" in line
            ):
                return True

        return False

    def _extract_tables(
        self,
        page: Any,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Extract tables using PyMuPDF's table detection API.

        If the installed PyMuPDF version does not expose table
        detection, ingestion continues without failing.
        """

        if not hasattr(page, "find_tables"):
            logger.warning(
                "PyMuPDF table detection is unavailable",
                extra={
                    "page_number": page_number,
                },
            )

            metrics.increment(
                "rag_pdf_table_detection_unavailable_total"
            )

            return []

        try:
            table_finder = page.find_tables()

            tables = getattr(
                table_finder,
                "tables",
                [],
            )

        except Exception as exc:
            logger.warning(
                "Table extraction failed for page",
                extra={
                    "page_number": page_number,
                    "error": str(exc),
                },
            )

            metrics.increment(
                "rag_pdf_table_extraction_errors_total"
            )

            return []

        candidates: list[dict[str, Any]] = []

        for table_index, table in enumerate(tables):
            rows = table.extract()

            if not rows:
                continue

            table_data = self._rows_to_records(rows)

            content = self._table_to_text(
                rows=rows,
                page_number=page_number,
                table_index=table_index,
            )

            bbox = tuple(
                getattr(
                    table,
                    "bbox",
                    (0, 0, 0, 0),
                )
            )

            candidates.append(
                {
                    "block_type": "table",
                    "content": content,
                    "table_data": table_data,
                    "metadata": {
                        "bbox": bbox,
                        "page_number": page_number,
                        "table_index": table_index,
                        "row_count": len(rows),
                        "column_count": (
                            max(
                                len(row)
                                for row in rows
                            )
                            if rows
                            else 0
                        ),
                    },
                }
            )

            metrics.increment(
                "rag_pdf_tables_total"
            )

        return candidates

    @staticmethod
    def _rows_to_records(
        rows: list[list[Any]],
    ) -> list[dict[str, Any]]:
        """
        Convert table rows into structured records.

        The first row is treated as the header row.

        Duplicate and blank headers are normalized so that every
        record has a deterministic set of keys.
        """

        if not rows:
            return []

        raw_headers = rows[0]

        headers: list[str] = []
        used_headers: dict[str, int] = {}

        for index, header in enumerate(raw_headers):
            normalized = str(
                header or ""
            ).strip()

            if not normalized:
                normalized = f"column_{index + 1}"

            count = used_headers.get(
                normalized,
                0,
            )

            if count:
                unique_header = (
                    f"{normalized}_{count + 1}"
                )
            else:
                unique_header = normalized

            used_headers[normalized] = count + 1

            headers.append(unique_header)

        records: list[dict[str, Any]] = []

        for row in rows[1:]:
            record: dict[str, Any] = {}

            for index, header in enumerate(headers):
                value = (
                    row[index]
                    if index < len(row)
                    else None
                )

                if isinstance(value, str):
                    value = value.strip()

                record[header] = value

            records.append(record)

        return records

    @staticmethod
    def _table_to_text(
        rows: list[list[Any]],
        page_number: int,
        table_index: int,
    ) -> str:
        """
        Create a text representation of a table.

        This representation will later be useful for embeddings
        and retrieval while table_data preserves structured values.
        """

        lines = [
            f"Table {table_index + 1} on page {page_number}:"
        ]

        for row in rows:
            values = [
                str(value or "").strip()
                for value in row
            ]

            lines.append(
                " | ".join(values)
            )

        return "\n".join(lines)

    def _extract_figures(
        self,
        page: Any,
        page_number: int,
    ) -> list[dict[str, Any]]:
        """
        Detect images/figures on the page.

        We preserve their existence and provenance but do not yet
        perform visual/semantic interpretation.
        """

        try:
            image_info = page.get_image_info(
                xrefs=True
            )
        except Exception:
            image_info = []

        candidates: list[dict[str, Any]] = []

        for image_index, image in enumerate(
            image_info
        ):
            bbox = tuple(
                image.get(
                    "bbox",
                    (0, 0, 0, 0),
                )
            )

            xref = image.get("xref")

            content = (
                f"Figure/image detected on page "
                f"{page_number}."
            )

            candidates.append(
                {
                    "block_type": "figure",
                    "content": content,
                    "table_data": [],
                    "metadata": {
                        "bbox": bbox,
                        "page_number": page_number,
                        "image_index": image_index,
                        "xref": xref,
                        "width": image.get("width"),
                        "height": image.get("height"),
                    },
                }
            )

            metrics.increment(
                "rag_pdf_images_total"
            )

        return candidates

    @staticmethod
    def _overlap_ratio(
        first_bbox: tuple[
            float,
            float,
            float,
            float,
        ],
        second_bbox: tuple[
            float,
            float,
            float,
            float,
        ],
    ) -> float:
        """
        Return the fraction of the first box covered by the second.
        """

        (
            first_x0,
            first_y0,
            first_x1,
            first_y1,
        ) = first_bbox

        (
            second_x0,
            second_y0,
            second_x1,
            second_y1,
        ) = second_bbox

        intersection_x0 = max(
            first_x0,
            second_x0,
        )

        intersection_y0 = max(
            first_y0,
            second_y0,
        )

        intersection_x1 = min(
            first_x1,
            second_x1,
        )

        intersection_y1 = min(
            first_y1,
            second_y1,
        )

        if (
            intersection_x1 <= intersection_x0
            or intersection_y1 <= intersection_y0
        ):
            return 0.0

        intersection_area = (
            (intersection_x1 - intersection_x0)
            * (intersection_y1 - intersection_y0)
        )

        first_area = (
            max(
                0.0,
                first_x1 - first_x0,
            )
            * max(
                0.0,
                first_y1 - first_y0,
            )
        )

        if first_area == 0:
            return 0.0

        return intersection_area / first_area
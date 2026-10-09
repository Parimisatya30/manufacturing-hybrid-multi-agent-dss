from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.chunking import SemanticChunker

from app.rag.ingestion import PDFDocumentLoader


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_pdf.py <pdf_path>")
        raise SystemExit(1)

    pdf_path = Path(sys.argv[1])

    loader = PDFDocumentLoader()

    document = loader.load(
        pdf_path,
        document_id=pdf_path.stem,
    )

    print("=" * 80)
    print("DOCUMENT")
    print("=" * 80)

    print(f"Document ID : {document.document_id}")
    print(f"Source      : {document.source}")
    print(f"Pages       : {document.metadata.get('page_count')}")
    print(f"Blocks      : {len(document.blocks)}")

    print()

    for block in document.blocks:
        print("-" * 80)
        print(f"Block ID    : {block.block_id}")
        print(f"Type        : {block.block_type}")
        print(f"Page        : {block.page_number}")
        print(f"Section     : {block.section}")
        print(f"Index       : {block.block_index}")

        if block.block_type == "table":
            print(f"Rows        : {len(block.table_data)}")
            print(f"Table data  : {block.table_data}")

        print("Content:")
        print(block.content[:1000])

        if block.metadata:
            print("Metadata:")
            print(block.metadata)

        print("\n" + "=" * 80)
    print("SEMANTIC CHUNKS")
    print("=" * 80)

    chunks = SemanticChunker().chunk(document)

    print(f"Total chunks: {len(chunks)}")

    for chunk in chunks:
        print("\n" + "-" * 80)
        print(f"Chunk ID    : {chunk.chunk_id}")
        print(f"Chunk index : {chunk.chunk_index}")
        print(f"Block IDs   : {chunk.block_ids}")
        print(f"Pages       : {chunk.page_numbers}")
        print(f"Sections    : {chunk.sections}")
        print(f"Block types : {chunk.block_types}")
        print("Content:")
        print(chunk.content[:2000])

if __name__ == "__main__":
    main()

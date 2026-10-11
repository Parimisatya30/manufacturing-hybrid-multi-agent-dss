
"""Inspect actual RAG results to prepare evaluation labels."""

from pathlib import Path

from app.rag.knowledge_base import KnowledgeBaseService


DOCUMENTS_DIR = Path("data/raw/documents")

QUERIES = [
    "What are the warning and critical vibration thresholds?",
    "How should active predictive maintenance alerts be triaged?",
    "What is the plant-wide OEE and which machines have the lowest OEE?",
    "How should material defects be investigated and contained?",
    "What are the first-pass yield targets and escalation thresholds?",
]


def main() -> None:
    knowledge_base = KnowledgeBaseService()

    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {DOCUMENTS_DIR}")

    for pdf_path in pdf_files:
        count = knowledge_base.index_pdf(pdf_path)
        print(f"Indexed {pdf_path.name}: {count} chunks")

    print("\n=== RETRIEVAL RESULTS ===")

    for query in QUERIES:
        print(f"\nQuery: {query}")

        results = knowledge_base.search(query, top_k=3)

        if not results:
            print("  No results returned.")
            continue

        for rank, result in enumerate(results, start=1):
            chunk = result.chunk
            print(
                f"\n  Rank: {rank}"
                f"\n  Chunk ID: {chunk.chunk_id}"
                f"\n  Document ID: {chunk.document_id}"
                f"\n  Score: {result.score:.4f}"
                f"\n  Content: {chunk.content[:700]}"
            )


if __name__ == "__main__":
    main()
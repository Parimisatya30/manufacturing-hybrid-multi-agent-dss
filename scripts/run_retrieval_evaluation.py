
"""Run retrieval evaluation against the manufacturing PDF knowledge base."""

import json
from pathlib import Path

from app.evaluation.retrieval_runner import (
    RetrievalEvaluationCase,
    RetrievalEvaluationRunner,
)
from app.rag.knowledge_base import KnowledgeBaseService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "raw" / "documents"
EVALUATION_FILE = (
    PROJECT_ROOT / "data" / "processed" / "retrieval_evaluation.json"
)


def main() -> None:
    """Index source PDFs and calculate retrieval evaluation metrics."""
    with EVALUATION_FILE.open("r", encoding="utf-8") as file:
        evaluation_data = json.load(file)

    cases = [
        RetrievalEvaluationCase(
            query=item["query"],
            relevant_chunk_ids=frozenset(item["relevant_chunk_ids"]),
        )
        for item in evaluation_data
    ]

    knowledge_base = KnowledgeBaseService()

    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {DOCUMENTS_DIR}")

    for pdf_path in pdf_files:
        count = knowledge_base.index_pdf(pdf_path)
        print(f"Indexed {pdf_path.name}: {count} chunks")

    runner = RetrievalEvaluationRunner(knowledge_base.pipeline)
    summary = runner.evaluate(cases, top_k=3)

    print("\n=== RETRIEVAL EVALUATION ===")

    for result in summary.results:
        print(f"\nQuery: {result.query}")
        print(f"Retrieved chunk IDs: {list(result.retrieved_chunk_ids)}")
        print(f"Recall@3: {result.recall:.3f}")
        print(f"Precision@3: {result.precision:.3f}")
        print(f"Reciprocal Rank: {result.reciprocal_rank:.3f}")

    print("\n=== AGGREGATE METRICS ===")
    print(f"Mean Recall@3: {summary.mean_recall:.3f}")
    print(f"Mean Precision@3: {summary.mean_precision:.3f}")
    print(f"Mean Reciprocal Rank (MRR): {summary.mean_reciprocal_rank:.3f}")


if __name__ == "__main__":
    main()
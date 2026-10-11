
"""Run retrieval evaluations against a configured RAG retriever."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.evaluation.metrics import (
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    """A query and the chunk IDs known to be relevant to it."""

    query: str
    relevant_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class RetrievalEvaluationResult:
    """Metrics calculated for one evaluation query."""

    query: str
    retrieved_chunk_ids: tuple[str, ...]
    recall: float
    precision: float
    reciprocal_rank: float


@dataclass(frozen=True)
class RetrievalEvaluationSummary:
    """Aggregate metrics across evaluation queries."""

    results: tuple[RetrievalEvaluationResult, ...]
    mean_recall: float
    mean_precision: float
    mean_reciprocal_rank: float


class RetrievalEvaluationRunner:
    """Evaluate a retriever without depending on its concrete implementation."""

    def __init__(self, retriever: object) -> None:
        self.retriever = retriever

    def evaluate(
        self,
        cases: Sequence[RetrievalEvaluationCase],
        top_k: int = 3,
    ) -> RetrievalEvaluationSummary:
        """Run queries and calculate per-query and aggregate metrics."""

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        if not cases:
            raise ValueError("At least one evaluation case is required")

        results: list[RetrievalEvaluationResult] = []

        for case in cases:
            if not case.query.strip():
                raise ValueError("Evaluation queries must not be blank")

            if not case.relevant_chunk_ids:
                raise ValueError(
                    f"Relevant chunk IDs are required for query: {case.query}"
                )

            search_results = self.retriever.retrieve(
                case.query,
                top_k=top_k,
            )

            retrieved_ids = tuple(
                result.chunk.chunk_id for result in search_results
            )

            relevant_ids = set(case.relevant_chunk_ids)

            results.append(
                RetrievalEvaluationResult(
                    query=case.query,
                    retrieved_chunk_ids=retrieved_ids,
                    recall=recall_at_k(retrieved_ids, relevant_ids, top_k),
                    precision=precision_at_k(
                        retrieved_ids, relevant_ids, top_k
                    ),
                    reciprocal_rank=mean_reciprocal_rank(
                        retrieved_ids, relevant_ids
                    ),
                )
            )

        count = len(results)

        return RetrievalEvaluationSummary(
            results=tuple(results),
            mean_recall=sum(item.recall for item in results) / count,
            mean_precision=sum(item.precision for item in results) / count,
            mean_reciprocal_rank=(
                sum(item.reciprocal_rank for item in results) / count
            ),
        )
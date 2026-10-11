
"""Deterministic evaluation metrics for information retrieval."""

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def recall_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: set[T],
    k: int,
) -> float:
    """Return the fraction of relevant documents found in the top k."""

    if k <= 0:
        raise ValueError("k must be greater than zero")

    if not relevant_ids:
        return 0.0

    retrieved = set(retrieved_ids[:k])
    return len(retrieved & relevant_ids) / len(relevant_ids)


def precision_at_k(
    retrieved_ids: Sequence[T],
    relevant_ids: set[T],
    k: int,
) -> float:
    """Return the fraction of top-k results that are relevant.

    Missing result positions count as non-relevant.
    Duplicate retrieved IDs count only once as relevant.
    """

    if k <= 0:
        raise ValueError("k must be greater than zero")

    retrieved = retrieved_ids[:k]
    relevant_count = len(set(retrieved) & relevant_ids)
    return relevant_count / k


def mean_reciprocal_rank(
    retrieved_ids: Sequence[T],
    relevant_ids: set[T],
) -> float:
    """Return the reciprocal rank of the first relevant result.

    Returns zero when no relevant result is retrieved.
    """

    for rank, document_id in enumerate(retrieved_ids, start=1):
        if document_id in relevant_ids:
            return 1.0 / rank

    return 0.0

import pytest

from app.evaluation.metrics import (
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)


def test_recall_at_k_counts_relevant_documents_found():
    retrieved = ["doc-1", "doc-3", "doc-5"]
    relevant = {"doc-1", "doc-2", "doc-3", "doc-4"}

    assert recall_at_k(retrieved, relevant, k=3) == pytest.approx(0.5)


def test_precision_at_k_counts_relevant_results():
    retrieved = ["doc-1", "doc-3", "doc-5"]
    relevant = {"doc-1", "doc-2", "doc-3"}

    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(2 / 3)


def test_precision_at_k_counts_missing_positions_as_non_relevant():
    retrieved = ["doc-1"]
    relevant = {"doc-1"}

    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(1 / 3)


def test_recall_at_k_returns_zero_when_no_relevant_documents_exist():
    assert recall_at_k(["doc-1"], set(), k=1) == 0.0


def test_mrr_uses_rank_of_first_relevant_document():
    retrieved = ["doc-1", "doc-2", "doc-3"]
    relevant = {"doc-2", "doc-3"}

    assert mean_reciprocal_rank(retrieved, relevant) == pytest.approx(0.5)


def test_mrr_returns_zero_when_no_relevant_document_is_found():
    assert mean_reciprocal_rank(["doc-1", "doc-2"], {"doc-3"}) == 0.0


@pytest.mark.parametrize(
    "metric",
    [recall_at_k, precision_at_k],
)
def test_metrics_reject_nonpositive_k(metric):
    with pytest.raises(ValueError, match="k must be greater than zero"):
        metric(["doc-1"], {"doc-1"}, k=0)
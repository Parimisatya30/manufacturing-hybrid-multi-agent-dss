
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.evaluation.retrieval_runner import (
    RetrievalEvaluationCase,
    RetrievalEvaluationRunner,
)


def make_result(chunk_id: str):
    return SimpleNamespace(
        chunk=SimpleNamespace(chunk_id=chunk_id),
        score=0.9,
    )


def test_runner_calculates_metrics_from_actual_retriever_results():
    retriever = Mock()
    retriever.retrieve.return_value = [
        make_result("vibration-1"),
        make_result("maintenance-1"),
        make_result("quality-1"),
    ]

    runner = RetrievalEvaluationRunner(retriever)
    cases = [
        RetrievalEvaluationCase(
            query="What indicates vibration anomalies?",
            relevant_chunk_ids=frozenset({"vibration-1", "vibration-2"}),
        )
    ]

    summary = runner.evaluate(cases, top_k=3)

    retriever.retrieve.assert_called_once_with(
        "What indicates vibration anomalies?",
        top_k=3,
    )

    assert summary.results[0].retrieved_chunk_ids == (
        "vibration-1",
        "maintenance-1",
        "quality-1",
    )
    assert summary.results[0].recall == 0.5
    assert summary.results[0].precision == pytest.approx(1 / 3)
    assert summary.results[0].reciprocal_rank == 1.0
    assert summary.mean_recall == 0.5
    assert summary.mean_precision == pytest.approx(1 / 3)
    assert summary.mean_reciprocal_rank == 1.0


def test_runner_rejects_nonpositive_top_k():
    runner = RetrievalEvaluationRunner(Mock())

    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        runner.evaluate(
            [
                RetrievalEvaluationCase(
                    query="Machine vibration",
                    relevant_chunk_ids=frozenset({"vibration-1"}),
                )
            ],
            top_k=0,
        )


def test_runner_rejects_empty_evaluation_dataset():
    runner = RetrievalEvaluationRunner(Mock())

    with pytest.raises(ValueError, match="At least one evaluation case"):
        runner.evaluate([])


def test_runner_rejects_blank_queries():
    runner = RetrievalEvaluationRunner(Mock())

    with pytest.raises(ValueError, match="must not be blank"):
        runner.evaluate(
            [
                RetrievalEvaluationCase(
                    query=" ",
                    relevant_chunk_ids=frozenset({"vibration-1"}),
                )
            ]
        )


def test_runner_rejects_cases_without_relevant_chunks():
    runner = RetrievalEvaluationRunner(Mock())

    with pytest.raises(ValueError, match="Relevant chunk IDs are required"):
        runner.evaluate(
            [
                RetrievalEvaluationCase(
                    query="Machine vibration",
                    relevant_chunk_ids=frozenset(),
                )
            ]
        )

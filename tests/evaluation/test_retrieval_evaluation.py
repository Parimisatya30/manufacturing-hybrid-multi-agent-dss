
from app.evaluation.metrics import (
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)


EVALUATION_CASES = [
    {
        "query": "What indicates a machine vibration anomaly?",
        "retrieved_ids": ["vibration-guide", "maintenance-guide", "quality-guide"],
        "relevant_ids": {"vibration-guide"},
    },
    {
        "query": "How should machine downtime be investigated?",
        "retrieved_ids": ["quality-guide", "downtime-guide", "maintenance-guide"],
        "relevant_ids": {"downtime-guide", "maintenance-guide"},
    },
    {
        "query": "How are manufacturing defects recorded?",
        "retrieved_ids": ["quality-guide", "vibration-guide", "downtime-guide"],
        "relevant_ids": {"quality-guide"},
    },
]


def test_evaluation_dataset_has_queries_and_relevance_labels():
    assert EVALUATION_CASES

    for case in EVALUATION_CASES:
        assert case["query"].strip()
        assert case["retrieved_ids"]
        assert case["relevant_ids"]


def test_retrieval_metrics_for_vibration_query():
    case = EVALUATION_CASES[0]

    assert recall_at_k(
        case["retrieved_ids"], case["relevant_ids"], k=3
    ) == 1.0
    assert precision_at_k(
        case["retrieved_ids"], case["relevant_ids"], k=3
    ) == 1 / 3
    assert mean_reciprocal_rank(
        case["retrieved_ids"], case["relevant_ids"]
    ) == 1.0


def test_retrieval_metrics_for_downtime_query():
    case = EVALUATION_CASES[1]

    assert recall_at_k(
        case["retrieved_ids"], case["relevant_ids"], k=3
    ) == 1.0
    assert precision_at_k(
        case["retrieved_ids"], case["relevant_ids"], k=3
    ) == 2 / 3
    assert mean_reciprocal_rank(
        case["retrieved_ids"], case["relevant_ids"]
    ) == 0.5
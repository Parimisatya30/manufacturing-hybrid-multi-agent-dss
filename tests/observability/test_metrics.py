from app.observability.metrics import Metrics


def test_increment_counter() -> None:
    metrics = Metrics()

    metrics.increment("requests_total")
    metrics.increment("requests_total")

    result = metrics.snapshot()

    assert result["counters"]["requests_total"] == 2


def test_observe_timing() -> None:
    metrics = Metrics()

    metrics.observe("query_duration_ms", 20.0)
    metrics.observe("query_duration_ms", 30.0)

    result = metrics.snapshot()

    timing = result["timings"]["query_duration_ms"]

    assert timing["count"] == 2
    assert timing["total_ms"] == 50.0
    assert timing["average_ms"] == 25.0


def test_timer_records_duration() -> None:
    import time

    metrics = Metrics()

    with metrics.timer("operation_duration_ms"):
        time.sleep(0.01)

    result = metrics.snapshot()

    timing = result["timings"]["operation_duration_ms"]

    assert timing["count"] == 1
    assert timing["total_ms"] > 0
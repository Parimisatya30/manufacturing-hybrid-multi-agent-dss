from collections import defaultdict
from contextlib import contextmanager
from threading import Lock
from time import perf_counter
from typing import Iterator


class Metrics:
    """Centralized in-process application metrics."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._timings: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value

    def observe(self, name: str, value: float) -> None:
        """Record a numeric observation."""
        with self._lock:
            self._timings[name].append(value)

    @contextmanager
    def timer(self, name: str) -> Iterator[None]:
        """Measure execution time in milliseconds."""
        start = perf_counter()

        try:
            yield
        finally:
            duration_ms = (perf_counter() - start) * 1000
            self.observe(name, duration_ms)

    def snapshot(self) -> dict[str, dict[str, object]]:
        """Return a snapshot of all collected metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timings": {
                    name: {
                        "count": len(values),
                        "total_ms": sum(values),
                        "average_ms": (
                            sum(values) / len(values)
                            if values
                            else 0.0
                        ),
                    }
                    for name, values in self._timings.items()
                },
            }


metrics = Metrics()
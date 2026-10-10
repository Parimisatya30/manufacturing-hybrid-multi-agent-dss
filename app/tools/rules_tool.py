"""Deterministic manufacturing rules evaluation."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleThreshold:
    """Warning and critical thresholds for a manufacturing metric."""

    metric: str
    warning: float
    critical: float
    unit: str = ""


class RulesTool:
    """Evaluate manufacturing metrics against configured thresholds."""

    def __init__(
        self,
        thresholds: dict[str, RuleThreshold] | None = None,
    ) -> None:
        self.thresholds = thresholds or {
            "vibration": RuleThreshold(
                metric="vibration",
                warning=7.0,
                critical=10.0,
                unit="mm/s",
            ),
            "defect_rate": RuleThreshold(
                metric="defect_rate",
                warning=2.0,
                critical=5.0,
                unit="%",
            ),
            "oee": RuleThreshold(
                metric="oee",
                warning=60.0,
                critical=40.0,
                unit="%",
            ),
        }

    def evaluate(
        self,
        metric: str,
        value: float,
    ) -> dict[str, Any]:
        """Evaluate a metric and return its status and explanation."""
        if metric not in self.thresholds:
            raise ValueError(f"Unknown manufacturing metric: {metric}")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Metric value must be numeric")

        threshold = self.thresholds[metric]

        if metric == "oee":
            if value <= threshold.critical:
                status = "CRITICAL"
            elif value <= threshold.warning:
                status = "WARNING"
            else:
                status = "NORMAL"
        else:
            if value >= threshold.critical:
                status = "CRITICAL"
            elif value >= threshold.warning:
                status = "WARNING"
            else:
                status = "NORMAL"

        return {
            "metric": metric,
            "value": value,
            "unit": threshold.unit,
            "status": status,
            "warning_threshold": threshold.warning,
            "critical_threshold": threshold.critical,
            "reason": self._build_reason(
                metric=metric,
                value=value,
                status=status,
                threshold=threshold,
            ),
        }

    @staticmethod
    def _build_reason(
        metric: str,
        value: float,
        status: str,
        threshold: RuleThreshold,
    ) -> str:
        """Explain the deterministic rule outcome."""
        if status == "NORMAL":
            return f"{metric} value {value} is within the normal range."

        if status == "WARNING":
            return (
                f"{metric} value {value} reached the warning threshold "
                f"of {threshold.warning}{threshold.unit}."
            )

        return (
            f"{metric} value {value} reached the critical threshold "
            f"of {threshold.critical}{threshold.unit}."
        )
import pytest

from app.tools.rules_tool import RuleThreshold, RulesTool


@pytest.mark.parametrize(
    ("metric", "value", "expected"),
    [
        ("vibration", 5.0, "NORMAL"),
        ("vibration", 7.0, "WARNING"),
        ("vibration", 10.0, "CRITICAL"),
        ("defect_rate", 1.0, "NORMAL"),
        ("defect_rate", 2.0, "WARNING"),
        ("defect_rate", 5.0, "CRITICAL"),
        ("oee", 80.0, "NORMAL"),
        ("oee", 60.0, "WARNING"),
        ("oee", 40.0, "CRITICAL"),
    ],
)
def test_evaluate_metric_thresholds(metric, value, expected):
    result = RulesTool().evaluate(metric, value)

    assert result["status"] == expected
    assert result["metric"] == metric
    assert "reason" in result


def test_unknown_metric_is_rejected():
    with pytest.raises(ValueError, match="Unknown manufacturing metric"):
        RulesTool().evaluate("temperature", 80.0)


@pytest.mark.parametrize("value", [True, "10", None])
def test_non_numeric_metric_value_is_rejected(value):
    with pytest.raises(TypeError, match="must be numeric"):
        RulesTool().evaluate("vibration", value)


def test_custom_thresholds_are_supported():
    rules = RulesTool(
        thresholds={
            "temperature": RuleThreshold(
                metric="temperature",
                warning=70.0,
                critical=90.0,
                unit="C",
            )
        }
    )

    result = rules.evaluate("temperature", 75.0)

    assert result["status"] == "WARNING"
    assert result["warning_threshold"] == 70.0
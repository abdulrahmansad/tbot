import json

from tbot.calibration_status import evaluate_calibration_readiness


def write_summary(path, **overrides):
    payload = {
        "schema_version": 2,
        "risk_model": "structural_rejection_plus_median20_range_floor",
        "bars_requested": 2000,
        "timeframes": [
            {
                "independent_event_count": 67,
                "primary_outcomes": {"AMBIGUOUS": 0},
            },
            {
                "independent_event_count": 73,
                "primary_outcomes": {"AMBIGUOUS": 1},
            },
            {
                "independent_event_count": 75,
                "primary_outcomes": {"AMBIGUOUS": 1},
            },
        ],
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_readiness_accepts_current_validation_shape(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path)

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is True
    assert result.primary_events == 215
    assert result.ambiguous_primary_events == 2


def test_readiness_rejects_short_sample(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path, bars_requested=1000)

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is False
    assert "insufficient_history_bars" in result.reasons


def test_readiness_does_not_use_performance_as_gate(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(
        path,
        timeframes=[
            {
                "independent_event_count": 150,
                "primary_outcomes": {"INVALIDATED": 150},
            }
        ],
    )

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is True

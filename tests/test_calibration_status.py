import json

from tbot.calibration_status import evaluate_calibration_readiness


def write_summary(path, **overrides):
    payload = {
        "schema_version": 3,
        "strategy_contract_version": "owner-flip-dip-2026-09-19",
        "risk_model": "structural_rejection_plus_median20_range_floor",
        "execution_model": "distinct_retest_episodes_with_correct_side_rearm",
        "primary_entry_timeframes": ["5M", "15M"],
        "max_executions_per_zone": 3,
        "partial_tp_owner_configured": False,
        "bars_requested": 2000,
        "timeframes": [
            {
                "entry_timeframe": "5M",
                "independent_event_count": 80,
                "primary_outcomes": {"AMBIGUOUS": 1},
                "news_filter_applied": True,
            },
            {
                "entry_timeframe": "15M",
                "independent_event_count": 80,
                "primary_outcomes": {"AMBIGUOUS": 1},
                "news_filter_applied": True,
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
    assert result.primary_events == 160
    assert result.ambiguous_primary_events == 2


def test_readiness_rejects_short_sample(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path, bars_requested=1000)

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is False
    assert "insufficient_history_bars" in result.reasons


def test_readiness_rejects_old_contract_schema(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(path, schema_version=2)

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is False
    assert "unsupported_calibration_schema" in result.reasons


def test_readiness_does_not_use_performance_as_gate(tmp_path):
    path = tmp_path / "summary.json"
    write_summary(
        path,
        timeframes=[
            {
                "entry_timeframe": "5M",
                "independent_event_count": 75,
                "primary_outcomes": {"INVALIDATED": 75},
                "news_filter_applied": True,
            },
            {
                "entry_timeframe": "15M",
                "independent_event_count": 75,
                "primary_outcomes": {"INVALIDATED": 75},
                "news_filter_applied": True,
            },
        ],
    )

    result = evaluate_calibration_readiness(path)

    assert result.ready_for_forward_demo is True

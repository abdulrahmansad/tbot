from datetime import datetime, timedelta, timezone

from tbot.runtime_status import evaluate_worker_snapshot


NOW = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)


def test_missing_worker_snapshot():
    result = evaluate_worker_snapshot({}, now=NOW)

    assert result.status == "missing"
    assert result.fresh is False


def test_fresh_worker_snapshot():
    result = evaluate_worker_snapshot(
        {"scanned_at": (NOW - timedelta(seconds=60)).isoformat()},
        now=NOW,
    )

    assert result.status == "fresh"
    assert result.fresh is True
    assert result.age_seconds == 60.0


def test_stale_worker_snapshot():
    result = evaluate_worker_snapshot(
        {"scanned_at": (NOW - timedelta(minutes=5)).isoformat()},
        now=NOW,
    )

    assert result.status == "stale"
    assert result.fresh is False


def test_clock_skew_is_not_fresh():
    result = evaluate_worker_snapshot(
        {"scanned_at": (NOW + timedelta(minutes=5)).isoformat()},
        now=NOW,
    )

    assert result.status == "clock_skew"
    assert result.fresh is False

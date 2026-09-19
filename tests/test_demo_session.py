from datetime import datetime, timedelta, timezone

from tbot.demo_session import DemoSession, DemoSessionStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_demo_session_status_transitions(tmp_path):
    store = DemoSessionStore(tmp_path / "session.json")
    store.write(
        DemoSession(
            name="Week 1",
            start=START + timedelta(hours=1),
            end=START + timedelta(days=1),
        )
    )

    assert store.describe(now=START)["status"] == "SCHEDULED"
    assert store.describe(now=START + timedelta(hours=2))["status"] == "ACTIVE"
    assert store.describe(now=START + timedelta(days=2))["status"] == "ENDED"


def test_unconfigured_demo_session_is_unbounded(tmp_path):
    store = DemoSessionStore(tmp_path / "missing.json")
    result = store.describe(now=START)
    assert result["configured"] is False
    assert result["status"] == "UNBOUNDED"

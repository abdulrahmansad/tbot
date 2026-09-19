from datetime import datetime, timedelta, timezone

from tbot.news import EconomicEvent, Impact
from tbot.news_cache import CachedEconomicCalendarProvider


START = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)


class Upstream:
    def __init__(self):
        self.calls = 0

    def fetch_events(self, *, start, end):
        self.calls += 1
        return [
            EconomicEvent(
                title="CPI",
                scheduled_at=START + timedelta(minutes=30),
                impact=Impact.HIGH,
                currency="USD",
            )
        ]


def test_calendar_cache_reuses_nearby_poll():
    upstream = Upstream()
    now = [START]
    provider = CachedEconomicCalendarProvider(
        upstream,
        ttl_minutes=15,
        padding_minutes=60,
        now_fn=lambda: now[0],
    )

    first = provider.fetch_events(
        start=START - timedelta(hours=2),
        end=START + timedelta(hours=2),
    )
    now[0] = START + timedelta(minutes=5)
    second = provider.fetch_events(
        start=START - timedelta(hours=2) + timedelta(minutes=5),
        end=START + timedelta(hours=2) + timedelta(minutes=5),
    )

    assert upstream.calls == 1
    assert first
    assert second


def test_calendar_cache_refreshes_after_ttl():
    upstream = Upstream()
    now = [START]
    provider = CachedEconomicCalendarProvider(
        upstream,
        ttl_minutes=15,
        padding_minutes=60,
        now_fn=lambda: now[0],
    )

    provider.fetch_events(
        start=START - timedelta(hours=2),
        end=START + timedelta(hours=2),
    )
    now[0] = START + timedelta(minutes=16)
    provider.fetch_events(
        start=START - timedelta(hours=2),
        end=START + timedelta(hours=2),
    )

    assert upstream.calls == 2

from datetime import datetime, timezone

from tbot.fallback_calendar import FallbackEconomicCalendarProvider
from tbot.news import EconomicEvent, Impact


NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)


class Broken:
    def fetch_events(self, *, start, end):
        raise RuntimeError("payment required")


class Working:
    def fetch_events(self, *, start, end):
        return [
            EconomicEvent(
                title="US CPI",
                scheduled_at=NOW,
                impact=Impact.HIGH,
                currency="USD",
                xauusd_relevant=True,
            )
        ]


def test_fallback_calendar_uses_next_provider_after_failure():
    provider = FallbackEconomicCalendarProvider([Broken(), Working()])

    events = provider.fetch_events(start=NOW, end=NOW)

    assert len(events) == 1
    assert provider.last_provider_name == "Working"
    assert provider.last_error is None


def test_fallback_calendar_records_failures_before_success():
    provider = FallbackEconomicCalendarProvider([Broken(), Working()])

    provider.fetch_events(start=NOW, end=NOW)

    assert provider.last_provider_name == "Working"
    assert provider.last_failures
    assert "payment required" in provider.last_failures[0]

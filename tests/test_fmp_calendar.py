import json
from datetime import datetime, timezone

import pytest

from tbot.fmp_calendar import FmpEconomicCalendarProvider
from tbot.news import Impact


def fake_get(url: str, api_key: str) -> bytes:
    assert "from=2026-09-19" in url
    assert "to=2026-09-19" in url
    assert api_key == "test-key"
    return json.dumps(
        [
            {
                "date": "2026-09-19 12:30:00",
                "country": "United States",
                "event": "CPI",
                "impact": "High",
            },
            {
                "date": "2026-09-19 14:00:00",
                "country": "Germany",
                "event": "Other",
                "impact": "Low",
                "currency": "EUR",
            },
        ]
    ).encode()


def test_fmp_calendar_normalizes_utc_usd_event():
    provider = FmpEconomicCalendarProvider("test-key", http_get=fake_get)
    start = datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 9, 19, 23, 59, tzinfo=timezone.utc)

    events = provider.fetch_events(start=start, end=end)

    assert len(events) == 2
    assert events[0].title == "CPI"
    assert events[0].currency == "USD"
    assert events[0].impact is Impact.HIGH
    assert events[0].scheduled_at.tzinfo is not None


def test_fmp_calendar_requires_key(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    with pytest.raises(ValueError):
        FmpEconomicCalendarProvider(api_key="")

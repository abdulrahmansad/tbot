import json
from datetime import datetime, timezone

from tbot.finance_calendar import FinanceCalendarProvider


START = datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 20, 23, 59, tzinfo=timezone.utc)


def test_finance_calendar_keeps_only_high_impact_us_events():
    payload = {
        "events": [
            {
                "title": "US CPI Report September 2026",
                "name": "US CPI",
                "time_utc": "2026-09-19T12:30:00+00:00",
                "impact": "high",
                "category": "economic-indicators",
            },
            {
                "title": "UK GDP September 2026",
                "name": "UK GDP",
                "time_utc": "2026-09-19T06:00:00+00:00",
                "impact": "high",
                "category": "economic-indicators",
            },
            {
                "title": "US Trade Balance",
                "name": "US Trade Balance",
                "time_utc": "2026-09-19T13:30:00+00:00",
                "impact": "medium",
                "category": "economic-indicators",
            },
        ]
    }
    provider = FinanceCalendarProvider(
        http_get=lambda url: json.dumps(payload).encode("utf-8")
    )

    events = provider.fetch_events(start=START, end=END)

    assert len(events) == 1
    assert events[0].currency == "USD"
    assert events[0].title == "US CPI Report September 2026"


def test_finance_calendar_accepts_fomc_without_us_prefix():
    payload = {
        "events": [
            {
                "title": "FOMC Rate Decision September 2026",
                "name": "FOMC decision",
                "time_utc": "2026-09-19T18:00:00+00:00",
                "impact": "high",
                "category": "central-banks-monetary-policy",
            }
        ]
    }
    provider = FinanceCalendarProvider(
        http_get=lambda url: json.dumps(payload).encode("utf-8")
    )

    events = provider.fetch_events(start=START, end=END)

    assert len(events) == 1
    assert events[0].currency == "USD"

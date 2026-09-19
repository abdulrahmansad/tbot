import json
from datetime import datetime, timezone

from tbot.xoomar_calendar import XoomarEconomicCalendarProvider


START = datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 20, 23, 59, tzinfo=timezone.utc)


def test_xoomar_parses_high_impact_us_event():
    payload = {
        "data": [
            {
                "eventName": "US CPI",
                "scheduledAt": "2026-09-19T12:30:00Z",
                "importance": "high",
                "source": "bls",
            }
        ],
        "updatedAt": "2026-09-19T10:00:00Z",
    }
    provider = XoomarEconomicCalendarProvider(
        http_get=lambda url: json.dumps(payload).encode("utf-8")
    )

    events = provider.fetch_events(start=START, end=END)

    assert len(events) == 1
    assert events[0].title == "US CPI"
    assert events[0].currency == "USD"

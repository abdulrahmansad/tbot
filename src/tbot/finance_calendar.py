from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .news import EconomicEvent, Impact


class FinanceCalendarError(RuntimeError):
    pass


def _default_get(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.financecalendar.com/",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_us_relevant(item: dict) -> bool:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("name", "title", "series", "category")
    ).lower()
    explicit_us = (
        text.startswith("us ")
        or " united states" in text
        or "fomc" in text
        or "federal reserve" in text
        or "fed rate" in text
    )
    return explicit_us


class FinanceCalendarProvider:
    """Free high-impact economic-calendar fallback.

    Source: financecalendar.com. The service requires visible attribution when
    its data is displayed.
    """

    base_url = "https://www.financecalendar.com/wp-json/fc/v1/calendar"
    attribution_url = "https://www.financecalendar.com"

    def __init__(self, *, http_get: Callable[[str], bytes] = _default_get) -> None:
        self.http_get = http_get

    def fetch_events(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[EconomicEvent]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("start/end must be timezone-aware")
        if end < start:
            raise ValueError("end must be on or after start")

        params = {
            "from": start.astimezone(timezone.utc).strftime("%Y-%m-%d"),
            "to": end.astimezone(timezone.utc).strftime("%Y-%m-%d"),
            "impact": "high",
            "limit": 500,
        }
        payload = json.loads(
            self.http_get(f"{self.base_url}?{urlencode(params)}").decode("utf-8")
        )

        if isinstance(payload, dict):
            raw_events = payload.get("events")
            if raw_events is None:
                raw_events = payload.get("data")
        elif isinstance(payload, list):
            raw_events = payload
        else:
            raw_events = None

        if not isinstance(raw_events, list):
            raise FinanceCalendarError(
                "FinanceCalendar response did not contain an event list"
            )

        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)
        events: list[EconomicEvent] = []

        for item in raw_events:
            if not isinstance(item, dict):
                continue
            impact = str(item.get("impact") or "").strip().lower()
            if impact != "high":
                continue
            if not _is_us_relevant(item):
                continue

            stamp = item.get("time_utc") or item.get("datetime")
            title = item.get("title") or item.get("name")
            if not stamp or not title:
                continue

            scheduled = _parse_datetime(str(stamp))
            if not (start_utc <= scheduled <= end_utc):
                continue

            events.append(
                EconomicEvent(
                    title=str(title),
                    scheduled_at=scheduled,
                    impact=Impact.HIGH,
                    currency="USD",
                    xauusd_relevant=True,
                )
            )

        events.sort(key=lambda event: event.scheduled_at)
        return events

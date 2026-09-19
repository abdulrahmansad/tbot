from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .news import EconomicEvent, Impact


class XoomarCalendarError(RuntimeError):
    pass


def _default_get(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "TBOT/1.0 (+private forward demo)",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class XoomarEconomicCalendarProvider:
    """No-key US macro calendar fallback based on XOOMAR's documented API."""

    base_url = "https://xoomar.com/api/markets/calendar"

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
            "importance": "high",
        }
        payload = json.loads(
            self.http_get(f"{self.base_url}?{urlencode(params)}").decode("utf-8")
        )

        raw_events = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(raw_events, list):
            raise XoomarCalendarError("XOOMAR response did not contain a data list")

        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)
        events: list[EconomicEvent] = []

        for item in raw_events:
            if not isinstance(item, dict):
                continue

            title = (
                item.get("eventName")
                or item.get("name")
                or item.get("title")
                or item.get("event")
                or item.get("series")
            )
            stamp = (
                item.get("scheduledAt")
                or item.get("scheduled_at")
                or item.get("time_utc")
                or item.get("datetime")
                or item.get("date")
            )
            if not title or not stamp:
                continue

            scheduled = _parse_datetime(str(stamp))
            if not (start_utc <= scheduled <= end_utc):
                continue

            importance = str(
                item.get("importance") or item.get("impact") or "high"
            ).strip().lower()
            if importance not in {"high", "3"}:
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

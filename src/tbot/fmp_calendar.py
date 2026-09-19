from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from .news import EconomicEvent, Impact


load_dotenv()


class FmpCalendarError(RuntimeError):
    pass


def _default_get(url: str, api_key: str) -> bytes:
    request = Request(url, headers={"apikey": api_key})
    with urlopen(request, timeout=20) as response:
        return response.read()


def _impact(value) -> Impact:
    text = str(value or "").strip().upper()
    if text in {"HIGH", "3", "HIGH IMPACT"}:
        return Impact.HIGH
    if text in {"MEDIUM", "2", "MODERATE", "MEDIUM IMPACT"}:
        return Impact.MEDIUM
    return Impact.LOW


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class FmpEconomicCalendarProvider:
    """Economic-calendar adapter for the FMP stable economic-calendar endpoint."""

    base_url = "https://financialmodelingprep.com/stable/economic-calendar"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        http_get: Callable[[str, str], bytes] = _default_get,
    ) -> None:
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FMP_API_KEY is required for the optional economic-calendar provider"
            )
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
        }
        payload = json.loads(
            self.http_get(f"{self.base_url}?{urlencode(params)}", self.api_key).decode(
                "utf-8"
            )
        )
        if isinstance(payload, dict) and payload.get("Error Message"):
            raise FmpCalendarError(str(payload["Error Message"]))
        if not isinstance(payload, list):
            raise FmpCalendarError("FMP economic-calendar response must be a list")

        events: list[EconomicEvent] = []
        for item in payload:
            if not isinstance(item, dict):
                continue

            stamp = item.get("date") or item.get("datetime")
            title = item.get("event") or item.get("name") or item.get("title")
            if not stamp or not title:
                continue

            scheduled = _parse_datetime(str(stamp))
            if not (start.astimezone(timezone.utc) <= scheduled <= end.astimezone(timezone.utc)):
                continue

            country = str(item.get("country") or "").strip().upper()
            currency = str(item.get("currency") or "").strip().upper()
            if not currency and country in {"US", "USA", "UNITED STATES"}:
                currency = "USD"

            events.append(
                EconomicEvent(
                    title=str(title),
                    scheduled_at=scheduled,
                    impact=_impact(item.get("impact")),
                    currency=currency or "UNKNOWN",
                    xauusd_relevant=True,
                )
            )

        events.sort(key=lambda event: event.scheduled_at)
        return events

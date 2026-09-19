from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from .news import EconomicEvent
from .news_provider import EconomicCalendarProvider


class CachedEconomicCalendarProvider:
    """Cache economic-calendar events across nearby worker polls."""

    def __init__(
        self,
        upstream: EconomicCalendarProvider,
        *,
        ttl_minutes: int = 15,
        padding_minutes: int = 60,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        if ttl_minutes < 1:
            raise ValueError("ttl_minutes must be >= 1")
        if padding_minutes < 0:
            raise ValueError("padding_minutes cannot be negative")
        self.upstream = upstream
        self.ttl = timedelta(minutes=ttl_minutes)
        self.padding = timedelta(minutes=padding_minutes)
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._fetched_at: datetime | None = None
        self._coverage_start: datetime | None = None
        self._coverage_end: datetime | None = None
        self._events: list[EconomicEvent] = []

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

        now = self.now_fn()
        if now.tzinfo is None:
            raise ValueError("cache clock must be timezone-aware")

        cache_fresh = (
            self._fetched_at is not None
            and now - self._fetched_at <= self.ttl
        )
        covered = (
            self._coverage_start is not None
            and self._coverage_end is not None
            and self._coverage_start <= start
            and self._coverage_end >= end
        )

        if not (cache_fresh and covered):
            coverage_start = start - self.padding
            coverage_end = end + self.padding
            self._events = list(
                self.upstream.fetch_events(
                    start=coverage_start,
                    end=coverage_end,
                )
            )
            self._fetched_at = now
            self._coverage_start = coverage_start
            self._coverage_end = coverage_end

        return [
            event
            for event in self._events
            if start <= event.scheduled_at <= end
        ]

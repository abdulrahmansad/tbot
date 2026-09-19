from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .news import EconomicEvent
from .news_provider import EconomicCalendarProvider


class FallbackEconomicCalendarProvider:
    """Try calendar providers in order until one succeeds."""

    def __init__(self, providers: Iterable[EconomicCalendarProvider]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("at least one calendar provider is required")
        self.last_provider_name: str | None = None
        self.last_error: str | None = None
        self.last_failures: list[str] = []

    def fetch_events(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[EconomicEvent]:
        errors: list[str] = []
        for provider in self.providers:
            try:
                events = provider.fetch_events(start=start, end=end)
                self.last_provider_name = type(provider).__name__
                self.last_failures = list(errors)
                self.last_error = None
                return events
            except Exception as exc:
                errors.append(f"{type(provider).__name__}: {type(exc).__name__}: {exc}")

        self.last_failures = list(errors)
        self.last_error = " | ".join(errors)
        raise RuntimeError(
            "all economic calendar providers failed: " + self.last_error
        )

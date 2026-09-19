from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from tbot.flip_dip.models import NewsGate


class Impact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class EconomicEvent:
    title: str
    scheduled_at: datetime
    impact: Impact
    currency: str = "USD"
    xauusd_relevant: bool = True


class NewsBlackoutEngine:
    def __init__(self, *, before_minutes: int, after_minutes: int) -> None:
        if before_minutes < 0 or after_minutes < 0:
            raise ValueError("blackout minutes cannot be negative")
        self.before = timedelta(minutes=before_minutes)
        self.after = timedelta(minutes=after_minutes)

    def evaluate(self, *, now: datetime, events: list[EconomicEvent]) -> NewsGate:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        relevant = sorted(
            (
                event
                for event in events
                if event.impact is Impact.HIGH
                and event.xauusd_relevant
                and event.currency.upper() == "USD"
            ),
            key=lambda event: event.scheduled_at,
        )

        for event in relevant:
            if event.scheduled_at.tzinfo is None:
                raise ValueError("event timestamps must be timezone-aware")

            blackout_start = event.scheduled_at - self.before
            blackout_end = event.scheduled_at + self.after
            if blackout_start <= now <= blackout_end:
                return NewsGate(
                    clear=False,
                    reason=f"High-impact news blackout: {event.title}",
                    event_time=event.scheduled_at,
                )

        return NewsGate(clear=True)

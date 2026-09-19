from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .news import EconomicEvent


class EconomicCalendarProvider(Protocol):
    def fetch_events(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> list[EconomicEvent]:
        ...

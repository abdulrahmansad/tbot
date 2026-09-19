from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Mapping


@dataclass(frozen=True)
class FlipDipConfig:
    symbol: str = "XAUUSD"
    risk_percent: float = 5.0
    minimum_rr: float = 5.0
    max_executions_per_zone: int = 3

    # Istanbul local time. 23:00 -> 20:00 crosses midnight.
    trading_start: time = time(23, 0)
    trading_end: time = time(20, 0)
    timezone: str = "Europe/Istanbul"

    news_blackout_before_minutes: int = 30
    news_blackout_after_minutes: int = 15

    confirmation_timeframe: Mapping[str, str] = field(
        default_factory=lambda: {
            "5M": "15M",
            "15M": "1H",
            "1H": "4H",
        }
    )

    # Must be calibrated from owner-approved examples.
    rejection_min_score: float | None = None
    flip_zone_definition_version: str = "UNVALIDATED"
    structure_definition_version: str = "UNVALIDATED"

    def validate(self) -> None:
        if self.symbol != "XAUUSD":
            raise ValueError("Phase 0 supports XAUUSD only.")
        if not (0 < self.risk_percent <= 100):
            raise ValueError("risk_percent must be > 0 and <= 100")
        if self.minimum_rr < 5:
            raise ValueError("Flip & Dip requires minimum_rr >= 5")
        if self.max_executions_per_zone < 1:
            raise ValueError("max_executions_per_zone must be >= 1")
        if self.news_blackout_before_minutes < 0 or self.news_blackout_after_minutes < 0:
            raise ValueError("news blackout values cannot be negative")

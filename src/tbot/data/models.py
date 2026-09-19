from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RawCandle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    symbol: str = "XAUUSD"
    timeframe: str = "5M"

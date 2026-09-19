from __future__ import annotations

from datetime import datetime
from typing import Protocol

from tbot.flip_dip.models import Candle


class MarketDataProvider(Protocol):
    def fetch_candles(
        self,
        *,
        timeframe: str,
        outputsize: int = 500,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        ...

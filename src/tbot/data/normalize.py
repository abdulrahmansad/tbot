from __future__ import annotations

from collections.abc import Iterable

from tbot.flip_dip.models import Candle

from .models import RawCandle


_ALLOWED_TIMEFRAMES = {"5M", "15M", "1H", "4H"}


def normalize_candles(rows: Iterable[RawCandle]) -> list[Candle]:
    normalized: list[Candle] = []

    for row in rows:
        if row.symbol != "XAUUSD":
            raise ValueError("Phase 0 accepts XAUUSD data only")
        if row.timeframe not in _ALLOWED_TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {row.timeframe}")
        if row.timestamp.tzinfo is None:
            raise ValueError("Candle timestamps must be timezone-aware")
        if row.high < max(row.open, row.close, row.low):
            raise ValueError("Invalid OHLC: high is below another price")
        if row.low > min(row.open, row.close, row.high):
            raise ValueError("Invalid OHLC: low is above another price")

        normalized.append(
            Candle(
                symbol=row.symbol,
                timeframe=row.timeframe,
                timestamp=row.timestamp,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
            )
        )

    normalized.sort(key=lambda candle: candle.timestamp)
    return normalized

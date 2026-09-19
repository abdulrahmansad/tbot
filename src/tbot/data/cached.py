from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .provider import MarketDataProvider
from tbot.flip_dip.models import Candle


_TIMEFRAME_SECONDS = {
    "5M": 5 * 60,
    "15M": 15 * 60,
    "1H": 60 * 60,
    "4H": 4 * 60 * 60,
}


@dataclass
class _CacheEntry:
    bucket: int
    outputsize: int
    candles: list[Candle]


class TimeframeCachedMarketDataProvider:
    """Cache live market data until the next timeframe bucket.

    Historical/ranged requests bypass this cache. Live calls for the same
    timeframe/output size share one upstream request per candle bucket.
    """

    def __init__(
        self,
        upstream: MarketDataProvider,
        *,
        now_fn: Callable[[], datetime] | None = None,
        refresh_grace_seconds: int = 15,
    ) -> None:
        if refresh_grace_seconds < 0:
            raise ValueError("refresh_grace_seconds cannot be negative")
        self.upstream = upstream
        self.now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self.refresh_grace_seconds = refresh_grace_seconds
        self._cache: dict[str, _CacheEntry] = {}

    def _bucket(self, timeframe: str) -> int:
        if timeframe not in _TIMEFRAME_SECONDS:
            raise ValueError(f"unsupported cache timeframe: {timeframe}")
        now = self.now_fn()
        if now.tzinfo is None:
            raise ValueError("cache clock must be timezone-aware")
        effective_timestamp = now.timestamp() - self.refresh_grace_seconds
        return int(effective_timestamp) // _TIMEFRAME_SECONDS[timeframe]

    def fetch_candles(
        self,
        *,
        timeframe: str,
        outputsize: int = 500,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        if start is not None or end is not None:
            return self.upstream.fetch_candles(
                timeframe=timeframe,
                outputsize=outputsize,
                start=start,
                end=end,
            )

        bucket = self._bucket(timeframe)
        cached = self._cache.get(timeframe)
        if (
            cached is not None
            and cached.bucket == bucket
            and cached.outputsize >= outputsize
        ):
            return cached.candles[-outputsize:]

        candles = self.upstream.fetch_candles(
            timeframe=timeframe,
            outputsize=outputsize,
        )
        self._cache[timeframe] = _CacheEntry(
            bucket=bucket,
            outputsize=outputsize,
            candles=list(candles),
        )
        return list(candles)

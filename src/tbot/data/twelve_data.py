from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv

from tbot.flip_dip.models import Candle


load_dotenv()

_INTERVALS = {
    "5M": "5min",
    "15M": "15min",
    "1H": "1h",
    "4H": "4h",
}


class TwelveDataError(RuntimeError):
    pass


def _default_get(url: str) -> bytes:
    with urlopen(url, timeout=20) as response:
        return response.read()


class TwelveDataXauUsdProvider:
    """XAU/USD candle adapter for Twelve Data.

    Strategy code sees normalized XAUUSD candles and is not coupled to the
    provider's symbol or interval naming.
    """

    base_url = "https://api.twelvedata.com/time_series"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        http_get: Callable[[str], bytes] = _default_get,
    ) -> None:
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TWELVE_DATA_API_KEY is required. Put it in the project .env file "
                "as TWELVE_DATA_API_KEY=your_key."
            )
        self.http_get = http_get

    def fetch_candles(
        self,
        *,
        timeframe: str,
        outputsize: int = 500,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        if timeframe not in _INTERVALS:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        if not (1 <= outputsize <= 5000):
            raise ValueError("outputsize must be between 1 and 5000")

        params: dict[str, str | int] = {
            "symbol": "XAU/USD",
            "interval": _INTERVALS[timeframe],
            "apikey": self.api_key,
            "outputsize": outputsize,
            "timezone": "UTC",
            "order": "asc",
            "format": "JSON",
        }

        if start is not None:
            params["start_date"] = self._format_datetime(start)
        if end is not None:
            params["end_date"] = self._format_datetime(end)

        payload = json.loads(
            self.http_get(f"{self.base_url}?{urlencode(params)}").decode("utf-8")
        )

        if payload.get("status") == "error":
            raise TwelveDataError(payload.get("message", "Twelve Data API error"))

        values = payload.get("values")
        if not isinstance(values, list):
            raise TwelveDataError("Twelve Data response did not contain candle values")

        candles: list[Candle] = []
        for item in values:
            stamp = datetime.fromisoformat(item["datetime"])
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            else:
                stamp = stamp.astimezone(timezone.utc)

            candles.append(
                Candle(
                    symbol="XAUUSD",
                    timeframe=timeframe,
                    timestamp=stamp,
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                )
            )

        candles.sort(key=lambda candle: candle.timestamp)
        return candles

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            raise ValueError("start/end must be timezone-aware")
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

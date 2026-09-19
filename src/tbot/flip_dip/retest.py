from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from .models import Candle, Direction, FlipZone


def candle_retests_zone(zone: FlipZone, candle: Candle) -> bool:
    if candle.timeframe != zone.timeframe.value:
        raise ValueError("Retest candle timeframe must match zone entry timeframe")

    overlaps = candle.high >= zone.lower_price and candle.low <= zone.upper_price
    if not overlaps:
        return False

    if zone.direction is Direction.SELL:
        return candle.open < zone.lower_price or candle.close < zone.lower_price

    return candle.open > zone.upper_price or candle.close > zone.upper_price


def candle_rearms_zone(zone: FlipZone, candle: Candle) -> bool:
    """Return True once price has clearly left the zone on the entry side."""
    if candle.timeframe != zone.timeframe.value:
        raise ValueError("Rearm candle timeframe must match zone entry timeframe")
    if zone.direction is Direction.SELL:
        return candle.high < zone.lower_price
    return candle.low > zone.upper_price


def retest_episodes_after(
    zone: FlipZone,
    candles: Sequence[Candle],
    *,
    after: datetime | None = None,
    max_retests: int = 3,
    require_rearm: bool = True,
) -> list[Candle]:
    """Return distinct correct-side retest episodes in chronological order.

    Consecutive candles touching/occupying one zone are one retest episode.
    When require_rearm is enabled, price must leave the zone on the correct
    side before another retest can be counted.
    """
    if max_retests < 1:
        raise ValueError("max_retests must be >= 1")

    threshold = after or zone.created_at
    retests: list[Candle] = []
    armed = True

    for candle in candles:
        if candle.timestamp <= threshold:
            continue
        if candle.timeframe != zone.timeframe.value:
            continue

        if not armed:
            if candle_rearms_zone(zone, candle):
                armed = True
            continue

        if candle_retests_zone(zone, candle):
            retests.append(candle)
            if len(retests) >= max_retests:
                break
            if require_rearm:
                armed = False

    return retests


def first_retest_after(
    zone: FlipZone,
    candles: Sequence[Candle],
    *,
    after: datetime | None = None,
) -> Candle | None:
    retests = retest_episodes_after(zone, candles, after=after, max_retests=1)
    return retests[0] if retests else None

from __future__ import annotations

from collections.abc import Sequence

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


def first_retest_after(zone: FlipZone, candles: Sequence[Candle]) -> Candle | None:
    for candle in candles:
        if candle.timestamp <= zone.created_at:
            continue
        if candle_retests_zone(zone, candle):
            return candle
    return None

from __future__ import annotations

from statistics import median
from typing import Sequence

from .models import Candle, Direction, FlipZone


def entry_reference(zone: FlipZone) -> float:
    return zone.lower_price if zone.direction is Direction.SELL else zone.upper_price


def recent_median_range(
    candles: Sequence[Candle],
    *,
    before,
    timeframe: str,
    lookback: int = 20,
) -> float | None:
    if lookback < 1:
        raise ValueError("lookback must be >= 1")

    eligible = [
        candle
        for candle in candles
        if candle.timeframe == timeframe and candle.timestamp < before
    ]
    sample = eligible[-lookback:]
    if not sample:
        return None

    ranges = [
        max(candle.high - candle.low, 0.0)
        for candle in sample
        if candle.high >= candle.low
    ]
    positive = [value for value in ranges if value > 0]
    return median(positive) if positive else None


def stabilized_sizing_reference(
    *,
    zone: FlipZone,
    structural_reference: float | None,
    candles: Sequence[Candle],
    before,
    lookback: int = 20,
    range_floor_multiple: float = 1.0,
) -> float:
    """Return a planning reference with a recent price-range floor.

    This is a sizing/calibration safeguard, not an entry or invalidation rule.
    It prevents microscopic zones/rejection extremes from creating unrealistic
    position sizes or normalized R values.
    """
    if range_floor_multiple <= 0:
        raise ValueError("range_floor_multiple must be positive")

    entry = entry_reference(zone)
    fallback = zone.upper_price if zone.direction is Direction.SELL else zone.lower_price
    reference = structural_reference if structural_reference is not None else fallback
    structural_distance = abs(entry - reference)

    normal_range = recent_median_range(
        candles,
        before=before,
        timeframe=zone.timeframe.value,
        lookback=lookback,
    )
    range_floor = (normal_range or 0.0) * range_floor_multiple
    risk_distance = max(structural_distance, range_floor, zone.upper_price - zone.lower_price)

    if zone.direction is Direction.SELL:
        return entry + risk_distance
    return entry - risk_distance

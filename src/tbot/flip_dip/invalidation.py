from __future__ import annotations

from .models import Candle, Direction, FlipZone


def is_invalidated_by_close(zone: FlipZone, candle: Candle) -> bool:
    """Apply the owner's entry-timeframe candle-close invalidation rule."""
    if candle.symbol != "XAUUSD":
        raise ValueError("Invalidation requires XAUUSD candle data")
    if candle.timeframe != zone.timeframe.value:
        raise ValueError(
            f"Invalidation candle must be {zone.timeframe.value}, got {candle.timeframe}"
        )

    if zone.direction is Direction.SELL:
        return candle.close > zone.upper_price

    return candle.close < zone.lower_price

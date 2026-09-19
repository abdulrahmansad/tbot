from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .invalidation import is_invalidated_by_close
from .models import Candle, Direction, FlipZone


class OutcomeStatus(str, Enum):
    OPEN = "OPEN"
    INVALIDATED = "INVALIDATED"
    TARGET_2R = "TARGET_2R"
    TARGET_3_5R = "TARGET_3_5R"
    TARGET_5R = "TARGET_5R"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class HistoricalOutcome:
    status: OutcomeStatus
    entry_reference_price: float
    risk_unit: float
    target_2r: float
    target_3_5r: float
    target_5r: float
    max_favorable_r: float
    max_adverse_r: float
    bars_observed: int
    resolved_at: object | None = None
    ambiguity_reason: str | None = None


def _entry_reference(zone: FlipZone) -> float:
    # Calibration-only reference: the near-side edge first approached on retest.
    return zone.lower_price if zone.direction is Direction.SELL else zone.upper_price


def _target(entry: float, risk: float, direction: Direction, r_multiple: float) -> float:
    if direction is Direction.SELL:
        return entry - (risk * r_multiple)
    return entry + (risk * r_multiple)


def simulate_historical_outcome(
    *,
    zone: FlipZone,
    candles: Sequence[Candle],
    activated_at,
) -> HistoricalOutcome:
    """Replay candles after plan activation without pretending to know intrabar order.

    R is normalized by zone width for calibration only. Strategy invalidation
    remains the owner's candle-close-beyond-zone rule. If one candle both
    reaches a new target and closes through invalidation, the result is marked
    AMBIGUOUS rather than guessing which happened first.
    """
    risk = max(zone.upper_price - zone.lower_price, 1e-9)
    entry = _entry_reference(zone)
    t2 = _target(entry, risk, zone.direction, 2.0)
    t35 = _target(entry, risk, zone.direction, 3.5)
    t5 = _target(entry, risk, zone.direction, 5.0)

    future = [
        candle
        for candle in candles
        if candle.timestamp > activated_at and candle.timeframe == zone.timeframe.value
    ]

    max_favorable_r = 0.0
    max_adverse_r = 0.0
    highest_target = 0.0

    for index, candle in enumerate(future, start=1):
        if zone.direction is Direction.SELL:
            favorable_r = max(0.0, (entry - candle.low) / risk)
            adverse_r = max(0.0, (candle.high - entry) / risk)
            hit_2 = candle.low <= t2
            hit_35 = candle.low <= t35
            hit_5 = candle.low <= t5
        else:
            favorable_r = max(0.0, (candle.high - entry) / risk)
            adverse_r = max(0.0, (entry - candle.low) / risk)
            hit_2 = candle.high >= t2
            hit_35 = candle.high >= t35
            hit_5 = candle.high >= t5

        max_favorable_r = max(max_favorable_r, favorable_r)
        max_adverse_r = max(max_adverse_r, adverse_r)

        target_this_candle = 5.0 if hit_5 else 3.5 if hit_35 else 2.0 if hit_2 else 0.0
        invalidated = is_invalidated_by_close(zone, candle)

        if invalidated and target_this_candle > highest_target:
            return HistoricalOutcome(
                status=OutcomeStatus.AMBIGUOUS,
                entry_reference_price=entry,
                risk_unit=risk,
                target_2r=t2,
                target_3_5r=t35,
                target_5r=t5,
                max_favorable_r=max_favorable_r,
                max_adverse_r=max_adverse_r,
                bars_observed=index,
                resolved_at=candle.timestamp,
                ambiguity_reason="same_candle_new_target_and_close_invalidation",
            )

        highest_target = max(highest_target, target_this_candle)

        if hit_5:
            return HistoricalOutcome(
                status=OutcomeStatus.TARGET_5R,
                entry_reference_price=entry,
                risk_unit=risk,
                target_2r=t2,
                target_3_5r=t35,
                target_5r=t5,
                max_favorable_r=max_favorable_r,
                max_adverse_r=max_adverse_r,
                bars_observed=index,
                resolved_at=candle.timestamp,
            )

        if invalidated:
            if highest_target >= 3.5:
                status = OutcomeStatus.TARGET_3_5R
            elif highest_target >= 2.0:
                status = OutcomeStatus.TARGET_2R
            else:
                status = OutcomeStatus.INVALIDATED
            return HistoricalOutcome(
                status=status,
                entry_reference_price=entry,
                risk_unit=risk,
                target_2r=t2,
                target_3_5r=t35,
                target_5r=t5,
                max_favorable_r=max_favorable_r,
                max_adverse_r=max_adverse_r,
                bars_observed=index,
                resolved_at=candle.timestamp,
            )

    if highest_target >= 3.5:
        status = OutcomeStatus.TARGET_3_5R
    elif highest_target >= 2.0:
        status = OutcomeStatus.TARGET_2R
    else:
        status = OutcomeStatus.OPEN

    return HistoricalOutcome(
        status=status,
        entry_reference_price=entry,
        risk_unit=risk,
        target_2r=t2,
        target_3_5r=t35,
        target_5r=t5,
        max_favorable_r=max_favorable_r,
        max_adverse_r=max_adverse_r,
        bars_observed=len(future),
    )

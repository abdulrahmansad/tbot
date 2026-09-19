from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Sequence
from uuid import uuid4

from .models import Candle, Direction, EntryTimeframe, FlipZone, SetupState, StructureConfirmation


@dataclass(frozen=True)
class ProvisionalDetectorConfig:
    pivot_left: int = 2
    pivot_right: int = 2
    zone_lookback: int = 80
    zone_padding_fraction: float = 0.15
    minimum_departure_zone_widths: float = 1.5
    rejection_lookahead_candles: int = 3
    minimum_rejection_score: float = 0.60

    def validate(self) -> None:
        if self.pivot_left < 1 or self.pivot_right < 1:
            raise ValueError("pivot windows must be >= 1")
        if self.zone_lookback < 10:
            raise ValueError("zone_lookback must be >= 10")
        if self.zone_padding_fraction < 0:
            raise ValueError("zone_padding_fraction cannot be negative")
        if self.minimum_departure_zone_widths <= 0:
            raise ValueError("minimum_departure_zone_widths must be positive")
        if self.rejection_lookahead_candles < 1:
            raise ValueError("rejection_lookahead_candles must be >= 1")
        if not (0 <= self.minimum_rejection_score <= 1):
            raise ValueError("minimum_rejection_score must be within 0..1")


def _entry_tf(value: str) -> EntryTimeframe:
    try:
        return EntryTimeframe(value)
    except ValueError as exc:
        raise ValueError(
            f"Provisional detector only supports 5M/15M/1H entry data, got {value}"
        ) from exc


def _pivot_highs(candles: Sequence[Candle], left: int, right: int) -> list[int]:
    indexes: list[int] = []
    for i in range(left, len(candles) - right):
        high = candles[i].high
        if all(high > candles[j].high for j in range(i-left, i)) and all(
            high >= candles[j].high for j in range(i+1, i+right+1)
        ):
            indexes.append(i)
    return indexes


def _pivot_lows(candles: Sequence[Candle], left: int, right: int) -> list[int]:
    indexes: list[int] = []
    for i in range(left, len(candles) - right):
        low = candles[i].low
        if all(low < candles[j].low for j in range(i-left, i)) and all(
            low <= candles[j].low for j in range(i+1, i+right+1)
        ):
            indexes.append(i)
    return indexes


class ProvisionalFlipZoneDetector:
    def __init__(self, config: ProvisionalDetectorConfig | None = None) -> None:
        self.config = config or ProvisionalDetectorConfig()
        self.config.validate()

    def detect(self, candles: Sequence[Candle]) -> list[FlipZone]:
        if not candles:
            return []
        timeframe = _entry_tf(candles[0].timeframe)
        if any(c.timeframe != candles[0].timeframe for c in candles):
            raise ValueError("All candles must share one timeframe")

        zones: list[FlipZone] = []
        for pivot_index in _pivot_highs(
            candles, self.config.pivot_left, self.config.pivot_right
        ):
            found = self._find_sell_flip(candles, pivot_index, timeframe)
            if found is not None:
                zones.append(found)

        for pivot_index in _pivot_lows(
            candles, self.config.pivot_left, self.config.pivot_right
        ):
            found = self._find_buy_flip(candles, pivot_index, timeframe)
            if found is not None:
                zones.append(found)

        zones.sort(key=lambda z: z.created_at)
        return zones

    def _zone_bounds(self, candle: Candle, use_high: bool) -> tuple[float, float]:
        body_high = max(candle.open, candle.close)
        body_low = min(candle.open, candle.close)
        full_range = max(candle.high - candle.low, 1e-9)
        padding = full_range * self.config.zone_padding_fraction

        if use_high:
            lower = max(body_high - padding, candle.low)
            upper = candle.high
        else:
            lower = candle.low
            upper = min(body_low + padding, candle.high)

        if lower >= upper:
            lower, upper = candle.low, candle.high
        return lower, upper

    def _find_sell_flip(
        self,
        candles: Sequence[Candle],
        pivot_index: int,
        timeframe: EntryTimeframe,
    ) -> FlipZone | None:
        pivot = candles[pivot_index]
        lower, upper = self._zone_bounds(pivot, True)
        end = min(len(candles), pivot_index + 1 + self.config.zone_lookback)
        traded_above = False

        for candle in candles[pivot_index + 1:end]:
            if candle.high > upper:
                traded_above = True
            if traded_above and candle.close < lower:
                return FlipZone(
                    id=f"v0-sell-{uuid4().hex[:12]}",
                    direction=Direction.SELL,
                    timeframe=timeframe,
                    lower_price=lower,
                    upper_price=upper,
                    created_at=candle.timestamp,
                    state=SetupState.RETURN_CONFIRMED,
                )
        return None

    def _find_buy_flip(
        self,
        candles: Sequence[Candle],
        pivot_index: int,
        timeframe: EntryTimeframe,
    ) -> FlipZone | None:
        pivot = candles[pivot_index]
        lower, upper = self._zone_bounds(pivot, False)
        end = min(len(candles), pivot_index + 1 + self.config.zone_lookback)
        traded_below = False

        for candle in candles[pivot_index + 1:end]:
            if candle.low < lower:
                traded_below = True
            if traded_below and candle.close > upper:
                return FlipZone(
                    id=f"v0-buy-{uuid4().hex[:12]}",
                    direction=Direction.BUY,
                    timeframe=timeframe,
                    lower_price=lower,
                    upper_price=upper,
                    created_at=candle.timestamp,
                    state=SetupState.RETURN_CONFIRMED,
                )
        return None


class ProvisionalRejectionEvaluator:
    def __init__(self, config: ProvisionalDetectorConfig | None = None) -> None:
        self.config = config or ProvisionalDetectorConfig()
        self.config.validate()

    def score(self, zone: FlipZone, candles: Sequence[Candle]) -> float:
        after = [c for c in candles if c.timestamp >= zone.created_at]
        if len(after) < 2:
            return 0.0

        width = max(zone.upper_price - zone.lower_price, 1e-9)
        sample = after[: self.config.rejection_lookahead_candles + 1]
        origin = sample[0]

        if zone.direction is Direction.SELL:
            best_departure = max(0.0, origin.close - min(c.low for c in sample[1:]))
            directional_closes = sum(1 for c in sample[1:] if c.close < zone.lower_price)
        else:
            best_departure = max(0.0, max(c.high for c in sample[1:]) - origin.close)
            directional_closes = sum(1 for c in sample[1:] if c.close > zone.upper_price)

        departure_component = min(
            best_departure / (width * self.config.minimum_departure_zone_widths),
            1.0,
        )
        close_component = directional_closes / max(len(sample) - 1, 1)

        efficiencies = []
        for c in sample[1:]:
            candle_range = max(c.high - c.low, 1e-9)
            efficiencies.append(abs(c.close - c.open) / candle_range)
        body_component = min(mean(efficiencies) * 1.5, 1.0) if efficiencies else 0.0

        score = departure_component * 0.50 + close_component * 0.30 + body_component * 0.20
        return max(0.0, min(score, 1.0))

    def is_healthy(self, zone: FlipZone, candles: Sequence[Candle]) -> bool:
        return self.score(zone, candles) >= self.config.minimum_rejection_score


class ProvisionalStructureDetector:
    def __init__(self, config: ProvisionalDetectorConfig | None = None) -> None:
        self.config = config or ProvisionalDetectorConfig()
        self.config.validate()

    def confirm(
        self,
        candles: Sequence[Candle],
        *,
        direction: Direction,
        timeframe: str,
    ) -> StructureConfirmation:
        filtered = [c for c in candles if c.timeframe == timeframe]
        needed = self.config.pivot_left + self.config.pivot_right + 2
        if len(filtered) < needed:
            return StructureConfirmation(
                confirmed=False,
                timeframe=timeframe,
                direction=direction,
            )

        highs = _pivot_highs(filtered, self.config.pivot_left, self.config.pivot_right)
        lows = _pivot_lows(filtered, self.config.pivot_left, self.config.pivot_right)
        latest = filtered[-1]

        if direction is Direction.BUY and highs:
            confirmed = latest.close > filtered[highs[-1]].high
        elif direction is Direction.SELL and lows:
            confirmed = latest.close < filtered[lows[-1]].low
        else:
            confirmed = False

        return StructureConfirmation(
            confirmed=confirmed,
            timeframe=timeframe,
            direction=direction,
            kind="BOS" if confirmed else None,
            observed_at=latest.timestamp if confirmed else None,
        )

from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle, Direction
from tbot.flip_dip.provisional import (
    ProvisionalDetectorConfig,
    ProvisionalFlipZoneDetector,
    ProvisionalRejectionEvaluator,
    ProvisionalStructureDetector,
)


def c(tf, minute, o, h, l, close):
    return Candle(
        symbol="XAUUSD",
        timeframe=tf,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minute),
        open=o,
        high=h,
        low=l,
        close=close,
    )


def test_structure_can_confirm_between_return_and_retest():
    detector = ProvisionalStructureDetector(
        ProvisionalDetectorConfig(pivot_left=1, pivot_right=1)
    )
    candles = [
        c("15M", 0, 100, 102, 99, 101),
        c("15M", 15, 101, 103, 97, 98),
        c("15M", 30, 98, 100, 99, 99.5),
        c("15M", 45, 99.5, 100, 95, 96),
        c("15M", 60, 96, 97, 93, 94),
    ]

    result = detector.confirm_between(
        candles,
        direction=Direction.SELL,
        timeframe="15M",
        start=candles[2].timestamp,
        end=candles[-1].timestamp,
    )

    assert result.confirmed
    assert result.observed_at is not None
    assert result.observed_at >= candles[2].timestamp


def test_overlapping_same_direction_zones_are_deduped():
    detector = ProvisionalFlipZoneDetector(
        ProvisionalDetectorConfig(
            pivot_left=1,
            pivot_right=1,
            zone_lookback=20,
            dedupe_overlap_ratio=0.5,
            dedupe_within_bars=3,
        )
    )
    candles = [
        c("5M", 0, 100, 101, 99, 100),
        c("5M", 5, 100, 105, 99.5, 104),
        c("5M", 10, 104, 103, 100, 101),
        c("5M", 15, 101, 104.8, 100, 104),
        c("5M", 20, 104, 106, 102, 105),
        c("5M", 25, 105, 106.2, 101, 102),
        c("5M", 30, 102, 103, 99, 100),
        c("5M", 35, 100, 102, 98, 99),
    ]
    zones = detector.detect(candles)

    sell_zones = [z for z in zones if z.direction is Direction.SELL]
    for i, first in enumerate(sell_zones):
        for second in sell_zones[i + 1:]:
            close_in_time = abs(
                (second.created_at - first.created_at).total_seconds()
            ) <= 15 * 60
            if not close_in_time:
                continue
            overlap = max(
                0.0,
                min(first.upper_price, second.upper_price)
                - max(first.lower_price, second.lower_price),
            )
            smaller = min(
                first.upper_price - first.lower_price,
                second.upper_price - second.lower_price,
            )
            assert smaller <= 0 or overlap / smaller < 0.5


def test_rejection_observed_only_after_full_window_closes():
    evaluator = ProvisionalRejectionEvaluator(
        ProvisionalDetectorConfig(rejection_lookahead_candles=2)
    )
    candles = [
        c("5M", 0, 100, 101, 99, 100),
        c("5M", 5, 100, 100.5, 97, 98),
        c("5M", 10, 98, 99, 96, 97),
    ]
    from tbot.flip_dip.models import EntryTimeframe, FlipZone, SetupState

    zone = FlipZone(
        id="z",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=99.5,
        upper_price=100.5,
        created_at=candles[0].timestamp,
        state=SetupState.RETURN_CONFIRMED,
    )

    result = evaluator.evaluate(zone, candles)

    assert result.observed_at == candles[2].timestamp + timedelta(minutes=5)
    assert result.sample_size == 3


def test_flip_search_starts_only_after_pivot_right_confirmation():
    detector = ProvisionalFlipZoneDetector(
        ProvisionalDetectorConfig(
            pivot_left=1,
            pivot_right=1,
            zone_lookback=20,
        )
    )
    candles = [
        c("5M", 0, 100, 101, 99, 100),
        c("5M", 5, 100, 105, 99, 104),   # pivot high candidate
        c("5M", 10, 104, 106, 98, 99),   # confirms pivot, but flips here
        c("5M", 15, 99, 100, 97, 98),
        c("5M", 20, 98, 99, 96, 97),
    ]

    zones = detector.detect(candles)

    # The candle needed to confirm the pivot cannot also be used as a
    # post-confirmation flip event.
    assert not any(
        z.direction is Direction.SELL and z.created_at == candles[2].timestamp
        for z in zones
    )

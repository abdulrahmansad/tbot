from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle, Direction, EntryTimeframe, FlipZone
from tbot.flip_dip.provisional import (
    ProvisionalDetectorConfig,
    ProvisionalFlipZoneDetector,
    ProvisionalRejectionEvaluator,
)
from tbot.flip_dip.retest import candle_retests_zone


def make_series(tf: str, rows: list[tuple[float, float, float, float]]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    step = timedelta(minutes=5 if tf == "5M" else 15)
    return [
        Candle(
            symbol="XAUUSD",
            timeframe=tf,
            timestamp=start + step * i,
            open=o,
            high=h,
            low=l,
            close=c,
        )
        for i, (o, h, l, c) in enumerate(rows)
    ]


def test_detects_simple_sell_flip():
    rows = [
        (100, 101, 99, 100),
        (100, 102, 99, 101),
        (101, 105, 100, 104),
        (104, 104.5, 101, 102),
        (102, 103, 100, 101),
        (101, 106, 100.5, 105),
        (105, 106.5, 102, 103),
        (103, 104, 99, 100),
        (100, 102, 98, 99),
    ]
    detector = ProvisionalFlipZoneDetector(
        ProvisionalDetectorConfig(pivot_left=2, pivot_right=2, zone_lookback=20)
    )
    zones = detector.detect(make_series("5M", rows))
    assert any(z.direction is Direction.SELL for z in zones)


def test_rejection_score_rewards_clean_departure():
    zone = FlipZone(
        id="z",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=100,
        upper_price=101,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    candles = make_series(
        "5M",
        [
            (100.5, 101.2, 99.8, 100.0),
            (100, 100.2, 98, 98.4),
            (98.4, 98.6, 96.5, 97),
            (97, 97.2, 95.5, 96),
        ],
    )
    evaluator = ProvisionalRejectionEvaluator()
    assert evaluator.score(zone, candles) >= 0.60


def test_sell_retest_must_come_from_below():
    zone = FlipZone(
        id="z",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=100,
        upper_price=101,
        created_at=datetime.now(timezone.utc),
    )
    candle = Candle(
        symbol="XAUUSD",
        timeframe="5M",
        timestamp=datetime.now(timezone.utc),
        open=99.5,
        high=100.5,
        low=99,
        close=99.8,
    )
    assert candle_retests_zone(zone, candle)

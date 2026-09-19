from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle, Direction, EntryTimeframe, FlipZone
from tbot.flip_dip.sizing import recent_median_range, stabilized_sizing_reference


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def candle(minute, high, low):
    return Candle(
        symbol="XAUUSD",
        timeframe="5M",
        timestamp=START + timedelta(minutes=minute),
        open=(high + low) / 2,
        high=high,
        low=low,
        close=(high + low) / 2,
    )


def test_recent_median_range_uses_only_prior_candles():
    candles = [
        candle(0, 101, 99),
        candle(5, 102, 98),
        candle(10, 110, 90),
    ]
    value = recent_median_range(
        candles,
        before=START + timedelta(minutes=10),
        timeframe="5M",
        lookback=20,
    )
    assert value == 3.0


def test_sell_sizing_reference_uses_range_floor_for_micro_zone():
    zone = FlipZone(
        id="z",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=100.0,
        upper_price=100.1,
        created_at=START,
    )
    candles = [
        candle(0, 101, 99),
        candle(5, 102, 98),
        candle(10, 103, 99),
    ]
    reference = stabilized_sizing_reference(
        zone=zone,
        structural_reference=100.11,
        candles=candles,
        before=START + timedelta(minutes=15),
    )
    assert reference == 104.0


def test_buy_sizing_reference_uses_range_floor_for_micro_zone():
    zone = FlipZone(
        id="z",
        direction=Direction.BUY,
        timeframe=EntryTimeframe.M5,
        lower_price=100.0,
        upper_price=100.1,
        created_at=START,
    )
    candles = [
        candle(0, 101, 99),
        candle(5, 102, 98),
        candle(10, 103, 99),
    ]
    reference = stabilized_sizing_reference(
        zone=zone,
        structural_reference=99.99,
        candles=candles,
        before=START + timedelta(minutes=15),
    )
    assert reference == 96.1

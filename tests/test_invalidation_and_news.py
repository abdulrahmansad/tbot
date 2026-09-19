from datetime import datetime, timedelta, timezone

import pytest

from tbot.flip_dip.invalidation import is_invalidated_by_close
from tbot.flip_dip.models import Candle, Direction, EntryTimeframe, FlipZone
from tbot.news import EconomicEvent, Impact, NewsBlackoutEngine


def make_zone(direction=Direction.SELL):
    return FlipZone(
        id="z",
        direction=direction,
        timeframe=EntryTimeframe.M5,
        lower_price=3600,
        upper_price=3602,
        created_at=datetime.now(timezone.utc),
    )


def candle(*, close: float, high: float = 3610, low: float = 3590):
    return Candle(
        symbol="XAUUSD",
        timeframe="5M",
        timestamp=datetime.now(timezone.utc),
        open=3601,
        high=high,
        low=low,
        close=close,
    )


def test_sell_wick_above_does_not_invalidate():
    assert not is_invalidated_by_close(make_zone(), candle(close=3601.5, high=3610))


def test_sell_close_above_invalidates():
    assert is_invalidated_by_close(make_zone(), candle(close=3603, high=3610))


def test_buy_close_below_invalidates():
    assert is_invalidated_by_close(
        make_zone(Direction.BUY),
        candle(close=3599, high=3605, low=3590),
    )


def test_news_blackout_blocks_high_impact_usd_event():
    now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    engine = NewsBlackoutEngine(before_minutes=30, after_minutes=15)
    event = EconomicEvent(
        title="Federal Reserve decision",
        scheduled_at=now + timedelta(minutes=20),
        impact=Impact.HIGH,
    )
    gate = engine.evaluate(now=now, events=[event])
    assert not gate.clear
    assert "Federal Reserve" in gate.reason


def test_low_impact_does_not_block():
    now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    engine = NewsBlackoutEngine(before_minutes=30, after_minutes=15)
    event = EconomicEvent(
        title="Minor release",
        scheduled_at=now,
        impact=Impact.LOW,
    )
    assert engine.evaluate(now=now, events=[event]).clear

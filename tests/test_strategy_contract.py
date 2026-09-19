from datetime import datetime, timedelta, timezone

import pytest

from tbot.flip_dip.config import FlipDipConfig
from tbot.flip_dip.models import Candle, Direction, EntryTimeframe, FlipZone
from tbot.flip_dip.retest import retest_episodes_after


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def candle(minute, o, h, l, close):
    return Candle(
        symbol="XAUUSD",
        timeframe="5M",
        timestamp=START + timedelta(minutes=minute),
        open=o,
        high=h,
        low=l,
        close=close,
    )


def sell_zone():
    return FlipZone(
        id="z",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=100,
        upper_price=102,
        created_at=START,
    )


def test_primary_entries_are_5m_15m_by_default():
    cfg = FlipDipConfig()
    assert cfg.enabled_entry_timeframes == ("5M", "15M")


def test_1h_entry_requires_explicit_opt_in():
    cfg = FlipDipConfig(enable_1h_entries=True)
    assert cfg.enabled_entry_timeframes == ("5M", "15M", "1H")
    assert cfg.confirmation_timeframe["1H"] == "4H"


def test_risk_cannot_exceed_owner_five_percent_cap():
    with pytest.raises(ValueError):
        FlipDipConfig(risk_percent=5.01).validate()


def test_execution_limit_cannot_exceed_three():
    with pytest.raises(ValueError):
        FlipDipConfig(max_executions_per_zone=4).validate()


def test_consecutive_zone_candles_are_one_retest_episode():
    zone = sell_zone()
    candles = [
        candle(5, 99, 101, 98, 99),
        candle(10, 99, 101.5, 98.5, 99.5),
        candle(15, 99.5, 101, 98, 99),
    ]

    retests = retest_episodes_after(
        zone,
        candles,
        after=START,
        max_retests=3,
        require_rearm=True,
    )

    assert [c.timestamp for c in retests] == [candles[0].timestamp]


def test_rearm_allows_second_and_third_retest():
    zone = sell_zone()
    candles = [
        candle(5, 99, 101, 98, 99),      # retest 1
        candle(10, 98, 99.5, 97, 98),    # leaves below / rearm
        candle(15, 99, 101, 98, 99),      # retest 2
        candle(20, 98, 99.4, 97, 98),    # rearm
        candle(25, 99, 101.5, 98, 99),    # retest 3
        candle(30, 98, 99.2, 97, 98),     # would rearm
        candle(35, 99, 101, 98, 99),      # ignored: max 3
    ]

    retests = retest_episodes_after(
        zone,
        candles,
        after=START,
        max_retests=3,
        require_rearm=True,
    )

    assert [c.timestamp for c in retests] == [
        candles[0].timestamp,
        candles[2].timestamp,
        candles[4].timestamp,
    ]

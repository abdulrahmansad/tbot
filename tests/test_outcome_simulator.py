from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle, Direction, EntryTimeframe, FlipZone
from tbot.flip_dip.outcome import OutcomeStatus, simulate_historical_outcome


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def candle(minute, o, h, l, c):
    return Candle(
        symbol="XAUUSD",
        timeframe="5M",
        timestamp=START + timedelta(minutes=minute),
        open=o,
        high=h,
        low=l,
        close=c,
    )


def sell_zone():
    return FlipZone(
        id="z1",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=100.0,
        upper_price=102.0,
        created_at=START,
    )


def test_outcome_tracks_partial_target_before_close_invalidation():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 99.5, 100.5, 95.5, 98.0),
            candle(10, 98.0, 103.5, 97.0, 103.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.TARGET_2R
    assert result.max_favorable_r >= 2.0
    assert result.bars_observed == 2


def test_same_candle_target_and_invalidation_is_ambiguous():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 100.0, 104.0, 95.0, 103.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.AMBIGUOUS
    assert result.ambiguity_reason == "same_candle_new_target_and_close_invalidation"

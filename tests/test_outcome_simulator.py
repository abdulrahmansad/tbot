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
            candle(5, 99.5, 100.5, 99.0, 99.5),
            candle(10, 99.5, 100.5, 95.5, 98.0),
            candle(15, 98.0, 103.5, 97.0, 103.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.TARGET_2R
    assert result.max_favorable_r >= 2.0
    assert result.bars_observed == 2
    assert result.terminal is True
    assert result.terminal_reason == "invalidated_after_2r"


def test_same_candle_target_and_invalidation_is_ambiguous():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 100.0, 101.0, 99.0, 100.0),
            candle(10, 100.0, 104.0, 95.0, 103.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.AMBIGUOUS
    assert result.terminal is True
    assert result.terminal_reason == "ambiguous_target_vs_invalidation_order"
    assert result.ambiguity_reason == "same_candle_new_target_and_close_invalidation"


def test_structural_sizing_reference_replaces_raw_zone_width_for_sell():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 100.0, 101.0, 99.0, 100.0),
            candle(10, 99.0, 100.0, 91.5, 93.0),
        ],
        activated_at=START + timedelta(minutes=5),
        sizing_reference_price=104.0,
    )

    assert result.entry_reference_price == 100.0
    assert result.risk_unit == 4.0
    assert result.target_2r == 92.0


def test_structural_sizing_reference_for_buy_uses_rejection_low():
    zone = FlipZone(
        id="b1",
        direction=Direction.BUY,
        timeframe=EntryTimeframe.M5,
        lower_price=100.0,
        upper_price=102.0,
        created_at=START,
    )
    result = simulate_historical_outcome(
        zone=zone,
        candles=[
            candle(5, 101.0, 102.0, 100.5, 101.5),
            candle(10, 102.0, 110.5, 101.0, 109.0),
        ],
        activated_at=START + timedelta(minutes=5),
        sizing_reference_price=98.0,
    )

    assert result.entry_reference_price == 102.0
    assert result.risk_unit == 4.0
    assert result.target_2r == 110.0


def test_partial_target_can_remain_open():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 99.5, 100.5, 99.0, 99.5),
            candle(10, 99.5, 100.5, 95.5, 98.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.TARGET_2R
    assert result.terminal is False
    assert result.terminal_reason is None


def test_five_r_is_terminal():
    result = simulate_historical_outcome(
        zone=sell_zone(),
        candles=[
            candle(5, 99.5, 100.5, 99.0, 99.5),
            candle(10, 99.0, 100.0, 89.5, 90.0),
        ],
        activated_at=START + timedelta(minutes=5),
    )

    assert result.status is OutcomeStatus.TARGET_5R
    assert result.terminal is True
    assert result.terminal_reason == "target_5r_reached"

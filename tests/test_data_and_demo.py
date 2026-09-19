from datetime import datetime, timezone

import pytest

from tbot.data.models import RawCandle
from tbot.data.normalize import normalize_candles
from tbot.flip_dip.config import FlipDipConfig
from tbot.flip_dip.demo import DemoEvent, DemoEventType, InMemoryDemoTracker
from tbot.flip_dip.models import (
    Direction,
    EntryTimeframe,
    FlipZone,
    NewsGate,
    SetupState,
    StructureConfirmation,
)
from tbot.flip_dip.planner import FlipDipPlanner
from tbot.flip_dip.risk import calculate_planning_risk
from tbot.flip_dip.runner import ForwardTestRunner


def test_normalize_xauusd_candles():
    rows = [
        RawCandle(
            timestamp=datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc),
            open=3600,
            high=3605,
            low=3598,
            close=3603,
            timeframe="5M",
        )
    ]
    candles = normalize_candles(rows)
    assert candles[0].symbol == "XAUUSD"
    assert candles[0].close == 3603.0


def test_non_xauusd_rejected():
    with pytest.raises(ValueError):
        normalize_candles(
            [
                RawCandle(
                    timestamp=datetime.now(timezone.utc),
                    open=1,
                    high=2,
                    low=0.5,
                    close=1.5,
                    symbol="EURUSD",
                )
            ]
        )


def test_forward_runner_creates_demo_plan_without_execution():
    cfg = FlipDipConfig()
    tracker = InMemoryDemoTracker()
    runner = ForwardTestRunner(
        planner=FlipDipPlanner(cfg),
        tracker=tracker,
    )
    zone = FlipZone(
        id="zone-1",
        direction=Direction.BUY,
        timeframe=EntryTimeframe.M15,
        lower_price=3600,
        upper_price=3602,
        created_at=datetime.now(timezone.utc),
        state=SetupState.WAITING_FOR_RETEST,
    )
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    result = runner.evaluate_retest(
        zone=zone,
        now=now,
        structure=StructureConfirmation(
            confirmed=True,
            timeframe="1H",
            direction=Direction.BUY,
            kind="CHOCH",
        ),
        rejection_is_healthy=True,
        news=NewsGate(clear=True),
        planned_rr=6.0,
    )
    assert result.plan_id is not None
    assert len(tracker.all()) == 1
    assert tracker.get(result.plan_id).events[0].event_type == DemoEventType.PLAN_CREATED


def test_terminal_demo_record_rejects_more_events():
    cfg = FlipDipConfig()
    tracker = InMemoryDemoTracker()
    runner = ForwardTestRunner(planner=FlipDipPlanner(cfg), tracker=tracker)
    zone = FlipZone(
        id="zone-2",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=3600,
        upper_price=3602,
        created_at=datetime.now(timezone.utc),
        state=SetupState.WAITING_FOR_RETEST,
    )
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    result = runner.evaluate_retest(
        zone=zone,
        now=now,
        structure=StructureConfirmation(
            confirmed=True,
            timeframe="15M",
            direction=Direction.SELL,
        ),
        rejection_is_healthy=True,
        news=NewsGate(clear=True),
        planned_rr=5.0,
    )
    tracker.append(
        DemoEvent(
            plan_id=result.plan_id,
            event_type=DemoEventType.INVALIDATED,
            timestamp=now,
        )
    )
    with pytest.raises(ValueError):
        tracker.append(
            DemoEvent(
                plan_id=result.plan_id,
                event_type=DemoEventType.PARTIAL_TP,
                timestamp=now,
            )
        )


def test_risk_is_planning_only():
    risk = calculate_planning_risk(
        account_equity=10_000,
        risk_percent=5,
        entry_price=3600,
        sizing_reference_price=3590,
    )
    assert risk.intended_risk_amount == 500
    assert risk.units_per_price_unit == 50

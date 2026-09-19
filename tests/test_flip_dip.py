from datetime import datetime, timezone

import pytest

from tbot.flip_dip.config import FlipDipConfig
from tbot.flip_dip.models import (
    Direction,
    EntryTimeframe,
    FlipZone,
    NewsGate,
    SetupState,
    StructureConfirmation,
)
from tbot.flip_dip.planner import FlipDipPlanner
from tbot.flip_dip.state_machine import FlipDipStateMachine
from tbot.flip_dip.time_rules import is_within_trading_window


def zone(state=SetupState.WAITING_FOR_RETEST, executions=0):
    return FlipZone(
        id="z1",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=2300.0,
        upper_price=2302.0,
        created_at=datetime.now(timezone.utc),
        state=state,
        execution_count=executions,
    )


def test_istanbul_cross_midnight_window():
    cfg = FlipDipConfig()
    # 21:30 UTC = 00:30 Istanbul (UTC+3), allowed.
    dt = datetime(2026, 9, 19, 21, 30, tzinfo=timezone.utc)
    assert is_within_trading_window(
        dt,
        timezone=cfg.timezone,
        start=cfg.trading_start,
        end=cfg.trading_end,
    )


def test_blocked_between_20_and_23_istanbul():
    cfg = FlipDipConfig()
    # 18:30 UTC = 21:30 Istanbul, blocked.
    dt = datetime(2026, 9, 19, 18, 30, tzinfo=timezone.utc)
    assert not is_within_trading_window(
        dt,
        timezone=cfg.timezone,
        start=cfg.trading_start,
        end=cfg.trading_end,
    )


def test_planner_requires_correct_htf_and_5r():
    cfg = FlipDipConfig()
    planner = FlipDipPlanner(cfg)
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)

    decision = planner.build_plan(
        zone=zone(),
        now=now,
        structure=StructureConfirmation(
            confirmed=True,
            timeframe="15M",
            direction=Direction.SELL,
            kind="BOS",
            observed_at=now,
        ),
        rejection_is_healthy=True,
        news=NewsGate(clear=True),
        planned_rr=5.0,
        sizing_reference_price=2304.0,
    )
    assert decision.plan is not None
    assert decision.plan.execution_number == 1
    assert decision.plan.confirmation_timeframe == "15M"
    assert decision.plan.risk_percent == 5.0
    assert decision.plan.target_5r_price == 2280.0


def test_planner_rejects_below_5r():
    cfg = FlipDipConfig()
    planner = FlipDipPlanner(cfg)
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)

    decision = planner.build_plan(
        zone=zone(),
        now=now,
        structure=StructureConfirmation(
            confirmed=True,
            timeframe="15M",
            direction=Direction.SELL,
            kind="BOS",
            observed_at=now,
        ),
        rejection_is_healthy=True,
        news=NewsGate(clear=True),
        planned_rr=4.99,
        sizing_reference_price=2304.0,
    )
    assert decision.plan is None
    assert "rr_below_minimum" in decision.reasons


def test_third_execution_exhausts_zone():
    cfg = FlipDipConfig()
    sm = FlipDipStateMachine(cfg)
    z = zone(state=SetupState.PLAN_TRACKING, executions=2)
    sm.record_completed_execution(z)
    assert z.execution_count == 3
    assert z.state == SetupState.EXHAUSTED


def test_invalid_state_transition_is_blocked():
    sm = FlipDipStateMachine(FlipDipConfig())
    z = zone(state=SetupState.ZONE_CANDIDATE)
    with pytest.raises(ValueError):
        sm.transition(z, SetupState.PLAN_READY)

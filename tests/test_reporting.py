from datetime import datetime, timezone

from tbot.flip_dip.demo import (
    DemoEvent,
    DemoEventType,
    InMemoryDemoTracker,
)
from tbot.flip_dip.models import (
    Direction,
    EntryTimeframe,
    SetupState,
    TradePlan,
)
from tbot.flip_dip.reporting import summarize_demo


def plan(execution_number: int) -> TradePlan:
    return TradePlan(
        zone_id=f"zone-{execution_number}",
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_timeframe=EntryTimeframe.M5,
        confirmation_timeframe="15M",
        entry_low=3600,
        entry_high=3602,
        invalidation_rule="5M candle CLOSE below the Flip & Dip zone",
        minimum_rr=5,
        risk_percent=5,
        execution_number=execution_number,
        status=SetupState.PLAN_READY,
    )


def test_summary_groups_by_execution_number():
    now = datetime.now(timezone.utc)
    tracker = InMemoryDemoTracker()

    first = tracker.create(plan_id="p1", plan=plan(1), created_at=now)
    second = tracker.create(plan_id="p2", plan=plan(2), created_at=now)

    tracker.append(
        DemoEvent(
            plan_id="p1",
            event_type=DemoEventType.COMPLETED,
            timestamp=now,
            r_multiple=5.0,
        )
    )
    tracker.append(
        DemoEvent(
            plan_id="p2",
            event_type=DemoEventType.INVALIDATED,
            timestamp=now,
            r_multiple=-1.0,
        )
    )

    summary = summarize_demo([first, second])

    assert summary.total_plans == 2
    assert summary.completed == 1
    assert summary.invalidated == 1
    assert summary.realized_r_sum == 4.0
    assert summary.realized_r_average == 2.0
    assert summary.by_execution_number[1]["completed"] == 1
    assert summary.by_execution_number[2]["invalidated"] == 1

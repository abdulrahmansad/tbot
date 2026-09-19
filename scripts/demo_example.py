from datetime import datetime, timezone

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
from tbot.flip_dip.reporting import summarize_demo
from tbot.flip_dip.runner import ForwardTestRunner


def main() -> None:
    config = FlipDipConfig()
    tracker = InMemoryDemoTracker()
    runner = ForwardTestRunner(
        planner=FlipDipPlanner(config),
        tracker=tracker,
    )

    now = datetime.now(timezone.utc)
    zone = FlipZone(
        id="example-zone",
        direction=Direction.SELL,
        timeframe=EntryTimeframe.M5,
        lower_price=3600.0,
        upper_price=3602.0,
        created_at=now,
        state=SetupState.WAITING_FOR_RETEST,
    )

    result = runner.evaluate_retest(
        zone=zone,
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
        sizing_reference_price=3606.0,
    )

    if result.plan_id is None:
        print("NO PLAN:", result.decision.reasons)
        return

    print("DEMO PLAN CREATED:", result.plan_id)
    print(result.decision.plan)

    tracker.append(
        DemoEvent(
            plan_id=result.plan_id,
            event_type=DemoEventType.COMPLETED,
            timestamp=now,
            r_multiple=5.0,
            note="Synthetic example only",
        )
    )

    print(summarize_demo(tracker.all()))


if __name__ == "__main__":
    main()

from datetime import datetime, timedelta, timezone

from tbot.flip_dip.backtest import HistoricalSetup
from tbot.flip_dip.clustering import cluster_ready_setups
from tbot.flip_dip.models import (
    Direction,
    EntryTimeframe,
    FlipZone,
    TradePlan,
)
from tbot.flip_dip.planner import PlanDecision


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def ready_setup(zone_id, retest_minute, rejection, lower, upper):
    zone = FlipZone(
        id=zone_id,
        direction=Direction.BUY,
        timeframe=EntryTimeframe.M5,
        lower_price=lower,
        upper_price=upper,
        created_at=START,
    )
    plan = TradePlan(
        zone_id=zone_id,
        symbol="XAUUSD",
        direction=Direction.BUY,
        entry_timeframe=EntryTimeframe.M5,
        confirmation_timeframe="15M",
        entry_low=lower,
        entry_high=upper,
        invalidation_rule="5M candle CLOSE below the Flip & Dip zone",
        minimum_rr=5.0,
        risk_percent=5.0,
        execution_number=1,
    )
    return HistoricalSetup(
        zone=zone,
        rejection_score=rejection,
        decision=PlanDecision(plan=plan, reasons=()),
        retest_at=START + timedelta(minutes=retest_minute),
    )


def test_same_event_zones_cluster_and_rank_best_rejection_primary():
    setups = [
        ready_setup("z1", 10, 0.80, 100, 102),
        ready_setup("z2", 10, 0.95, 101, 102),
        ready_setup("z3", 30, 0.90, 103, 104),
    ]

    clusters = cluster_ready_setups(setups)

    assert len(clusters) == 2
    assert clusters[0].member_zone_ids == ("z2", "z1")
    assert clusters[0].primary_zone_id == "z2"
    assert clusters[1].member_zone_ids == ("z3",)

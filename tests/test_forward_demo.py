from datetime import datetime, timedelta, timezone

from tbot.flip_dip.backtest import HistoricalSetup
from tbot.flip_dip.models import (
    Candle,
    Direction,
    EntryTimeframe,
    FlipZone,
    TradePlan,
)
from tbot.flip_dip.planner import PlanDecision
from tbot.forward_demo import ForwardDemoService


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeMarketData:
    def fetch_candles(self, *, timeframe, outputsize=500, start=None, end=None):
        step = {"5M": 5, "15M": 15, "1H": 60, "4H": 240}[timeframe]
        return [
            Candle(
                symbol="XAUUSD",
                timeframe=timeframe,
                timestamp=START + timedelta(minutes=step * i),
                open=100,
                high=101,
                low=99,
                close=100,
            )
            for i in range(10)
        ]


class FakeConfig:
    confirmation_timeframe = {"5M": "15M", "15M": "1H", "1H": "4H"}
    news_blackout_before_minutes = 30
    news_blackout_after_minutes = 15


class FakeScanner:
    strategy_config = FakeConfig()

    def scan(self, candles_by_timeframe, *, entry_timeframe, planned_rr):
        zone = FlipZone(
            id=f"stable-{entry_timeframe}",
            direction=Direction.BUY,
            timeframe=EntryTimeframe(entry_timeframe),
            lower_price=99,
            upper_price=100,
            created_at=START,
        )
        plan = TradePlan(
            zone_id=zone.id,
            symbol="XAUUSD",
            direction=Direction.BUY,
            entry_timeframe=EntryTimeframe(entry_timeframe),
            confirmation_timeframe=self.strategy_config.confirmation_timeframe[entry_timeframe],
            entry_low=99,
            entry_high=100,
            invalidation_rule=f"{entry_timeframe} candle CLOSE below the Flip & Dip zone",
            minimum_rr=5,
            risk_percent=5,
            execution_number=1,
        )
        entry = candles_by_timeframe[entry_timeframe]
        return [
            HistoricalSetup(
                zone=zone,
                rejection_score=0.9,
                decision=PlanDecision(plan=plan, reasons=()),
                retest_at=entry[-1].timestamp,
            )
        ]


def make_service(tmp_path):
    service = ForwardDemoService(
        market_data=FakeMarketData(),
        plans_path=tmp_path / "plans.jsonl",
        seen_path=tmp_path / "seen.json",
        snapshot_path=tmp_path / "live.json",
    )
    service.scanner = FakeScanner()
    return service


def test_forward_demo_records_fresh_plan_once(tmp_path):
    service = make_service(tmp_path)

    first = service.poll_once(entry_timeframes=("5M",), now=START)
    second = service.poll_once(entry_timeframes=("5M",), now=START)

    assert first.created_plan_ids == ("demo-stable-5M",)
    assert second.created_plan_ids == ()
    rows = service.store.read_raw()
    assert len(rows) == 1
    assert rows[0]["plan_id"] == "demo-stable-5M"


def test_forward_demo_writes_live_snapshot(tmp_path):
    service = make_service(tmp_path)

    service.poll_once(entry_timeframes=("5M",), now=START)

    import json

    payload = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    assert payload["execution_enabled"] is False
    assert payload["timeframes"]["5M"]["status"] == "ok"
    assert payload["timeframes"]["5M"]["ready_primary_count"] == 1
    assert payload["timeframes"]["5M"]["latest_ready_plan"]["zone_id"] == "stable-5M"

from datetime import datetime, timedelta, timezone

from tbot.demo_session import DemoSession, DemoSessionStore
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
from tbot.news import EconomicEvent, Impact


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
    timezone = "Europe/Istanbul"
    from datetime import time as _time
    trading_start = _time(23, 0)
    trading_end = _time(20, 0)
    strategy_contract_version = "owner-flip-dip-2026-09-19"
    primary_entry_timeframes = ("5M", "15M")


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
        session_path=tmp_path / "session.json",
    )
    service.scanner = FakeScanner()
    return service


def test_forward_demo_records_fresh_plan_once(tmp_path):
    service = make_service(tmp_path)

    first = service.poll_once(entry_timeframes=("5M",), now=START)
    second = service.poll_once(entry_timeframes=("5M",), now=START)

    assert first.created_plan_ids == ("demo-stable-5M-e1",)
    assert second.created_plan_ids == ()
    rows = service.store.read_raw()
    assert len(rows) == 1
    assert rows[0]["plan_id"] == "demo-stable-5M-e1"


def test_forward_demo_writes_live_snapshot(tmp_path):
    service = make_service(tmp_path)

    service.poll_once(entry_timeframes=("5M",), now=START)

    import json

    payload = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    assert payload["execution_enabled"] is False
    assert payload["timeframes"]["5M"]["status"] == "ok"
    assert payload["timeframes"]["5M"]["ready_primary_count"] == 1
    assert payload["timeframes"]["5M"]["latest_ready_plan"]["zone_id"] == "stable-5M"


class FakeCalendar:
    def fetch_events(self, *, start, end):
        return [
            EconomicEvent(
                title="CPI",
                scheduled_at=START + timedelta(minutes=45),
                impact=Impact.HIGH,
                currency="USD",
                xauusd_relevant=True,
            )
        ]


def test_forward_demo_blocks_setup_if_retest_was_inside_news_blackout(tmp_path):
    service = ForwardDemoService(
        market_data=FakeMarketData(),
        calendar=FakeCalendar(),
        plans_path=tmp_path / "plans.jsonl",
        seen_path=tmp_path / "seen.json",
        snapshot_path=tmp_path / "live.json",
    )
    service.scanner = FakeScanner()

    # Fake 5M setup retest occurs at START+45m. Poll at +70m, which is outside
    # the current +15m blackout, to prove the setup is checked at retest time.
    result = service.poll_once(
        entry_timeframes=("5M",),
        fresh_bars=6,
        now=START + timedelta(minutes=70),
    )

    assert result.fresh_primary_count == 1
    assert result.created_plan_ids == ()
    assert result.news_clear is True

def test_live_snapshot_hides_stale_ready_plan(tmp_path):
    service = make_service(tmp_path)
    service.poll_once(
        entry_timeframes=("5M",),
        now=START + timedelta(hours=2),
    )

    import json

    payload = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    tf = payload["timeframes"]["5M"]
    assert tf["ready_primary_count"] == 1
    assert tf["fresh_primary_count"] == 0
    assert tf["latest_ready_plan"] is None


class ThreeExecutionScanner:
    strategy_config = FakeConfig()

    def scan(self, candles_by_timeframe, *, entry_timeframe, planned_rr):
        output = []
        for execution_number, minute in ((1, 15), (2, 30), (3, 45)):
            zone = FlipZone(
                id="same-zone",
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
                confirmation_timeframe="15M",
                entry_low=99,
                entry_high=100,
                invalidation_rule="5M candle CLOSE below the Flip & Dip zone",
                minimum_rr=5,
                risk_percent=5,
                execution_number=execution_number,
            )
            output.append(
                HistoricalSetup(
                    zone=zone,
                    rejection_score=0.9,
                    decision=PlanDecision(plan=plan, reasons=()),
                    execution_number=execution_number,
                    retest_at=START + timedelta(minutes=minute),
                )
            )
        return output


def test_forward_demo_persists_three_execution_ids_once(tmp_path):
    service = make_service(tmp_path)
    service.scanner = ThreeExecutionScanner()

    first = service.poll_once(
        entry_timeframes=("5M",),
        fresh_bars=10,
        now=START + timedelta(minutes=45),
    )
    second = service.poll_once(
        entry_timeframes=("5M",),
        fresh_bars=10,
        now=START + timedelta(minutes=45),
    )

    assert first.created_plan_ids == (
        "demo-same-zone-e1",
        "demo-same-zone-e2",
        "demo-same-zone-e3",
    )
    assert second.created_plan_ids == ()
    rows = service.store.read_raw()
    assert [row["plan_id"] for row in rows] == [
        "demo-same-zone-e1",
        "demo-same-zone-e2",
        "demo-same-zone-e3",
    ]


def test_scheduled_demo_session_blocks_new_plans(tmp_path):
    service = make_service(tmp_path)
    DemoSessionStore(tmp_path / "session.json").write(
        DemoSession(
            name="Future Demo",
            start=START + timedelta(hours=2),
            end=START + timedelta(days=1),
        )
    )

    result = service.poll_once(entry_timeframes=("5M",), now=START)

    assert result.created_plan_ids == ()
    import json
    snapshot = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    assert snapshot["demo_session"]["status"] == "SCHEDULED"


def test_active_demo_session_tags_created_plan(tmp_path):
    service = make_service(tmp_path)
    DemoSessionStore(tmp_path / "session.json").write(
        DemoSession(
            name="Friend Week 1",
            start=START - timedelta(hours=1),
            end=START + timedelta(days=1),
        )
    )

    result = service.poll_once(entry_timeframes=("5M",), now=START)
    assert result.created_plan_ids == ("demo-stable-5M-e1",)

    rows = service.store.read_raw()
    assert rows[0]["session_name"] == "Friend Week 1"
    assert rows[0]["session_start"] is not None
    assert rows[0]["session_end"] is not None


def test_market_status_reports_closed_or_stale(tmp_path):
    service = make_service(tmp_path)

    service.poll_once(
        entry_timeframes=("5M",),
        now=START + timedelta(hours=2),
    )

    import json
    snapshot = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    assert snapshot["market_status"] == "CLOSED_OR_STALE"
    assert snapshot["market_data_age_seconds"] > 20 * 60

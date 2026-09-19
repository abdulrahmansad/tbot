import json
from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle
from tbot.forward_tracking import ForwardOutcomeTracker


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeMarketData:
    def fetch_candles(self, *, timeframe, outputsize=1000, start=None, end=None):
        rows = [
            (100, 101, 99, 100),
            (100, 100.5, 99, 99.5),
            (99.5, 100.5, 95.5, 98),
            (98, 103.5, 97, 103),
        ]
        return [
            Candle(
                symbol="XAUUSD",
                timeframe=timeframe,
                timestamp=START + timedelta(minutes=5 * i),
                open=o,
                high=h,
                low=l,
                close=c,
            )
            for i, (o, h, l, c) in enumerate(rows)
        ]


def test_forward_tracker_updates_plan_outcome(tmp_path):
    plans_path = tmp_path / "plans.jsonl"
    plans_path.write_text(
        json.dumps(
            {
                "plan_id": "demo-z1",
                "created_at": (START + timedelta(minutes=5)).isoformat(),
                "plan": {
                    "zone_id": "z1",
                    "direction": "SELL",
                    "entry_timeframe": "5M",
                    "confirmation_timeframe": "15M",
                    "entry_low": 100.0,
                    "entry_high": 102.0,
                    "invalidation_rule": "5M candle CLOSE above the Flip & Dip zone",
                    "minimum_rr": 5.0,
                    "risk_percent": 5.0,
                    "execution_number": 1,
                },
                "events": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    tracker = ForwardOutcomeTracker(
        market_data=FakeMarketData(),
        plans_path=plans_path,
        results_path=tmp_path / "results.json",
    )

    result = tracker.update()

    assert result["demo-z1"]["outcome_status"] == "TARGET_2R"
    assert result["demo-z1"]["terminal"] is True
    assert result["demo-z1"]["terminal_reason"] == "invalidated_after_2r"
    assert result["demo-z1"]["max_favorable_r"] >= 2.0

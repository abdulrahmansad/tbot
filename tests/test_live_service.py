from datetime import datetime, timedelta, timezone

from tbot.flip_dip.models import Candle
from tbot.live import LivePlanningService


class FakeProvider:
    def fetch_candles(self, *, timeframe, outputsize=500, start=None, end=None):
        step = 5 if timeframe == "5M" else 15
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = []
        price = 100.0
        for i in range(40):
            o = price
            h = price + (2 if i % 7 == 0 else 1)
            l = price - (2 if i % 9 == 0 else 1)
            c = price + (0.5 if i % 2 == 0 else -0.5)
            rows.append(
                Candle(
                    symbol="XAUUSD",
                    timeframe=timeframe,
                    timestamp=base + timedelta(minutes=step * i),
                    open=o,
                    high=max(h, o, c),
                    low=min(l, o, c),
                    close=c,
                )
            )
            price = c
        return rows


def test_live_service_scans_without_execution():
    service = LivePlanningService(market_data=FakeProvider())
    result = service.scan_once(entry_timeframe="5M", bars=40)
    assert result.entry_timeframe == "5M"
    assert result.confirmation_timeframe == "15M"
    assert result.candidate_count >= 0
    assert result.ready_count >= 0

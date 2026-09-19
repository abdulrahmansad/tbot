from datetime import datetime, timedelta, timezone

from tbot.flip_dip.backtest import ProvisionalBacktester
from tbot.flip_dip.models import Candle


def candles(tf: str, minutes: int, rows: list[tuple[float, float, float, float]]):
    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    return [
        Candle(
            symbol="XAUUSD",
            timeframe=tf,
            timestamp=start + timedelta(minutes=minutes * i),
            open=o,
            high=h,
            low=l,
            close=c,
        )
        for i, (o, h, l, c) in enumerate(rows)
    ]


def test_end_to_end_scan_returns_inspectable_setups():
    entry_rows = [
        (100, 101, 99, 100),
        (100, 102, 99, 101),
        (101, 105, 100, 104),
        (104, 104.5, 101, 102),
        (102, 103, 100, 101),
        (101, 106, 100.5, 105),
        (105, 106.5, 102, 103),
        (103, 104, 99, 100),
        (100, 102, 98, 99),
        (99, 103.5, 98.5, 100),
        (100, 101, 97, 98),
        (98, 99, 96, 97),
    ]
    htf_rows = [
        (100, 104, 98, 102),
        (102, 105, 100, 104),
        (104, 104.5, 99, 100),
        (100, 101, 96, 97),
        (97, 98, 94, 95),
        (95, 96, 92, 93),
        (93, 94, 90, 91),
        (91, 92, 89, 90),
    ]

    scanner = ProvisionalBacktester()
    setups = scanner.scan(
        {
            "5M": candles("5M", 5, entry_rows),
            "15M": candles("15M", 15, htf_rows),
        },
        entry_timeframe="5M",
        planned_rr=5.0,
    )

    assert isinstance(setups, list)
    for setup in setups:
        assert 0.0 <= setup.rejection_score <= 1.0
        assert setup.decision.plan is not None or setup.decision.reasons

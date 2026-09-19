from datetime import datetime, timedelta, timezone

import pytest

from tbot.flip_dip.models import Candle
from tbot.historical_test import HistoricalTestRequest, HistoricalTestService


START = datetime(2026, 1, 5, tzinfo=timezone.utc)


class FakeMarketData:
    def __init__(self):
        self.calls = []

    def fetch_candles(self, *, timeframe, outputsize=500, start=None, end=None):
        self.calls.append(timeframe)
        step = {"5M": 5, "15M": 15, "1H": 60, "4H": 240}[timeframe]
        rows = []
        moment = start or START
        limit = end or (moment + timedelta(hours=12))
        price = 100.0
        while moment <= limit and len(rows) < 500:
            rows.append(
                Candle(
                    symbol="XAUUSD",
                    timeframe=timeframe,
                    timestamp=moment,
                    open=price,
                    high=price + 1,
                    low=price - 1,
                    close=price + (0.2 if len(rows) % 2 == 0 else -0.2),
                )
            )
            price = rows[-1].close
            moment += timedelta(minutes=step)
        return rows


class FakeCalendar:
    def fetch_events(self, *, start, end):
        return []


def test_historical_test_fetches_each_required_timeframe_once():
    market = FakeMarketData()
    service = HistoricalTestService(market_data=market, calendar=FakeCalendar())

    result = service.run(
        HistoricalTestRequest(
            start=START,
            end=START + timedelta(days=2),
            starting_balance=100,
            risk_percent=5,
        )
    )

    assert result["status"] == "ok"
    assert result["news_filter_applied"] is True
    assert set(market.calls) == {"5M", "15M", "1H"}
    assert len(market.calls) == 3
    assert set(result["timeframes"]) == {"5M", "15M"}
    assert result["account_scenario"]["ending_balance"] >= 0


def test_historical_test_rejects_more_than_fourteen_days():
    service = HistoricalTestService(
        market_data=FakeMarketData(),
        calendar=FakeCalendar(),
    )
    with pytest.raises(ValueError, match="14 days"):
        service.run(
            HistoricalTestRequest(
                start=START,
                end=START + timedelta(days=15),
            )
        )


def test_historical_test_enforces_five_percent_risk_cap():
    service = HistoricalTestService(
        market_data=FakeMarketData(),
        calendar=FakeCalendar(),
    )
    with pytest.raises(ValueError, match="<= 5"):
        service.run(
            HistoricalTestRequest(
                start=START,
                end=START + timedelta(days=1),
                risk_percent=5.1,
            )
        )


def test_historical_test_can_include_secondary_1h():
    market = FakeMarketData()
    service = HistoricalTestService(market_data=market, calendar=FakeCalendar())

    result = service.run(
        HistoricalTestRequest(
            start=START,
            end=START + timedelta(days=2),
            include_1h=True,
        )
    )

    assert set(result["timeframes"]) == {"5M", "15M", "1H"}
    assert set(market.calls) == {"5M", "15M", "1H", "4H"}

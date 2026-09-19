from datetime import datetime, timedelta, timezone

from tbot.data.cached import TimeframeCachedMarketDataProvider
from tbot.flip_dip.models import Candle


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


class Upstream:
    def __init__(self):
        self.calls = 0

    def fetch_candles(self, *, timeframe, outputsize=500, start=None, end=None):
        self.calls += 1
        return [
            Candle(
                symbol="XAUUSD",
                timeframe=timeframe,
                timestamp=START + timedelta(minutes=i),
                open=100,
                high=101,
                low=99,
                close=100,
            )
            for i in range(outputsize)
        ]


def test_cache_reuses_live_request_inside_same_timeframe_bucket():
    upstream = Upstream()
    now = [START + timedelta(minutes=1)]
    provider = TimeframeCachedMarketDataProvider(
        upstream,
        now_fn=lambda: now[0],
    )

    provider.fetch_candles(timeframe="5M", outputsize=100)
    provider.fetch_candles(timeframe="5M", outputsize=100)

    assert upstream.calls == 1


def test_cache_refreshes_when_timeframe_bucket_changes():
    upstream = Upstream()
    now = [START + timedelta(minutes=1)]
    provider = TimeframeCachedMarketDataProvider(
        upstream,
        now_fn=lambda: now[0],
    )

    provider.fetch_candles(timeframe="5M", outputsize=100)
    now[0] = START + timedelta(minutes=6)
    provider.fetch_candles(timeframe="5M", outputsize=100)

    assert upstream.calls == 2


def test_cache_shares_confirmation_timeframe_between_scans():
    upstream = Upstream()
    provider = TimeframeCachedMarketDataProvider(
        upstream,
        now_fn=lambda: START + timedelta(minutes=16),
    )

    provider.fetch_candles(timeframe="15M", outputsize=500)
    provider.fetch_candles(timeframe="15M", outputsize=500)

    assert upstream.calls == 1


def test_ranged_request_bypasses_live_cache():
    upstream = Upstream()
    provider = TimeframeCachedMarketDataProvider(
        upstream,
        now_fn=lambda: START,
    )

    provider.fetch_candles(timeframe="5M", outputsize=10, start=START)
    provider.fetch_candles(timeframe="5M", outputsize=10, start=START)

    assert upstream.calls == 2

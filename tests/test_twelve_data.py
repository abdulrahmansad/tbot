import json

import pytest

from tbot.data.twelve_data import TwelveDataError, TwelveDataXauUsdProvider


def fake_response(url: str) -> bytes:
    assert "symbol=XAU%2FUSD" in url
    assert "interval=5min" in url
    assert "timezone=UTC" in url
    return json.dumps(
        {
            "status": "ok",
            "values": [
                {
                    "datetime": "2026-09-19 10:00:00",
                    "open": "3600.10",
                    "high": "3605.20",
                    "low": "3598.40",
                    "close": "3603.70",
                }
            ],
        }
    ).encode()


def test_twelve_data_normalizes_xauusd():
    provider = TwelveDataXauUsdProvider("test-key", http_get=fake_response)
    candles = provider.fetch_candles(timeframe="5M", outputsize=1)
    assert len(candles) == 1
    assert candles[0].symbol == "XAUUSD"
    assert candles[0].timeframe == "5M"
    assert candles[0].close == 3603.70
    assert candles[0].timestamp.tzinfo is not None


def test_provider_requires_key_when_env_missing(monkeypatch):
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    monkeypatch.setattr("tbot.data.twelve_data.load_dotenv", lambda: False)
    with pytest.raises(ValueError):
        TwelveDataXauUsdProvider(api_key="")


def test_provider_surfaces_api_error():
    def fail(url: str) -> bytes:
        return json.dumps({"status": "error", "message": "bad key"}).encode()

    provider = TwelveDataXauUsdProvider("x", http_get=fail)
    with pytest.raises(TwelveDataError):
        provider.fetch_candles(timeframe="15M")

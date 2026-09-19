# tbot — XAUUSD Flip & Dip Planner

Phase 0 is a **trade-planning and demo-tracking engine** for the owner's XAUUSD Flip & Dip strategy.

**It does not place trades.**

## What exists now

- XAUUSD-only domain model
- 5M, 15M, 1H, 4H candle support
- 5M→15M, 15M→1H, 1H→4H confirmation mapping
- Flip & Dip state machine
- max 3 executions per zone
- candle-close invalidation
- minimum 5R gate
- configurable 5% planning risk
- Istanbul 23:00→20:00 trading window
- high-impact USD news blackout engine
- demo/forward-test event tracking
- JSONL persistence and summary reporting
- Twelve Data XAU/USD adapter
- CI tests

## Strategy boundary

The strategy deliberately excludes liquidity sweeps, equal highs/lows, previous day/session highs/lows, liquidity pools, RSI, MACD, moving averages, Fibonacci, volume indicators, and unrelated SMC rules.

Flip Zone recognition, rejection quality, and CHoCH/BOS interpretation are **not guessed**. They remain unvalidated detector interfaces until owner-approved chart examples are supplied.

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
pytest -q
```

## Market data

Copy `.env.example` to `.env` and add a Twelve Data API key when live/historical API testing begins.

The data adapter converts provider symbol `XAU/USD` to internal `XAUUSD` and normalizes timestamps to UTC.

## Demo mode

`scripts/demo_example.py` demonstrates a synthetic plan. It does not connect to a broker.

Manual calibration scenarios can be stored as JSON using `examples/manual_scenario.json`.

## Documentation

- `docs/STRATEGY_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_PROVIDER.md`
- `docs/DEMO_PROTOCOL.md`
- `docs/STATUS.md`

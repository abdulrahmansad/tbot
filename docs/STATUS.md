# Project Status

## 2026-09-19 — Phase 0B provisional automation

### Implemented and tested

- repository and CI
- immutable Flip & Dip strategy contract
- XAUUSD-only configuration
- 5M / 15M / 1H / 4H candle support
- required higher-timeframe confirmation mapping
- Istanbul 23:00 → 20:00 trading-window handling
- maximum three executions per zone
- minimum 5R plan gate
- 5% configurable planning-risk model
- candle-close invalidation
- high-impact USD news-blackout engine
- demo/forward-test event tracking
- JSONL demo persistence and summary reporting
- provider-neutral market-data layer
- Twelve Data XAU/USD adapter
- manual calibration scenarios
- provisional v0 Flip Zone detector
- provisional v0 rejection scorer
- provisional v0 pivot-based higher-timeframe structure detector
- retest-from-correct-side detector
- historical setup scanner
- command-line historical scan tool

### Important status distinction

The software can now generate automated provisional Flip & Dip candidates.

It is NOT yet correct to call those candidates the trader's final strategy signals.

The current Flip Zone, rejection, and structure rules are temporary v0 definitions created because owner-approved chart examples are unavailable. They are intentionally configurable and replaceable.

### Still required before demo week

1. Run historical XAUUSD scans using a real API key/data feed.
2. Inspect generated setups on charts or exported examples.
3. Tune provisional parameters until the setups are plausible.
4. Decide/finalize partial TP levels and percentages.
5. Add an economic-calendar data adapter.
6. Add a live polling service.
7. Freeze a named strategy version.
8. Start the one-week demo/forward test.

### Not part of Phase 0

- broker order placement
- automatic execution
- liquidity-sweep logic
- RSI/MACD/MA/Fibonacci/volume strategy additions

The bot remains a planner and hypothetical tracker only.

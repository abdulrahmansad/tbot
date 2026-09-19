# Project Status

## 2026-09-19 — Phase 0 foundation

Implemented:
- repository initialized
- strategy contract documented
- XAUUSD-only strategy config
- 5M / 15M / 1H / 4H timeframe model
- required HTF confirmation mapping
- 23:00 → 20:00 Istanbul cross-midnight trading window
- Flip & Dip lifecycle state machine
- maximum-three-execution enforcement
- deterministic trade-plan gate
- minimum 5R requirement
- 5% planning-risk model
- explicit candle-close invalidation
- high-impact USD news blackout engine
- normalized OHLC candle model
- provider-neutral market-data interface
- Twelve Data XAU/USD adapter
- manual calibration scenario loader
- in-memory demo/forward-test tracker
- append-only JSONL demo persistence
- demo reporting with execution #1/#2/#3 breakdown
- runnable synthetic demo example
- CI test workflow
- owner-specific detector interfaces
- explicit failures for unvalidated subjective rules

Still intentionally unimplemented:
- automated Flip Zone recognition
- automated rejection-quality recognition
- automated CHoCH/BOS recognition
- final TP ladder/partial percentages
- external economic-calendar provider
- API/web dashboard
- live polling scheduler

Blocked on owner calibration examples:
- exact Flip Zone visual definition
- healthy vs weak rejection examples
- exact CHoCH/BOS swing interpretation

Current rule:
The software may run manual/synthetic planning scenarios, but it must not claim automated strategy accuracy until the three subjective detectors above are calibrated.

Next build:
1. calibrate Flip Zone detector from screenshots
2. calibrate rejection evaluator
3. calibrate CHoCH/BOS detector
4. add TP plan once owner method is fixed
5. connect live XAU/USD polling
6. begin demo week

# Project Status

## 2026-09-19 — Phase 0C calibration + hosted demo foundation

### Implemented and tested

- repository and GitHub Actions CI
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
- provider-neutral market-data layer
- Twelve Data XAU/USD adapter
- automatic .env loading for local development
- deterministic Flip Zone IDs across repeated scans
- provisional v0 Flip Zone detector
- provisional v0 rejection scorer
- provisional v0 pivot-based higher-timeframe structure detector
- sequential HTF confirmation between return and retest
- correct-side retest detector
- overlapping-zone deduplication
- event-level clustering for concurrent READY zones
- historical setup scanner
- conservative historical outcome simulator
- 2R / 3.5R / 5R calibration targets
- explicit AMBIGUOUS status when OHLC cannot determine intrabar order
- max favorable/adverse R audit metrics
- richer CSV/JSON calibration exports
- one-command 5M / 15M / 1H full calibration runner
- demo/forward-test event tracking
- JSONL demo persistence
- persistent forward-demo discovery with seen-zone deduplication
- forward-demo outcome tracking
- read-only FastAPI dashboard API
- responsive Live / Plans / Performance / History dashboard shell
- Docker deployment
- two-service Compose runtime: web + monitoring worker
- server-side secret architecture; no market-data key is exposed to browser code

### Real-data calibration completed

The first real Twelve Data calibration bundle completed successfully before
outcome tracking was added:

- 5M → 15M: 146 candidates / 19 READY
- 15M → 1H: 130 candidates / 14 READY
- 1H → 4H: 142 candidates / 26 READY
- total: 418 candidates / 59 READY zones

That bundle exposed multi-zone clustering behavior and informed the new event
clustering layer.

### Important status distinction

The software now has a functioning detector, real-data scan path, historical
outcome engine, forward-demo worker, persistence, API, and dashboard shell.

It is still NOT correct to call provisional v0 a final or validated strategy.

The current Flip Zone, rejection, structure, event-ranking and calibration R
rules remain provisional until the enhanced outcome calibration is rerun and
reviewed.

### Next required calibration run

Run the updated full calibration after pulling the latest code:

python scripts/run_full_calibration.py

The new bundle will include:

- retest timestamps
- HTF structure confirmation timestamps
- cluster IDs/ranks/primary-zone labels
- entry reference and provisional zone-width R unit
- 2R / 3.5R / 5R targets
- max favorable/adverse R
- outcome status
- ambiguity flags

This enhanced bundle is required before detector tuning and v1 freeze.

### Remaining before one-week public demo

1. Review enhanced historical outcomes by timeframe/direction.
2. Tune detector and event-ranking rules from evidence.
3. Decide/finalize partial TP percentages if the provisional model changes.
4. Add a real economic-calendar provider adapter.
5. Freeze a named calibrated strategy version.
6. Run the forward-demo worker against fresh XAUUSD data.
7. Review one-week forward results.
8. Deploy web + worker with server-side secrets.
9. Expose the Phase 0 dashboard to invited users.

### Explicitly excluded

- broker order placement
- automatic execution
- assisted execution buttons
- liquidity-sweep logic
- RSI
- MACD
- moving averages
- Fibonacci
- volume strategy additions

TBOT remains a planning and hypothetical tracking system only.


## 2026-09-19 — Stabilized-risk calibration findings

The first calibration using the stabilized structural risk model removed the
previous unrealistic 100R-300R artifacts. Primary-event MFE is now within a
credible range for this sample.

Current evidence does NOT support raising the rejection-score threshold as a
hard filter.

A persistent calibration warning was observed for 1H BUY setups: zero 5R
outcomes occurred in both chronological halves of the current sample. This is
not yet a strategy rule. It must be tested on a second independent historical
window before 1H BUY can be restricted or disabled.

No timeframe/direction hard gate should be added from one sample alone.

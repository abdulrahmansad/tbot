# Project Status

## 2026-09-19 — Flip & Dip V1 candidate / private forward-demo readiness

### Current strategy version

flip-dip-v1-candidate

State:

REVIEW_REQUIRED

The candidate is historically calibrated enough to begin forward-demo
validation. It is not owner-approved and no profitability claim is made.

### Implemented and tested

- immutable Flip & Dip strategy contract
- XAUUSD-only scope
- 5M / 15M / 1H entry timeframes
- 15M / 1H / 4H confirmation mapping
- strict event chronology:
  - confirmed pivot
  - trade through zone
  - return through zone
  - rejection window completion
  - HTF BOS confirmation at candle close
  - later retest
  - plan ready
  - future-candle outcome tracking only
- deterministic zone IDs
- overlap deduplication
- event-level multi-zone clustering
- primary-zone ranking
- Istanbul trading-window handling
- high-impact USD news blackout
- FMP economic-calendar adapter
- free FinanceCalendar fallback adapter
- automatic calendar provider fallback
- cached economic-calendar provider
- candle-close invalidation
- minimum 5R gate
- maximum three planned executions per zone
- configurable 5% planning risk
- stabilized structural sizing model
- recent 20-candle median-range risk floor
- 2R / 3.5R / 5R calibration milestones
- explicit intrabar AMBIGUOUS handling
- separate milestone status vs terminal outcome state
- MFE / MAE audit metrics
- CSV/JSON calibration export
- 1,000-bar and 2,000-bar calibration modes
- repeatable calibration analysis report
- calibration-quality readiness gate
- forward-demo plan discovery
- duplicate-plan prevention
- persistent plan/result storage
- forward outcome tracking
- worker-produced live snapshot
- worker heartbeat freshness detection
- read-only FastAPI dashboard API
- responsive Live / Plans / Performance / History UI
- v1 candidate metadata surfaced in dashboard
- Docker runtime
- web + worker Compose deployment
- worker-only market-data/news secrets
- timeframe-aware Twelve Data cache
- candle-publication grace period
- optional private-dashboard HTTP Basic protection
- no broker execution code or execution endpoints

### 2,000-bar validation

Sample label:

validation-2000

Risk model:

structural_rejection_plus_median20_range_floor

Primary independent events:

- 5M -> 15M: 67
- 15M -> 1H: 73
- 1H -> 4H: 75
- total: 215

Primary outcomes:

- TARGET_5R: 46
- TARGET_3_5R: 13
- TARGET_2R: 23
- INVALIDATED: 131
- AMBIGUOUS: 2

These are historical diagnostic outcomes, not broker-realized P&L.

### Calibration conclusions

- the previous unrealistic 100R-300R normalization artifacts were removed,
- rejection score does not justify a higher universal hard threshold,
- no BUY/SELL or timeframe hard filter is promoted from the historical sample,
- the earlier 1H BUY weakness was not stable across the expanded window,
- the existing cluster ranking remains adequate for the v1 candidate,
- the corrected detector is frozen for forward-demo testing instead of further
  historical curve-fitting.

See:

docs/V1_VALIDATION_2000.md

### Live architecture

Production/private-demo flow:

worker
-> Twelve Data + economic calendar
-> shared runtime snapshot/results
-> web API
-> dashboard

The web service does not call Twelve Data in production.

### API quota design

The timeframe-aware market-data cache refreshes approximately:

- 5M: once per 5-minute bucket
- 15M: once per 15-minute bucket
- 1H: once per hour
- 4H: once per four hours

Confirmation-timeframe data is shared between scans.

The economic calendar is cached for 10 minutes.

### Current deployment boundary

The current build is intended for private/internal forward-demo validation.

Before public/external display, confirm that the selected market-data
license/provider permits the intended external display/commercial usage.

See:

docs/DATA_LICENSING.md

### Remaining before owner approval

1. Run the forward-demo worker continuously against fresh XAUUSD data. FMP is optional; FinanceCalendar provides the built-in free fallback.
2. Observe which calendar provider is active in the dashboard/health output.
3. Observe and review the planned one-week forward-demo period.
4. Review terminal outcomes, partial milestones, MFE/MAE and operational logs.
5. Decide whether provisional TP percentages remain or need owner adjustment.
6. Confirm market-data licensing before public/external display.
7. Only then consider moving the strategy from REVIEW_REQUIRED to
   OWNER_APPROVED.

### Explicitly excluded

- broker order placement
- automatic execution
- assisted execution buttons
- liquidity-sweep strategy logic
- RSI
- MACD
- moving averages
- Fibonacci
- volume strategy additions

TBOT remains a planning and hypothetical tracking system only.

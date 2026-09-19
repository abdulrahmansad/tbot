# Phase 0 Product Review — Expert + End User

Date: 2026-09-19

## Phase 0 product goal

Phase 0 is not just a detector. It is a usable single-strategy laboratory for
the owner's XAUUSD Flip & Dip strategy.

A normal user should be able to:

1. Understand which strategy/version is active.
2. Choose a historical From/To interval.
3. Enter a starting balance and risk up to the 5% strategy cap.
4. Run the exact same Flip & Dip logic on that interval.
5. See setups, execution #1/#2/#3, outcomes, drawdown and a clearly labeled
   account scenario.
6. Start a named forward-demo session with start/end dates.
7. Leave the worker running while the session moves through
   SCHEDULED -> ACTIVE -> ENDED.
8. See whether the market is OPEN or CLOSED/DATA STALE.
9. Separately see whether the strategy trading window is open.
10. Separately see whether high-impact news blocks new entries.
11. See new READY plans generated from the strategy without any broker order.
12. Review only the plans/outcomes belonging to the selected demo session.

## Expert audit findings

### Previously strong

- strict strategy sequence and no-lookahead handling
- XAUUSD scope
- higher-timeframe structure mapping
- correct-side retest logic
- max three execution identities
- candle-close invalidation
- 5% risk cap
- minimum 5R target
- historical calibration/readiness gate
- forward tracking
- news protection
- execution-disabled boundary

### Previously weak from an end-user perspective

- historical testing was tied to a fixed calibration sample instead of a
  user-selected date range
- no bounded demo-session concept
- market closure/stale-data state was implicit
- session results could mix between demo periods
- Live did not explain why no plan was shown
- 1H existed in the engine but appeared missing in the UI
- review metrics were too aggregate for execution #1/#2/#3 analysis

## Phase 0 upgrades

- Test Strategy tab with From/To, starting balance, risk and optional secondary
  1H mode
- on-demand historical replay using the authoritative strategy contract
- per-test timeframe/outcome/setup summaries
- account milestone scenario and drawdown
- 14-day interactive limit to avoid silent 5M truncation under the Phase 0
  provider response cap
- shared historical timeframe fetches are de-duplicated
- Demo tab with named start/end sessions
- deterministic session IDs
- forward plans tagged to their exact session
- session-specific plan/outcome summary
- market status: OPEN / CLOSED_OR_STALE / UNKNOWN
- separate strategy trading-window status
- separate news-gate status and next high-impact USD event
- Live explanations for no-plan states
- 1H displayed as a supported secondary entry mode
- performance breakdown by timeframe, direction and execution number
- Review tab for strategy contract/readiness

## Important limitation

The owner has not yet supplied the exact partial take-profit percentages and
levels.

Therefore account outputs are still milestone-payout scenarios, not exact
broker-realized strategy P&L. This is shown explicitly in the product.

## Phase 0 launch boundary

Phase 0 is ready for live forward-demo use when:

- authoritative calibration is ready
- preflight returns ready=true
- worker is healthy
- local interactive server is healthy
- historical Test Strategy workflow passes a smoke test
- a bounded Demo session can be created
- Live correctly reports current market/window/news state
- no broker execution surface exists
- CI is green

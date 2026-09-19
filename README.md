# tbot — XAUUSD Flip & Dip Planner

Phase 0 is a **trade-planning and demo-tracking engine** for the owner's XAUUSD Flip & Dip strategy.

It does **not** place trades.

## Phase 0 goals

- XAUUSD only
- 5M, 15M, 1H, 4H
- deterministic strategy state machine
- higher-timeframe CHoCH/BOS confirmation mapping
- maximum 3 executions per zone
- candle-close invalidation
- minimum 5R planned reward
- configurable 5% risk model
- Istanbul trading window 23:00 → 20:00
- high-impact news gate
- demo/forward-test logging
- no liquidity concepts or unrelated indicators

## Important

Flip-zone detection, rejection quality, and CHoCH/BOS definitions remain explicit strategy interfaces until they are calibrated from owner-approved chart examples. The engine must never silently invent those rules.

See `docs/STRATEGY_SPEC.md`, `docs/ARCHITECTURE.md`, and `docs/STATUS.md`.

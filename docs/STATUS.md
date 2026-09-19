# Project Status

## 2026-09-19 — Authoritative Flip & Dip contract applied

Current version:

`flip-dip-v1-authoritative`

Current state:

`CALIBRATING`

The prior `flip-dip-v1-candidate` and its 2,000-bar validation are superseded.
They modeled first executions only and treated 1H as a normal primary entry.

## Implemented contract

- XAUUSD-only
- 5M and 15M primary entries
- optional 1H→4H entry mode
- strict flip-through / return-through chronology
- configurable candidate Flip Zone detector
- configurable rejection score, default 0.60
- required HTF CHOCH/BOS before retest
- distinct correct-side retest episodes
- up to 3 executions per zone
- execution-specific IDs and persistence
- candle-close invalidation on entry timeframe
- default 5% risk with hard 5% cap
- explicit mathematical 5R target
- partial TP owner configuration required; no invented default ladder
- Istanbul 23:00→20:00 trading window
- high-impact USD news filtering
- historical news filtering in schema-v3 calibration
- forward news fail-closed provider chain
- planning/demo only; no broker execution

## Calibration state

Schema v3 is now required.

A valid Phase 0 calibration must include:

- contract version `owner-flip-dip-2026-09-19`
- 5M and 15M primary timeframe calibration
- distinct retest execution model
- max execution cap 3
- historical news gate applied
- stabilized structural risk model
- at least 2,000 bars
- minimum independent-event data-quality threshold
- ambiguity rate within the configured ceiling

Until this is rerun successfully, dashboard readiness must show calibration required and the real worker must refuse normal startup.

## Remaining owner clarification

Exact partial TP levels and percentages are not provided by the strategy text.

Phase 0 therefore records milestones but does not claim exact strategy profit.
The historical account calculator is a labeled scenario only until the partial TP ladder is supplied.

## Next phase

1. Run authoritative schema-v3 calibration.
2. Review the new multi-execution bundle.
3. Reset old forward-demo runtime state.
4. Start a fresh forward-demo period.
5. Review interpretation accuracy before any owner approval.

## Safety/product boundary

No broker orders, automatic execution, or assisted execution endpoints exist.

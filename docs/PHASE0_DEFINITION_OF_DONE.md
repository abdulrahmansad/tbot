# Phase 0 Definition of Done

## Code-complete requirements

1. Authoritative owner strategy contract encoded.
2. XAUUSD 5M/15M/1H/4H candles normalized.
3. Primary entries default to 5M/15M.
4. 1H entry requires explicit opt-in.
5. Flip-through then return-through chronology enforced.
6. Healthy-rejection gate enforced with configurable candidate threshold.
7. Required HTF CHOCH/BOS must be observed before retest.
8. Distinct retest episodes are counted objectively.
9. Maximum three executions per zone is enforced end-to-end.
10. Every execution has a unique identity in calibration and forward demo.
11. Candle-close invalidation is entry-timeframe specific.
12. Intended risk defaults to 5% and cannot exceed 5%.
13. Mathematical minimum 5R target is explicit in each READY plan.
14. Partial TP configuration is explicit; no invented owner ladder.
15. Istanbul 23:00→20:00 trading window is enforced.
16. High-impact news gate is enforced at retest time.
17. Historical calibration applies the news gate.
18. Historical calibration uses schema v3.
19. Old schema/calibration cannot start a real forward demo.
20. Historical and forward outcomes track milestones and terminal state separately.
21. Forward plan persistence allows e1/e2/e3 and prevents duplicates.
22. Worker snapshot/heartbeat and dashboard are read-only.
23. Market/news provider keys remain worker-only.
24. No broker execution code/endpoints exist.
25. CI is green.

## Historical validation requirements before forward demo

- schema_version = 3
- strategy_contract_version = owner-flip-dip-2026-09-19
- primary timeframes 5M and 15M are both present
- optional 1H is only included when explicitly requested
- execution model = distinct retest episodes with correct-side rearm
- max executions per zone = 3
- historical news filter applied
- stabilized structural risk model used
- at least 2,000 bars requested
- at least 150 independent primary events across primary timeframes
- ambiguous-event rate <= 5%
- no performance threshold is used as a readiness shortcut

The old schema-v2 validation does **not** satisfy these requirements.

## Forward-demo requirements before owner approval

- current schema-v3 calibration passes readiness
- old runtime state is reset
- worker runs continuously
- worker heartbeat remains healthy
- news protection is connected
- e1/e2/e3 plans are recorded once each
- outcomes are tracked to terminal state
- one-week forward-demo behavior is reviewed
- owner supplies/confirms partial TP ladder

## Public-launch requirements

Before external/public users are served:

- confirm external-display/commercial market-data licensing
- preserve planning/demo-only and execution-disabled boundary
- deploy shared persistent storage
- configure access controls appropriately

Phase 0 completion does not mean profitable, live-trading safe, or owner-approved.

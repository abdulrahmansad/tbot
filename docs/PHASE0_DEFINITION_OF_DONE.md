# Phase 0 Definition of Done

## Code-complete requirements

1. Strategy contract is encoded.
2. XAUUSD 5M/15M/1H/4H data can be normalized.
3. Automated Flip Zone detection exists.
4. Rejection scoring exists.
5. Higher-timeframe structure detection exists.
6. Strict event ordering and no-lookahead timing are enforced.
7. Retest detection exists.
8. Trading-window rules are enforced.
9. News blackout logic and a real calendar adapter exist.
10. Candle-close invalidation exists.
11. Minimum 5R logic exists.
12. Configurable partial TP logic exists.
13. Stabilized planning-risk normalization exists.
14. Max three executions per zone is implemented.
15. Historical scan/export works.
16. Independent-event clustering works.
17. Historical outcome tracking works.
18. Milestones and terminal outcomes are distinct.
19. Calibration analysis/readiness reporting works.
20. Forward-demo discovery and persistence work.
21. Forward-demo outcome tracking works.
22. Live worker snapshot and heartbeat work.
23. Dashboard/API read shared worker state.
24. Web traffic does not multiply market-data API calls.
25. Private hosted access can be protected.
26. CI tests pass.
27. No broker execution code exists.

## Historical validation requirements

Before forward demo:

- strict-sequence calibration completed,
- stabilized structural risk model used,
- at least 2,000 bars requested,
- at least 150 independent primary events available,
- ambiguous primary outcomes remain within the calibration-quality ceiling,
- no performance threshold is used as a readiness shortcut.

The current v1 candidate satisfies these historical data-quality gates.

## Forward-demo requirements

Before owner approval:

- TWELVE_DATA_API_KEY configured for the worker,
- live news protection available through FMP or the built-in FinanceCalendar fallback,
- forward worker runs continuously,
- worker heartbeat remains healthy,
- fresh plans are recorded once,
- outcomes are tracked to terminal state,
- one-week forward-demo results are reviewed,
- partial TP policy is confirmed or revised by the owner.

## Public-launch requirements

Before external/public users are served:

- confirm an appropriate external-display/commercial market-data license,
- configure private/public access appropriately,
- preserve the planning/demo and execution-disabled product boundary,
- deploy shared persistent storage for worker/web state.

Phase 0 code completeness does not mean the strategy is profitable or
owner-approved.

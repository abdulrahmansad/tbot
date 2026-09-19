# Phase 0 Definition of Done

Phase 0 is complete when all of the following are true:

1. Strategy contract is encoded.
2. XAUUSD 5M/15M/1H/4H data can be normalized.
3. Provisional automated Flip Zone detection exists.
4. Provisional rejection scoring exists.
5. Provisional higher-timeframe structure detection exists.
6. Retest detection exists.
7. Trading-window rules are enforced.
8. News blackout logic exists.
9. Candle-close invalidation exists.
10. Minimum 5R logic exists.
11. Configurable partial TP logic exists.
12. Risk planning is implemented.
13. Max three executions per zone is implemented.
14. Historical scan/export works.
15. Demo tracking/reporting works.
16. Live polling service exists.
17. CI tests pass.
18. No broker execution code exists.

External inputs still required before the demo week:
- market-data API key
- historical calibration run
- review/tuning of provisional detector
- economic calendar provider/API if news filtering is to be live
- final owner-defined TP percentages/levels if different from provisional defaults

Phase 0 being code-complete does not mean the strategy is trader-validated or profitable.

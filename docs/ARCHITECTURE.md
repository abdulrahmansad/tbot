# Phase 0 Architecture

## Objective

Create a deterministic XAUUSD Flip & Dip planner that can later consume live candles, produce trade plans, and forward-test those plans without broker execution.

## Layers

1. **Market data adapter**
   - normalized OHLC candles
   - 5M / 15M / 1H / 4H
   - provider intentionally not locked yet

2. **Strategy detectors**
   - Flip Zone detector
   - rejection evaluator
   - CHoCH/BOS detector
   - owner-calibrated; no silent default rules

3. **State machine**
   - tracks lifecycle of each zone
   - enforces max 3 executions

4. **Plan gate**
   - correct HTF confirmation
   - healthy rejection
   - >= 5R
   - Istanbul trading window
   - news blackout

5. **Trade-plan output**
   - direction
   - zone
   - entry timeframe
   - confirmation timeframe
   - invalidation rule
   - intended risk
   - execution number
   - reasons when no plan is produced

6. **Demo tracker** (next implementation step)
   - timestamp every READY plan
   - follow hypothetical result
   - store completion/invalidation/expiry
   - never send broker orders

## Safety boundary

No broker execution module is part of Phase 0.

A future application may consume plans, but the strategy engine itself remains a planning and evaluation system unless the product contract is explicitly changed.

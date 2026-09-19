# XAUUSD Flip & Dip — Authoritative Phase 0 Strategy Contract

Contract version: `owner-flip-dip-2026-09-19`

This file is the Phase 0 source of truth. The software automates planning,
historical calibration, and forward-demo tracking only. It must never place a
broker order.

## 1. Scope and timeframes

Symbol: XAUUSD only.

Analysis timeframes:

- 4H
- 1H
- 15M
- 5M

Primary entry timeframes:

- 5M
- 15M

Optional entry timeframe:

- 1H, only when explicitly enabled.

Required confirmation mapping:

- 5M entry -> 15M CHoCH/BOS
- 15M entry -> 1H CHoCH/BOS
- 1H entry -> 4H CHoCH/BOS

## 2. Forbidden concepts

The strategy must not add:

- liquidity sweeps
- equal highs/lows
- previous day high/low
- previous session high/low
- liquidity pools
- RSI
- MACD
- moving averages
- Fibonacci
- volume indicators
- unrelated SMC rules

## 3. Core Flip & Dip sequence

SELL:

1. A valid Flip Zone exists.
2. Price trades/spikes above the zone. A candle may close above it.
3. Price subsequently returns below the zone.
4. Healthy rejection is confirmed.
5. Required higher-timeframe bearish CHoCH/BOS is observed.
6. Price later retests the zone from below.
7. A SELL plan may become READY.

BUY is the exact inverse.

The initial flip/spike is not an execution.

## 4. Retests and executions

A zone may produce up to three executions.

Each execution is a distinct correct-side retest episode:

- execution #1
- execution #2
- execution #3

Consecutive candles occupying the same zone are one retest episode. After a
recorded execution, price must leave the zone back on the correct side before
another retest is counted. This software-counting rule is configurable and
exists only to distinguish separate retest episodes objectively.

No fourth execution is allowed.

## 5. Rejection quality

Weak, messy, indecisive rejection must be skipped.

The exact numerical rejection definition is not specified by the owner text,
so Phase 0 uses a configurable candidate score. The current candidate default
is 0.60 and must not be treated as immutable owner doctrine.

## 6. CHoCH / BOS

Each execution requires the correct higher-timeframe directional structure
confirmation.

The confirmation:

- must be on the required HTF,
- must match BUY/SELL direction,
- must be CHOCH or BOS,
- must be observed before the retest.

The exact swing interpretation/classification remains configurable because the
owner text does not provide a complete mathematical CHoCH/BOS algorithm.
Current automated detection uses a pivot-break BOS candidate model.

## 7. Entry

A plan may become READY only after the full sequence:

FLIP ZONE
-> FLIP THROUGH
-> RETURN THROUGH
-> HEALTHY REJECTION
-> REQUIRED HTF CHOCH/BOS
-> LATER CORRECT-SIDE RETEST

Being near a zone is not enough.

## 8. Invalidation

SELL:

- entry-timeframe candle CLOSE above the zone invalidates the trade.

BUY:

- entry-timeframe candle CLOSE below the zone invalidates the trade.

A wick alone does not invalidate.

The invalidation timeframe is always the entry timeframe.

## 9. Risk

Default intended risk is exactly 5% of current account equity per execution.

Configuration may reduce risk but must never exceed the owner's 5% cap.

Each execution is a separate trade/risk event.

Because invalidation is based on a future candle close, exact realized loss
cannot be guaranteed to equal 5%. Phase 0 uses a separate sizing reference for
planning and must never misrepresent that reference as the actual invalidation
price.

## 10. Minimum reward

Minimum planned reward is 5R.

The plan must be able to compute a mathematical 5R target from:

- entry reference
- planning risk distance

No setup may be READY with planned RR below 5.

## 11. Partial take profit

Partial exits are required by the owner strategy.

Exact TP levels and percentages were not specified. Therefore Phase 0 must not
invent a final ladder.

`FlipDipConfig.partial_tp_levels` remains explicitly unconfigured until the
owner supplies percentages/levels.

Historical milestone scenarios may use 2R/3.5R/5R for analysis but must be
labeled hypothetical and not exact strategy P&L.

## 12. Trading hours

Timezone: Europe/Istanbul.

New entries are allowed:

- start 23:00
- end 20:00 the following day

20:00 <= local time < 23:00 is blocked.

The cross-midnight window is valid and intentional.

## 13. High-impact news

New entries must be blocked around high-impact USD/XAUUSD-relevant events.

Examples include:

- CPI
- NFP
- FOMC
- Federal Reserve rate decisions
- Powell/Fed speeches
- major US economic releases

Exact blackout minutes are configurable. Candidate defaults:

- 30 minutes before
- 15 minutes after

Historical validation must apply the news gate. Forward demo must fail closed
if all calendar providers fail.

## 14. Multiple trades

Multiple trades per day are allowed.

Every execution independently must satisfy:

- valid Flip & Dip sequence
- healthy rejection
- required HTF CHoCH/BOS
- valid correct-side retest
- minimum 5R
- risk cap
- trading hours
- news filter

## 15. Ambiguous rules

The following are configurable candidate definitions rather than silently
invented owner rules:

- exact Flip Zone construction
- rejection threshold/scoring
- exact CHoCH/BOS swing algorithm
- retest episode counting/rearm behavior
- partial TP percentages and levels
- news blackout minutes
- risk percentage up to the 5% cap
- trading hours
- optional 1H entry mode

Any future change to these must remain explicit and documented.

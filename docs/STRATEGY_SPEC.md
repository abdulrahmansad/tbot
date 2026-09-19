# XAUUSD Flip & Dip — Strategy Contract

## Purpose

This file is the Phase 0 source of truth. The software must automate **planning and demo tracking only**. It must never place a broker order.

## Scope

- Symbol: XAUUSD
- Analysis timeframes: 4H, 1H, 15M, 5M
- Primary entry timeframes: 15M, 5M
- 1H entry logic is retained because the owner explicitly supplied 1H → 4H confirmation rules.

### Confirmation mapping

| Entry TF | Required structure TF |
|---|---|
| 5M | 15M |
| 15M | 1H |
| 1H | 4H |

## Core sequence

FLIP ZONE
→ price flips through zone
→ price returns through zone
→ healthy rejection
→ required higher-timeframe CHoCH/BOS
→ retest
→ plan ready
→ candle-close invalidation
→ minimum 5R
→ partial take profits

## SELL

1. Valid Flip Zone exists.
2. Price trades above the zone. A candle may close above it.
3. Price subsequently returns below the zone.
4. Rejection must qualify as healthy.
5. Required higher timeframe confirms bearish CHoCH/BOS.
6. Price later retests the zone from below.
7. A SELL plan may become READY.

## BUY

Exact inverse of SELL.

## Retests / executions

- Initial flip is not an execution.
- Maximum 3 executions/plans per zone.
- Each execution is tracked independently.
- After execution #3, the zone is exhausted for new plans.

## Invalidation

SELL: entry-timeframe candle must CLOSE above the zone.
BUY: entry-timeframe candle must CLOSE below the zone.
A wick alone does not invalidate.

## Risk

Configured risk = 5% per execution.

Important implementation note: candle-close invalidation means the future invalidation fill price is unknown. The planner can display intended risk, but no system can guarantee a hard 5% realized loss without a separate emergency price/order rule. Phase 0 must not misrepresent this.

## Reward

- Minimum planned reward: 5R.
- Less than 5R → no plan.
- Partial take profits supported.
- Exact TP levels and percentages remain configurable until owner-defined.

## Trading hours

Timezone: Europe/Istanbul.
New plans allowed from 23:00 through 20:00 the following day.
20:00–23:00 is blocked.

## News

New plans are blocked around high-impact XAUUSD-relevant events. Blackout durations are configurable.

## Explicitly forbidden additions

Do not introduce:
- liquidity sweeps
- equal highs/lows
- previous day/session high/low logic
- liquidity pools
- RSI
- MACD
- moving averages
- Fibonacci
- volume indicators
- unrelated SMC rules

## Rules intentionally unvalidated

These must NOT be guessed:
1. exact Flip Zone detection
2. healthy rejection threshold/definition
3. exact swing-point algorithm for CHoCH/BOS
4. exact TP ladder and percentages

Until owner-approved examples are available, implementations for these rules must either be configurable, return an unvalidated status, or raise an explicit error.

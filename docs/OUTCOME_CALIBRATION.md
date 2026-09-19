# Historical Outcome Calibration

Status: provisional calibration logic, not owner-approved trading P&L.

## Purpose

The outcome simulator answers a narrow question:

After a setup becomes PLAN_READY, what did price do next under the written
Flip & Dip invalidation rule?

It does not place orders and it does not claim broker-realized returns.

## Calibration entry reference

The plan is an entry area, not a fixed market order.

For historical calibration only:

- SELL uses the zone lower boundary as the reference entry.
- BUY uses the zone upper boundary as the reference entry.

This represents the near-side edge first approached on a correct-side retest.

## Calibration R unit

One R is normalized to the Flip Zone width:

zone_width = zone_upper - zone_lower

This is a comparison metric so setups of different price scales can be
compared. It is not the final position-sizing model.

Targets are therefore reported at 2R, 3.5R and 5R relative to this provisional
reference.

## Strategy invalidation

Invalidation does not use a fixed-R stop.

The owner's rule remains:

- SELL: entry-timeframe candle CLOSE above the zone.
- BUY: entry-timeframe candle CLOSE below the zone.
- A wick alone does not invalidate.

Because close-based invalidation and zone-width R are different concepts,
realized loss cannot be assumed to equal exactly -1R.

## Intrabar ambiguity

OHLC candles do not reveal event order inside a candle.

If the same candle both:

1. reaches a previously unachieved target, and
2. closes through strategy invalidation,

the simulator returns AMBIGUOUS.

It must not guess whether target or invalidation happened first.

## Event clustering

Multiple historical Flip Zones can become ready during the same directional
market event.

The calibration layer groups READY setups when they share:

- entry timeframe,
- direction, and
- retest timing within one entry-timeframe bar.

All zones remain visible.

Within each cluster the provisional primary zone is ranked by:

1. highest rejection score,
2. narrower zone,
3. earlier zone creation time.

The primary label is for reporting and calibration only. It does not silently
delete secondary zones or change the owner's rule allowing multiple zones.

## Outcome statuses

- OPEN: no terminal outcome within available candles.
- INVALIDATED: close invalidation before reaching 2R.
- TARGET_2R: reached at least 2R before later invalidation/end of data.
- TARGET_3_5R: reached at least 3.5R before later invalidation/end of data.
- TARGET_5R: reached 5R.
- AMBIGUOUS: OHLC ordering cannot determine target-vs-invalidation sequence.

## Before V1 freeze

Do not label this profitability-grade until:

- calibration outputs have been reviewed,
- event clustering is inspected,
- unresolved/ambiguous cases are understood,
- the provisional entry/R assumptions are either owner-approved or replaced,
- forward demo testing is completed.

# LEGACY / SUPERSEDED VALIDATION

This report is retained for audit history only.

It is **not valid for the current authoritative strategy contract** because it:
- modeled only the first execution/retest per zone,
- treated 1H as a normal primary entry timeframe,
- predates schema-v3 historical news filtering and execution-specific identities.

Do not use this report to declare the current strategy forward-demo ready.

---

# Flip & Dip V1 Candidate — 2,000-Bar Validation

Date: 2026-09-19

Status: historical calibration quality accepted for forward-demo testing.

This document does not claim profitability, live-trading fitness, or owner
approval.

## Calibration configuration

- Sample label: validation-2000
- Requested bars per entry/confirmation timeframe: 2,000
- Risk model: structural_rejection_plus_median20_range_floor
- Entry reference: near-side Flip Zone edge
- Strategy invalidation: entry-timeframe candle close beyond the Flip Zone
- Broker execution: disabled

## Primary independent events

The validation set produced 215 independent primary events:

- 5M -> 15M: 67
- 15M -> 1H: 73
- 1H -> 4H: 75

Two primary events were ambiguous, below the 5% calibration-data ambiguity
ceiling used by the readiness gate.

## Primary outcomes

Across the 215 primary events:

- TARGET_5R: 46
- TARGET_3_5R: 13
- TARGET_2R: 23
- INVALIDATED: 131
- AMBIGUOUS: 2

These counts are diagnostic historical outcomes under the calibration model,
not broker-realized P&L.

## Timeframe observations

5M -> 15M:

- 67 primary events
- 10 TARGET_5R
- 4 TARGET_3_5R
- 5 TARGET_2R
- 48 INVALIDATED

15M -> 1H:

- 73 primary events
- 18 TARGET_5R
- 6 TARGET_3_5R
- 8 TARGET_2R
- 40 INVALIDATED
- 1 AMBIGUOUS

1H -> 4H:

- 75 primary events
- 18 TARGET_5R
- 3 TARGET_3_5R
- 10 TARGET_2R
- 43 INVALIDATED
- 1 AMBIGUOUS

## Direction observations

No direction/timeframe combination is promoted to a permanent hard filter from
this sample.

The previous 1,000-bar sample showed weak 1H BUY behavior. The expanded
2,000-bar validation showed that weakness was not stable across the full
historical window: the older half of 1H BUY produced 5R outcomes while the
newer half did not.

This is treated as regime sensitivity rather than evidence to disable 1H BUY.

## Rejection score

The data does not support raising the rejection-score threshold as a universal
hard filter. Strong and weak outcomes overlap materially across rejection
scores.

The current rejection threshold is retained for the v1 candidate.

## Multi-zone clustering

The existing primary-zone ranking remains:

1. highest rejection score
2. narrower zone
3. earlier zone creation time

Across 86 multi-zone clusters in this validation set, only four clusters
contained a secondary zone reaching 5R while the chosen primary did not.

This is considered adequate for the forward-demo candidate. No new
cluster-ranking optimization is introduced.

## Risk normalization

The stabilized risk model removed the previous unrealistic 100R-300R
normalization artifacts.

The calibration risk distance is:

max(
    rejection structural distance,
    recent 20-candle median full range,
    Flip Zone width
)

This is a planning/sizing safeguard only. It does not detect setups or replace
the candle-close invalidation rule.

## V1 candidate decision

The historical evidence supports freezing the current detector as:

flip-dip-v1-candidate

State:

REVIEW_REQUIRED

The candidate keeps:

- 5M, 15M, and 1H entry timeframes
- BUY and SELL directions
- existing rejection threshold
- existing primary-cluster ranking
- strict event chronology
- stabilized structural risk model
- minimum 5R plan requirement
- candle-close invalidation
- maximum three executions per zone
- planning/demo-only boundary

## Next proof stage

The next validation stage is forward demo.

Historical calibration quality is sufficient to begin forward-demo tracking,
but the strategy must not be marked OWNER_APPROVED until forward behavior is
reviewed.

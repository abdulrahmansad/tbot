# Phase 0 Strategy Audit

Date: 2026-09-19

Contract: `owner-flip-dip-2026-09-19`

## Result

The repository has been reconciled to the owner's written Flip & Dip strategy.

The previous first-execution-only validation is superseded. A new schema-v3
calibration is required before the real forward demo can restart.

## Rule-by-rule audit

| Owner rule | Phase 0 implementation |
|---|---|
| XAUUSD only | Enforced |
| 4H/1H/15M/5M analysis | Supported |
| 5M primary entry | Enforced/default |
| 15M primary entry | Enforced/default |
| 1H entry | Optional explicit opt-in only |
| 5M -> 15M structure | Enforced |
| 15M -> 1H structure | Enforced |
| optional 1H -> 4H structure | Enforced |
| No liquidity rules | No liquidity entry logic present |
| Flip through zone | Enforced by detector |
| Return through zone | Enforced by detector |
| Healthy rejection | Enforced with configurable candidate threshold |
| HTF CHOCH/BOS before retest | Enforced |
| Later correct-side retest | Enforced |
| Initial flip is not entry | Enforced |
| Max 3 executions/retests per zone | Enforced |
| Distinct retest counting | Correct-side rearm episode model |
| Candle-close invalidation | Enforced on entry timeframe |
| Wick alone does not invalidate | Enforced |
| 5% intended risk | Default exact 5%; hard cap prevents >5% |
| Separate risk per execution | Execution-specific plans |
| Minimum 5R | Enforced; explicit 5R price computed |
| Partial exits | Supported/configurable; no invented final ladder |
| Istanbul 23:00 -> 20:00 | Enforced |
| High-impact news filter | Enforced at retest time |
| Multiple trades/day | Allowed |
| No RSI/MACD/MA/Fib/volume | Not used |
| No broker execution | No execution client/endpoints |

## Candidate definitions that remain configurable

These are not fully mathematically defined by the owner text and therefore
remain explicit candidate parameters:

1. Flip Zone construction.
2. Rejection score formula and minimum threshold.
3. CHOCH/BOS swing interpretation/classification.
4. Distinct-retest rearm definition.
5. News blackout minutes.
6. Optional 1H entry enablement.
7. Partial TP levels/percentages.

No additional trading concepts may be added to solve these ambiguities.

## Partial TP status

The owner requires partial exits but has not supplied exact levels/percentages.

Therefore:

- no default owner TP ladder exists,
- READY plans are marked `partial_tp_configured=false`,
- historical 2R/3.5R/5R account calculations are labeled milestone scenarios,
- exact strategy P&L is unavailable until the owner defines the partial ladder.

## Calibration reset

Old schema-v2 calibration is rejected by the current readiness gate.

Schema-v3 validation requires:

- primary 5M/15M calibration,
- up to three distinct retest executions,
- execution-specific setup identities,
- historical news filtering,
- current risk model,
- current contract version.

## Runtime reset

Before the next real forward demo:

1. complete schema-v3 calibration,
2. review the new bundle,
3. run `scripts/reset_phase0_runtime.py --confirm`,
4. restart worker/server,
5. run preflight and local smoke tests.

The worker refuses normal startup if current calibration does not satisfy the
authoritative contract.

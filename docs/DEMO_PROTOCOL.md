# Demo / Forward-Test Protocol

## Goal

The first demo period validates whether the software interprets the owner's strategy correctly. Profitability alone is not proof of correctness.

## Bot behavior

The bot:
- watches XAUUSD data
- identifies eligible strategy states
- creates hypothetical trade plans
- records what would have happened
- never sends an order

## Minimum review fields per plan

- plan id
- timestamp
- direction
- Flip & Dip zone
- entry timeframe
- required confirmation timeframe
- rejection result
- CHoCH/BOS result
- execution number (1/2/3)
- planned R:R
- news gate
- trading-hours gate
- invalidation outcome
- partial/completed TP events
- final R result when available
- chart evidence link/snapshot when UI is added

## One-week owner review

After the first live demo week, review:
1. Did the bot identify zones the owner considers valid?
2. Did it reject zones the owner considers invalid?
3. Did it classify rejection correctly?
4. Did its CHoCH/BOS confirmation match the owner's reading?
5. Did it wait for the required retest?
6. Did it honor max 3 executions?
7. Did it avoid blocked hours/news?
8. Did it incorrectly create any plan?

Only after interpretation accuracy is acceptable should profitability metrics be treated as meaningful.

## Approval state

A demo strategy version should have one of:
- DRAFT
- CALIBRATING
- DEMO_ACTIVE
- REVIEW_REQUIRED
- OWNER_APPROVED
- REJECTED

OWNER_APPROVED means the planner behavior matches the intended strategy. It does not guarantee profitability.

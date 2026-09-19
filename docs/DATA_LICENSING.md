# Market Data Licensing Boundary

TBOT is currently prepared for private/internal forward-demo validation.

## Twelve Data development use

The current Twelve Data Basic/free offering is suitable for development and
internal/non-display testing within its API credit limits.

TBOT's worker cache is designed to keep normal XAUUSD live polling within the
free daily request budget by sharing timeframe data across scans.

## Public/external display

Do not expose Twelve Data-derived market data or plan values to public/external
users under an internal/non-display license.

Before public launch, the project owner must verify that the selected market
data plan/provider explicitly permits the intended external display and
commercial usage.

This is a product/licensing requirement, not a strategy rule.

## Current deployment rule

Until an appropriate external-display license is confirmed:

- run the dashboard as a private demo,
- enable TBOT_DASHBOARD_USERNAME / TBOT_DASHBOARD_PASSWORD,
- do not market the URL as a public market-data product,
- do not remove the planning/demo-only and execution-disabled notices.

## Provider separation

Only the worker receives market-data/news API keys.

The web service receives derived state through shared persistent storage and
does not call Twelve Data directly.

This architecture remains valid if the market-data provider or licensing tier
changes later.

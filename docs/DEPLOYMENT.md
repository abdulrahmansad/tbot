# Phase 0 Deployment

TBOT Phase 0 runs as two processes.

## 1. Web service

Command:

python scripts/run_server.py

Responsibilities:

- serve the user dashboard
- expose read-only API endpoints
- show calibration and forward-demo results
- read worker-produced live snapshots
- never place broker orders
- never call Twelve Data in production

Default local URL:

http://localhost:8000

## 2. Forward-demo worker

Command:

python scripts/run_forward_demo.py --interval 60

Responsibilities:

- poll XAUUSD market data
- detect fresh primary Flip & Dip plans
- prevent duplicate plan creation across polls
- apply the news blackout when an economic-calendar provider is configured
- persist hypothetical plans
- update hypothetical outcomes
- write the shared live snapshot consumed by the web service

There is no broker client and no order-placement code.

## Environment variables

The worker requires:

TWELVE_DATA_API_KEY

Optional primary economic-calendar provider:

FMP_API_KEY

If FMP is unavailable or plan-gated, TBOT automatically falls back to the
free FinanceCalendar API for high-impact US/Fed event protection.

The web service does not need either provider API key.

For a hosted private dashboard, configure:

TBOT_DASHBOARD_USERNAME
TBOT_DASHBOARD_PASSWORD

Provider secrets must be configured in the worker environment only. Dashboard
access credentials must be configured in the web environment only. Do not put
them in source code, frontend JavaScript, Docker images, Git, or the web
service environment.

## Preflight

Before starting the real demo:

python scripts/preflight_demo.py

For a hosted private demo:

python scripts/preflight_demo.py --hosted

The hosted check requires market data, news protection, historical calibration
readiness, and private dashboard credentials. By default preflight performs a
real provider smoke test: one small Twelve Data candle request and one calendar
request through the fallback chain. Use --skip-network only for offline config
inspection.

## Local Compose

With a local .env file configured:

docker compose up --build

This starts:

- web on port 8000
- worker polling every 60 seconds
- one shared runtime volume for live snapshot, demo records, and results

The .env file is excluded from the Docker build context and is supplied only
to the worker service.

## Hosting shape

Deploy one web process and one worker process with shared persistent storage.

Web:

python scripts/run_server.py

Worker:

python scripts/run_forward_demo.py --interval 60

Only the worker needs TWELVE_DATA_API_KEY.

The worker may receive FMP_API_KEY as the primary economic-calendar provider.
If FMP fails (including plan-gated HTTP 402 responses), the worker automatically
uses FinanceCalendar as its fallback.

The web service reads:

- data/runtime/live-snapshot.json
- data/runtime/forward-plans.jsonl
- data/runtime/forward-results.json
- calibration files when present

from shared persistent storage.

## Live data fan-out

Production live-data flow:

worker -> Twelve Data / economic calendar -> shared runtime snapshot -> web -> users

The web process does not call Twelve Data in production. One worker poll feeds
all dashboard visitors through the shared snapshot, so user traffic does not
multiply market-data API usage.

## Read-only dashboard endpoints

- GET /
- GET /api/health
- GET /api/calibration/status
- GET /api/live
- GET /api/plans
- GET /api/performance
- GET /api/history

There are intentionally no endpoints for:

- order placement
- broker execution
- buy/sell submission
- assisted execution

## Before public Phase 0

Do not expose the app as an owner-approved strategy until:

1. historical calibration quality is accepted,
2. a named candidate version is frozen,
3. the forward-demo period has been observed and reviewed,
4. runtime storage and worker secrets are configured on the chosen host.

The current historical state is flip-dip-v1-candidate and remains
REVIEW_REQUIRED until forward-demo evidence is reviewed.


## Provider request budgets

The worker uses a timeframe-aware market cache. Under continuous one-minute
worker cycles, upstream Twelve Data refreshes occur approximately once per
actual timeframe bucket rather than once per scan:

- 5M: about 288 requests/day
- 15M: about 96 requests/day
- 1H: about 24 requests/day
- 4H: about 6 requests/day

Total normal market-data refreshes are about 414/day before retries or unusual
operations.

Economic-calendar responses are cached for 10 minutes. FMP is tried first when
configured; FinanceCalendar is used automatically if FMP is unavailable or
plan-gated.

These are engineering estimates, not provider guarantees. Provider limits and
licenses must be checked before production/public launch.

## Private-demo access

When TBOT_DASHBOARD_USERNAME and TBOT_DASHBOARD_PASSWORD are configured, the
hosted FastAPI app protects dashboard/API routes with HTTP Basic authentication.
The minimal /api/health endpoint remains unauthenticated for uptime checks.

Do not use private-demo authentication as a substitute for an appropriate
external-display market-data license.


## Calendar fallback behavior

News protection must not fail open just because the preferred provider is unavailable.
The worker tries providers in this order:

1. XOOMAR free US macro calendar.
2. FinanceCalendar free API.
3. FMP only when FMP_API_KEY is configured.

This order avoids repeatedly hitting a known plan-gated FMP endpoint when a
free US high-impact calendar is already available.

Only high-impact US/Federal Reserve events from the fallback feed are converted
into USD/XAUUSD blackout events. The live snapshot and health API expose the
provider that actually supplied the current calendar data.

FinanceCalendar requires visible attribution when its data is displayed; the
dashboard shows a source link when that fallback is active.

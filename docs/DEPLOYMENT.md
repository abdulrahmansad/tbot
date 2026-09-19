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

Optional but recommended before the forward-demo week:

FMP_API_KEY

The web service does not need either API key.

Secrets must be configured in the worker hosting environment only. Do not put
them in source code, frontend JavaScript, Docker images, Git, or the web
service environment.

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

The worker should also receive FMP_API_KEY once the economic-calendar feed is
enabled.

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

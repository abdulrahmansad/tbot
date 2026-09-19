# Phase 0 Deployment

TBOT Phase 0 runs as two processes.

## 1. Web service

Command:

python scripts/run_server.py

Responsibilities:

- serve the user dashboard
- expose read-only API endpoints
- show calibration and forward-demo results
- never place broker orders

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

There is no broker client and no order-placement code.

## Environment variables

Required for real XAUUSD market data:

TWELVE_DATA_API_KEY

Optional but recommended before the forward-demo week:

FMP_API_KEY

Secrets must be configured in the hosting provider environment. Do not put
them in source code, frontend JavaScript, Docker images, or Git.

## Local Compose

With a local .env file configured:

docker compose up --build

This starts:

- web on port 8000
- worker polling every 60 seconds
- one shared runtime volume for demo records/results

The .env file is excluded from the Docker build context.

## Hosting shape

Deploy one web process and one worker process with shared persistent storage.

Web:

python scripts/run_server.py

Worker:

python scripts/run_forward_demo.py --interval 60

Both need TWELVE_DATA_API_KEY.

The worker should also receive FMP_API_KEY once the economic-calendar feed is
enabled.

## Read-only dashboard endpoints

- GET /
- GET /api/health
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

Do not expose the app as a validated strategy until:

1. the enhanced historical calibration has been rerun,
2. detector parameters have been reviewed,
3. a named calibrated version is frozen,
4. forward-demo results have been observed,
5. runtime storage and secrets are configured on the chosen host.

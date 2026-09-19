# tbot — XAUUSD Flip & Dip Planner

TBOT is a planning and forward-demo system for the owner's XAUUSD Flip & Dip strategy.

**It never places broker orders.**

Current strategy version: `flip-dip-v1-candidate`

State: `REVIEW_REQUIRED`

## Current capabilities

- XAUUSD-only scope
- 5M / 15M / 1H entry timeframes
- 15M / 1H / 4H confirmation mapping
- strict no-lookahead event chronology
- deterministic Flip Zones
- rejection scoring and HTF BOS confirmation
- correct-side retest detection
- event clustering / primary-zone ranking
- Istanbul trading window
- high-impact USD news blackout
- stabilized structural risk normalization
- 2R / 3.5R / 5R milestone tracking
- candle-close invalidation
- separate milestone vs terminal outcome state
- 2,000-bar historical validation support
- forward-demo discovery / deduplication / outcome tracking
- worker-generated live snapshot and heartbeat monitoring
- read-only FastAPI dashboard
- Live / Plans / Performance / History UI
- worker-only market/news API secrets
- timeframe-aware Twelve Data caching
- economic-calendar caching
- optional private dashboard HTTP Basic protection
- Docker / Compose deployment
- CI regression tests

## Strategy boundary

The strategy deliberately excludes liquidity sweeps, equal highs/lows, previous day/session highs/lows, liquidity pools, RSI, MACD, moving averages, Fibonacci, volume indicators, and unrelated SMC rules.

The current detector is frozen as a historical-validation candidate for forward demo. It is not claimed to be profitable or owner-approved.

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Calibration

```bash
python scripts/run_full_calibration.py
python scripts/run_full_calibration.py --bars 2000 --label validation-2000
python scripts/analyze_calibration.py
```

## Forward-demo prerequisites

Copy `.env.example` to `.env`.

Required for the real forward-demo period:

- `TWELVE_DATA_API_KEY`
- `FMP_API_KEY` is optional; TBOT falls back to FinanceCalendar if FMP is unavailable.

For a hosted private dashboard also set:

- `TBOT_DASHBOARD_USERNAME`
- `TBOT_DASHBOARD_PASSWORD`

Check readiness:

```bash
python scripts/preflight_demo.py --hosted
```

## Run locally with Docker Compose

```bash
docker compose up --build
```

The worker owns market/news provider access. The web service reads the shared runtime snapshot and does not call Twelve Data directly.

## Important data-license boundary

The current deployment should be treated as private/internal forward-demo validation until the selected market-data license explicitly permits the intended public/external display use.

See `docs/DATA_LICENSING.md`.

## Documentation

- `docs/STRATEGY_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTCOME_CALIBRATION.md`
- `docs/V1_VALIDATION_2000.md`
- `docs/DEPLOYMENT.md`
- `docs/DATA_LICENSING.md`
- `docs/PHASE0_DEFINITION_OF_DONE.md`
- `docs/STATUS.md`

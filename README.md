# tbot — XAUUSD Flip & Dip Planner

TBOT is a planning, calibration, and forward-demo system for the owner's XAUUSD Flip & Dip strategy.

**It never places broker orders.**

Current strategy version: `flip-dip-v1-authoritative`

Current state: `CALIBRATING` until schema-v3 historical validation passes.

## Authoritative Phase 0 contract

- XAUUSD only
- primary entries: 5M and 15M
- optional 1H entry mode only when explicitly enabled
- confirmation mapping: 5M→15M, 15M→1H, optional 1H→4H
- Flip Zone → flip through → return through → healthy rejection → HTF CHOCH/BOS → later retest
- up to 3 distinct retest executions per zone
- entry-timeframe candle-close invalidation
- default 5% risk per execution, never above 5%
- minimum 5R mathematical target
- Istanbul 23:00→20:00 entry window
- high-impact USD news blackout
- no liquidity concepts or unrelated indicators
- partial exits required, but exact owner TP ladder is still unconfigured

See `docs/STRATEGY_SPEC.md`.

## Important validation state

The old 2,000-bar v2 calibration is **superseded** because it modeled first executions only and treated 1H as a normal primary entry.

Before restarting forward demo, run a new schema-v3 calibration:

```powershell
cd "$HOME\tbot"
git pull
.\.venv\Scripts\python.exe scripts\run_full_calibration.py --bars 2000 --label authoritative-v3
```

Optional 1H calibration:

```powershell
.\.venv\Scripts\python.exe scripts\run_full_calibration.py --bars 2000 --label authoritative-v3 --include-1h
```

Then check:

```powershell
.\.venv\Scripts\python.exe scripts\preflight_demo.py
```

A real forward-demo worker will refuse to start until the current calibration matches the authoritative schema-v3 contract.

## Clean restart after strategy changes

After a successful new calibration:

```powershell
.\.venv\Scripts\python.exe scripts\reset_phase0_runtime.py --confirm
.\.venv\Scripts\python.exe scripts\run_forward_demo.py --interval 60
```

## Dashboard

```powershell
.\.venv\Scripts\python.exe scripts\run_server.py
```

Open `http://localhost:8000`.

## Historical account simulator

Performance includes a hypothetical compounding scenario (for example, starting with $100 at 5% risk).

It is **not exact strategy P&L** until the owner defines the partial TP ladder and the new strategy-contract calibration is valid.

## Explicitly excluded

- broker execution
- liquidity sweeps
- equal highs/lows
- previous day/session high/low rules
- liquidity pools
- RSI
- MACD
- moving averages
- Fibonacci
- volume indicators
- unrelated SMC logic

## Key docs

- `docs/STRATEGY_SPEC.md`
- `docs/PHASE0_DEFINITION_OF_DONE.md`
- `docs/CALIBRATION_WORKFLOW.md`
- `docs/DEMO_PROTOCOL.md`
- `docs/STATUS.md`

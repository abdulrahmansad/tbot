# Authoritative Calibration Workflow

## Purpose

Calibration verifies whether the candidate detector interprets the owner's
Flip & Dip strategy consistently. It does not prove profitability.

## Required default timeframes

Primary entries:

- 5M -> 15M confirmation
- 15M -> 1H confirmation

Optional only when explicitly enabled:

- 1H -> 4H confirmation

## What schema v3 calibrates

For each detected Flip Zone:

1. confirmed pivot-derived candidate zone
2. price flips through zone
3. price returns through zone
4. full rejection window completes
5. rejection score is evaluated
6. required HTF BOS/CHOCH candidate is observed
7. later correct-side retest episode #1
8. correct-side rearm
9. later retest episode #2
10. correct-side rearm
11. later retest episode #3
12. each execution independently applies:
   - rejection gate
   - HTF structure gate
   - trading hours
   - historical high-impact-news gate
   - minimum 5R plan
   - 5% risk metadata
13. each execution is replayed on future candles
14. all records are exported with execution-specific setup keys

## Command

Windows:

```powershell
cd "$HOME\tbot"
.\.venv\Scripts\python.exe scripts\run_full_calibration.py --bars 2000 --label authoritative-v3
```

Optional 1H entry study:

```powershell
.\.venv\Scripts\python.exe scripts\run_full_calibration.py --bars 2000 --label authoritative-v3 --include-1h
```

Do not use `--allow-no-news` for real Phase 0 validation.

## Output

- `data/runtime/calibration/summary.json`
- `review-5m.csv/json`
- `review-15m.csv/json`
- optional `review-1h.csv/json`
- `data/runtime/tbot-calibration.zip`

The runner clears stale review files before every calibration so an old 1H
study cannot contaminate a new primary-timeframe validation.

## Readiness

Run:

```powershell
.\.venv\Scripts\python.exe scripts\preflight_demo.py
```

Forward demo remains blocked until the calibration readiness gate accepts the
current schema-v3 contract.

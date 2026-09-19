# Calibration Workflow Without Owner Screenshots

Because chart examples are not currently available, Phase 0 uses a provisional detector only to create examples that can be reviewed.

## Process

1. Fetch historical XAUUSD 5M + 15M data.
2. Run provisional Flip Zone detection.
3. Apply provisional rejection scoring.
4. Apply provisional higher-timeframe pivot break confirmation.
5. Detect a later retest from the correct side.
6. Apply normal strategy gates.
7. Save/show every READY and SKIPPED setup.
8. Review the generated examples.
9. Tune detector parameters.
10. Freeze a calibrated strategy version before the demo week.

## Command

After setting TWELVE_DATA_API_KEY:

python scripts/scan_history.py --entry-tf 5M --bars 1000

Other examples:

python scripts/scan_history.py --entry-tf 15M --bars 1000
python scripts/scan_history.py --entry-tf 1H --bars 1000

The scanner does not place orders and is not a broker simulator.

## What success means at this stage

Success is not high profit.

Success means the generated zones and rejected/accepted setups are plausible enough to review and refine. Only after the detection logic is calibrated should a serious profitability backtest be built.

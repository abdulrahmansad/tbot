from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime

from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.flip_dip.backtest import ProvisionalBacktester
from tbot.flip_dip.calibration import export_calibration_csv, export_calibration_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan historical XAUUSD data with provisional Flip & Dip v0 rules."
    )
    parser.add_argument("--entry-tf", choices=["5M", "15M", "1H"], default="5M")
    parser.add_argument("--bars", type=int, default=1000)
    parser.add_argument("--rr", type=float, default=5.0)
    parser.add_argument("--start", help="UTC ISO datetime, e.g. 2026-08-01T00:00:00+00:00")
    parser.add_argument("--end", help="UTC ISO datetime")
    parser.add_argument("--csv-out", help="Optional calibration CSV output path")
    parser.add_argument("--json-out", help="Optional calibration JSON output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    confirmation = {"5M": "15M", "15M": "1H", "1H": "4H"}[args.entry_tf]
    start = datetime.fromisoformat(args.start) if args.start else None
    end = datetime.fromisoformat(args.end) if args.end else None

    provider = TwelveDataXauUsdProvider()
    entry = provider.fetch_candles(
        timeframe=args.entry_tf,
        outputsize=args.bars,
        start=start,
        end=end,
    )
    htf = provider.fetch_candles(
        timeframe=confirmation,
        outputsize=args.bars,
        start=start,
        end=end,
    )

    scanner = ProvisionalBacktester()
    setups = scanner.scan(
        {
            args.entry_tf: entry,
            confirmation: htf,
        },
        entry_timeframe=args.entry_tf,
        planned_rr=args.rr,
    )

    print(f"XAUUSD provisional v0 scan: {args.entry_tf} -> {confirmation}")
    print(f"Entry candles: {len(entry)} | HTF candles: {len(htf)}")
    print(f"Detected Flip & Dip candidates: {len(setups)}")

    reason_counts: Counter[str] = Counter()
    ready = 0

    for index, setup in enumerate(setups, 1):
        zone = setup.zone
        decision = setup.decision
        if decision.plan is not None:
            ready += 1
            label = "PLAN_READY"
        else:
            label = "SKIP"
            reason_counts.update(decision.reasons)

        print(
            f"{index:03d} {zone.created_at.isoformat()} "
            f"{zone.direction.value} "
            f"zone={zone.lower_price:.2f}-{zone.upper_price:.2f} "
            f"rejection={setup.rejection_score:.2f} "
            f"{label}"
        )
        if decision.reasons:
            print("    reasons:", ", ".join(decision.reasons))

    print()
    print(f"READY: {ready}")
    print(f"SKIPPED: {len(setups) - ready}")
    if reason_counts:
        print("Skip reasons:")
        for reason, count in reason_counts.most_common():
            print(f"  {reason}: {count}")

    if args.csv_out:
        path = export_calibration_csv(setups, args.csv_out)
        print(f"Calibration CSV: {path}")
    if args.json_out:
        path = export_calibration_json(setups, args.json_out)
        print(f"Calibration JSON: {path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.flip_dip.backtest import ProvisionalBacktester
from tbot.flip_dip.calibration import export_calibration_csv, export_calibration_json


TIMEFRAMES = (
    ("5M", "15M"),
    ("15M", "1H"),
    ("1H", "4H"),
)


def run_one(provider, scanner, entry_tf, confirmation_tf, bars, out_dir):
    entry = provider.fetch_candles(timeframe=entry_tf, outputsize=bars)
    htf = provider.fetch_candles(timeframe=confirmation_tf, outputsize=bars)
    setups = scanner.scan(
        {entry_tf: entry, confirmation_tf: htf},
        entry_timeframe=entry_tf,
        planned_rr=5.0,
    )

    csv_path = export_calibration_csv(setups, out_dir / f"review-{entry_tf.lower()}.csv")
    json_path = export_calibration_json(setups, out_dir / f"review-{entry_tf.lower()}.json")

    reasons = Counter()
    ready = 0
    for setup in setups:
        if setup.decision.plan is not None:
            ready += 1
        else:
            reasons.update(setup.decision.reasons)

    return {
        "entry_timeframe": entry_tf,
        "confirmation_timeframe": confirmation_tf,
        "entry_candles": len(entry),
        "confirmation_candles": len(htf),
        "candidate_count": len(setups),
        "ready_count": ready,
        "skipped_count": len(setups) - ready,
        "skip_reasons": dict(reasons.most_common()),
        "csv": str(csv_path),
        "json": str(json_path),
    }


def main():
    out_dir = Path("data/runtime/calibration")
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = TwelveDataXauUsdProvider()
    scanner = ProvisionalBacktester()

    summaries = []
    for entry_tf, confirmation_tf in TIMEFRAMES:
        print(f"Running {entry_tf} -> {confirmation_tf}...")
        summary = run_one(
            provider,
            scanner,
            entry_tf,
            confirmation_tf,
            1000,
            out_dir,
        )
        summaries.append(summary)
        print(
            f"  candidates={summary['candidate_count']} "
            f"ready={summary['ready_count']} "
            f"skipped={summary['skipped_count']}"
        )

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    zip_path = Path("data/runtime/tbot-calibration.zip")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(out_dir.glob("*")):
            archive.write(path, arcname=path.name)

    print(f"Summary: {summary_path}")
    print(f"Calibration bundle: {zip_path}")


if __name__ == "__main__":
    main()

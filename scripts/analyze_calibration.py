from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


TIMEFRAMES = ("5m", "15m", "1h")


def as_float(value):
    if value in (None, ""):
        return None
    return float(value)


def load_rows(root: Path):
    rows = []
    for tf in TIMEFRAMES:
        path = root / f"review-{tf}.csv"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["_source_tf"] = tf
                rows.append(row)
    return rows


def summarize(root: Path):
    rows = load_rows(root)
    ready = [r for r in rows if r.get("status") == "PLAN_READY"]
    primary = [
        r for r in ready if str(r.get("cluster_primary", "")).lower() == "true"
    ]

    outcome_counts = Counter(r.get("outcome_status") or "UNRESOLVED" for r in primary)
    by_tf = {}
    by_direction = {}

    for tf in TIMEFRAMES:
        subset = [r for r in primary if r["_source_tf"] == tf]
        by_tf[tf.upper()] = {
            "primary_events": len(subset),
            "outcomes": dict(
                Counter(r.get("outcome_status") or "UNRESOLVED" for r in subset)
            ),
        }

    for direction in ("BUY", "SELL"):
        subset = [r for r in primary if r.get("direction") == direction]
        by_direction[direction] = {
            "primary_events": len(subset),
            "outcomes": dict(
                Counter(r.get("outcome_status") or "UNRESOLVED" for r in subset)
            ),
        }

    widths = []
    rejection_scores = []
    mfe_values = []
    mae_values = []
    for row in primary:
        width_bps = as_float(row.get("zone_width_bps"))
        if width_bps is None:
            lower = as_float(row.get("zone_lower"))
            upper = as_float(row.get("zone_upper"))
            if lower is not None and upper is not None:
                mid = (lower + upper) / 2
                width_bps = ((upper - lower) / mid) * 10000 if mid else None
        if width_bps is not None:
            widths.append(width_bps)

        score = as_float(row.get("rejection_score"))
        if score is not None:
            rejection_scores.append(score)

        mfe = as_float(row.get("max_favorable_r"))
        mae = as_float(row.get("max_adverse_r"))
        if mfe is not None:
            mfe_values.append(mfe)
        if mae is not None:
            mae_values.append(mae)

    return {
        "candidate_count": len(rows),
        "ready_zone_count": len(ready),
        "primary_event_count": len(primary),
        "secondary_zone_count": max(len(ready) - len(primary), 0),
        "primary_outcomes": dict(outcome_counts),
        "by_timeframe": by_tf,
        "by_direction": by_direction,
        "diagnostics": {
            "median_rejection_score": median(rejection_scores) if rejection_scores else None,
            "median_zone_width_bps": median(widths) if widths else None,
            "minimum_zone_width_bps": min(widths) if widths else None,
            "maximum_zone_width_bps": max(widths) if widths else None,
            "maximum_favorable_r": max(mfe_values) if mfe_values else None,
            "maximum_adverse_r": max(mae_values) if mae_values else None,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="data/runtime/calibration",
        help="Directory containing review-5m/15m/1h CSV files.",
    )
    parser.add_argument(
        "--json-out",
        default="data/runtime/calibration-analysis.json",
    )
    args = parser.parse_args()

    result = summarize(Path(args.dir))
    print(json.dumps(result, indent=2))

    target = Path(args.json_out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Analysis: {target}")


if __name__ == "__main__":
    main()

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


def _segment_metrics(rows):
    if not rows:
        return {
            "events": 0,
            "target_5r": 0,
            "partial_or_better": 0,
            "invalidated": 0,
        }
    outcomes = Counter(row.get("outcome_status") or "UNRESOLVED" for row in rows)
    return {
        "events": len(rows),
        "target_5r": outcomes.get("TARGET_5R", 0),
        "partial_or_better": (
            outcomes.get("TARGET_2R", 0)
            + outcomes.get("TARGET_3_5R", 0)
            + outcomes.get("TARGET_5R", 0)
        ),
        "invalidated": outcomes.get("INVALIDATED", 0),
    }


def _chronological_direction_checks(primary):
    checks = {}
    warnings = []
    for tf in ("5M", "15M", "1H"):
        tf_rows = [row for row in primary if row.get("entry_timeframe") == tf]
        tf_rows.sort(key=lambda row: row.get("retest_at") or row.get("created_at") or "")
        midpoint = len(tf_rows) // 2
        halves = {
            "early": tf_rows[:midpoint],
            "late": tf_rows[midpoint:],
        }
        checks[tf] = {}
        for direction in ("BUY", "SELL"):
            early = [row for row in halves["early"] if row.get("direction") == direction]
            late = [row for row in halves["late"] if row.get("direction") == direction]
            checks[tf][direction] = {
                "early": _segment_metrics(early),
                "late": _segment_metrics(late),
            }

            total_events = len(early) + len(late)
            early_5r = sum(row.get("outcome_status") == "TARGET_5R" for row in early)
            late_5r = sum(row.get("outcome_status") == "TARGET_5R" for row in late)
            if total_events >= 12 and early and late and early_5r == 0 and late_5r == 0:
                warnings.append(
                    {
                        "type": "persistent_zero_5r_segment",
                        "timeframe": tf,
                        "direction": direction,
                        "events": total_events,
                        "note": (
                            "Observed zero TARGET_5R outcomes in both chronological halves. "
                            "Treat as a calibration warning, not a hard strategy gate, until "
                            "validated on a second independent sample."
                        ),
                    }
                )
    return checks, warnings


def summarize(root: Path):
    rows = load_rows(root)
    ready = [r for r in rows if r.get("status") == "PLAN_READY"]
    primary = [
        r for r in ready if str(r.get("cluster_primary", "")).lower() == "true"
    ]

    outcome_counts = Counter(r.get("outcome_status") or "UNRESOLVED" for r in primary)
    chronological_checks, calibration_warnings = _chronological_direction_checks(primary)
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
        "chronological_direction_checks": chronological_checks,
        "calibration_warnings": calibration_warnings,
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

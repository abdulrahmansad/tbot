from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .backtest import HistoricalSetup


def setup_to_row(setup: HistoricalSetup) -> dict[str, object]:
    zone = setup.zone
    plan = setup.decision.plan
    return {
        "zone_id": zone.id,
        "created_at": zone.created_at.isoformat(),
        "direction": zone.direction.value,
        "entry_timeframe": zone.timeframe.value,
        "zone_lower": zone.lower_price,
        "zone_upper": zone.upper_price,
        "rejection_score": round(setup.rejection_score, 4),
        "status": "PLAN_READY" if plan is not None else "SKIP",
        "skip_reasons": "|".join(setup.decision.reasons),
        "confirmation_timeframe": plan.confirmation_timeframe if plan else "",
        "execution_number": plan.execution_number if plan else "",
        "minimum_rr": plan.minimum_rr if plan else "",
        "risk_percent": plan.risk_percent if plan else "",
        "invalidation_rule": plan.invalidation_rule if plan else "",
    }


def export_calibration_csv(
    setups: Iterable[HistoricalSetup],
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [setup_to_row(setup) for setup in setups]

    fieldnames = [
        "zone_id",
        "created_at",
        "direction",
        "entry_timeframe",
        "zone_lower",
        "zone_upper",
        "rejection_score",
        "status",
        "skip_reasons",
        "confirmation_timeframe",
        "execution_number",
        "minimum_rr",
        "risk_percent",
        "invalidation_rule",
    ]

    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return target


def export_calibration_json(
    setups: Iterable[HistoricalSetup],
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [setup_to_row(setup) for setup in setups]
    target.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return target

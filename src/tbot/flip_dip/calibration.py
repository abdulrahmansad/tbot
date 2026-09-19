from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .backtest import HistoricalSetup
from .clustering import cluster_lookup


FIELDNAMES = [
    "zone_id",
    "cluster_id",
    "cluster_rank",
    "cluster_primary",
    "created_at",
    "rejection_observed_at",
    "retest_at",
    "structure_observed_at",
    "direction",
    "entry_timeframe",
    "zone_lower",
    "zone_upper",
    "zone_width",
    "zone_mid_price",
    "zone_width_bps",
    "rejection_score",
    "status",
    "skip_reasons",
    "confirmation_timeframe",
    "structure_kind",
    "execution_number",
    "minimum_rr",
    "risk_percent",
    "invalidation_rule",
    "outcome_status",
    "outcome_resolved_at",
    "entry_reference_price",
    "sizing_reference_price",
    "risk_unit",
    "target_2r",
    "target_3_5r",
    "target_5r",
    "max_favorable_r",
    "max_adverse_r",
    "bars_observed",
    "ambiguity_reason",
]


def setup_to_row(
    setup: HistoricalSetup,
    cluster: tuple[str, int, bool] | None = None,
) -> dict[str, object]:
    zone = setup.zone
    plan = setup.decision.plan
    outcome = setup.outcome
    cluster_id, cluster_rank, cluster_primary = cluster or ("", "", "")
    return {
        "zone_id": zone.id,
        "cluster_id": cluster_id,
        "cluster_rank": cluster_rank,
        "cluster_primary": cluster_primary,
        "created_at": zone.created_at.isoformat(),
        "rejection_observed_at": (
            setup.rejection_observed_at.isoformat()
            if setup.rejection_observed_at
            else ""
        ),
        "retest_at": setup.retest_at.isoformat() if setup.retest_at else "",
        "structure_observed_at": (
            setup.structure.observed_at.isoformat()
            if setup.structure and setup.structure.observed_at
            else ""
        ),
        "direction": zone.direction.value,
        "entry_timeframe": zone.timeframe.value,
        "zone_lower": zone.lower_price,
        "zone_upper": zone.upper_price,
        "zone_width": zone.upper_price - zone.lower_price,
        "zone_mid_price": (zone.upper_price + zone.lower_price) / 2.0,
        "zone_width_bps": (
            ((zone.upper_price - zone.lower_price)
            / max((zone.upper_price + zone.lower_price) / 2.0, 1e-9))
            * 10000.0
        ),
        "rejection_score": round(setup.rejection_score, 4),
        "status": "PLAN_READY" if plan is not None else "SKIP",
        "skip_reasons": "|".join(setup.decision.reasons),
        "confirmation_timeframe": plan.confirmation_timeframe if plan else "",
        "structure_kind": setup.structure.kind if setup.structure else "",
        "execution_number": plan.execution_number if plan else "",
        "minimum_rr": plan.minimum_rr if plan else "",
        "risk_percent": plan.risk_percent if plan else "",
        "invalidation_rule": plan.invalidation_rule if plan else "",
        "outcome_status": outcome.status.value if outcome else "",
        "outcome_resolved_at": (
            outcome.resolved_at.isoformat()
            if outcome and outcome.resolved_at is not None
            else ""
        ),
        "entry_reference_price": outcome.entry_reference_price if outcome else "",
        "sizing_reference_price": (
            plan.sizing_reference_price if plan and plan.sizing_reference_price is not None else ""
        ),
        "risk_unit": outcome.risk_unit if outcome else "",
        "target_2r": outcome.target_2r if outcome else "",
        "target_3_5r": outcome.target_3_5r if outcome else "",
        "target_5r": outcome.target_5r if outcome else "",
        "max_favorable_r": round(outcome.max_favorable_r, 4) if outcome else "",
        "max_adverse_r": round(outcome.max_adverse_r, 4) if outcome else "",
        "bars_observed": outcome.bars_observed if outcome else "",
        "ambiguity_reason": outcome.ambiguity_reason if outcome else "",
    }


def _rows(setups: Iterable[HistoricalSetup]) -> list[dict[str, object]]:
    materialized = list(setups)
    clusters = cluster_lookup(materialized)
    return [
        setup_to_row(setup, clusters.get(setup.zone.id))
        for setup in materialized
    ]


def export_calibration_csv(
    setups: Iterable[HistoricalSetup],
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = _rows(setups)

    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return target


def export_calibration_json(
    setups: Iterable[HistoricalSetup],
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_rows(setups), indent=2), encoding="utf-8")
    return target

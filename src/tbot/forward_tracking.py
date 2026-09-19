from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .data.provider import MarketDataProvider
from .flip_dip.models import Direction, EntryTimeframe, FlipZone
from .flip_dip.outcome import OutcomeStatus, simulate_historical_outcome


_TERMINAL = {
    OutcomeStatus.TARGET_5R.value,
    OutcomeStatus.INVALIDATED.value,
    OutcomeStatus.AMBIGUOUS.value,
}


class ForwardResultStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, results: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(results, indent=2), encoding="utf-8")


class ForwardOutcomeTracker:
    """Update hypothetical forward-plan outcomes from market candles."""

    def __init__(
        self,
        *,
        market_data: MarketDataProvider,
        plans_path: str | Path = "data/runtime/forward-plans.jsonl",
        results_path: str | Path = "data/runtime/forward-results.json",
    ) -> None:
        self.market_data = market_data
        self.plans_path = Path(plans_path)
        self.results = ForwardResultStore(results_path)

    def update(self, *, bars: int = 1000) -> dict[str, dict[str, Any]]:
        stored = self.results.read()
        if not self.plans_path.exists():
            return stored

        plans = self._read_plans()
        candles_cache: dict[str, list] = {}

        for row in plans:
            plan_id = row["plan_id"]
            previous = stored.get(plan_id)
            if previous and previous.get("outcome_status") in _TERMINAL:
                continue

            plan = row["plan"]
            timeframe = plan["entry_timeframe"]
            if timeframe not in candles_cache:
                candles_cache[timeframe] = self.market_data.fetch_candles(
                    timeframe=timeframe,
                    outputsize=bars,
                )
            candles = candles_cache[timeframe]
            if not candles:
                continue

            activated_at = datetime.fromisoformat(row["created_at"])
            if activated_at < candles[0].timestamp:
                stored[plan_id] = {
                    "outcome_status": "INSUFFICIENT_HISTORY",
                    "updated_at": candles[-1].timestamp.isoformat(),
                }
                continue

            zone = FlipZone(
                id=plan["zone_id"],
                direction=Direction(plan["direction"]),
                timeframe=EntryTimeframe(timeframe),
                lower_price=float(plan["entry_low"]),
                upper_price=float(plan["entry_high"]),
                created_at=activated_at,
            )
            outcome = simulate_historical_outcome(
                zone=zone,
                candles=candles,
                activated_at=activated_at,
                sizing_reference_price=(
                    float(plan["sizing_reference_price"])
                    if plan.get("sizing_reference_price") is not None
                    else None
                ),
            )
            stored[plan_id] = {
                "outcome_status": outcome.status.value,
                "outcome_resolved_at": (
                    outcome.resolved_at.isoformat()
                    if outcome.resolved_at is not None
                    else None
                ),
                "entry_reference_price": outcome.entry_reference_price,
                "sizing_reference_price": plan.get("sizing_reference_price"),
                "risk_unit": outcome.risk_unit,
                "target_2r": outcome.target_2r,
                "target_3_5r": outcome.target_3_5r,
                "target_5r": outcome.target_5r,
                "max_favorable_r": round(outcome.max_favorable_r, 4),
                "max_adverse_r": round(outcome.max_adverse_r, 4),
                "bars_observed": outcome.bars_observed,
                "ambiguity_reason": outcome.ambiguity_reason,
                "updated_at": candles[-1].timestamp.isoformat(),
            }

        self.results.write(stored)
        return stored

    def _read_plans(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self.plans_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    rows.append(json.loads(stripped))
        return rows

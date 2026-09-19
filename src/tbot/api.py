from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from .dashboard_html import DASHBOARD_HTML
from .data.provider import MarketDataProvider
from .data.twelve_data import TwelveDataXauUsdProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.clustering import cluster_lookup
from .strategy_version import provisional_v0


DEFAULT_CALIBRATION_DIR = Path("data/runtime/calibration")
DEFAULT_FORWARD_PLANS_PATH = Path("data/runtime/forward-plans.jsonl")
DEFAULT_FORWARD_RESULTS_PATH = Path("data/runtime/forward-results.json")
SUPPORTED_ENTRY_TIMEFRAMES = ("5M", "15M", "1H")


def _read_rows(calibration_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for timeframe in ("5m", "15m", "1h"):
        path = calibration_dir / f"review-{timeframe}.csv"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def _number(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _history_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "zone_id": row.get("zone_id"),
        "cluster_id": row.get("cluster_id") or None,
        "cluster_rank": int(row["cluster_rank"]) if row.get("cluster_rank") else None,
        "cluster_primary": row.get("cluster_primary", "").lower() == "true",
        "created_at": row.get("created_at"),
        "retest_at": row.get("retest_at") or None,
        "structure_observed_at": row.get("structure_observed_at") or None,
        "direction": row.get("direction"),
        "entry_timeframe": row.get("entry_timeframe"),
        "zone_lower": _number(row.get("zone_lower")),
        "zone_upper": _number(row.get("zone_upper")),
        "rejection_score": _number(row.get("rejection_score")),
        "outcome_status": row.get("outcome_status") or None,
        "max_favorable_r": _number(row.get("max_favorable_r")),
        "max_adverse_r": _number(row.get("max_adverse_r")),
        "outcome_resolved_at": row.get("outcome_resolved_at") or None,
    }


def create_app(
    *,
    market_data: MarketDataProvider | None = None,
    calibration_dir: str | Path = DEFAULT_CALIBRATION_DIR,
    forward_plans_path: str | Path = DEFAULT_FORWARD_PLANS_PATH,
    forward_results_path: str | Path = DEFAULT_FORWARD_RESULTS_PATH,
) -> FastAPI:
    root = Path(calibration_dir)
    forward_path = Path(forward_plans_path)
    forward_results = Path(forward_results_path)
    app = FastAPI(
        title="TBOT Phase 0 API",
        version="0.1.0",
        description=(
            "Read-only XAUUSD Flip & Dip planning/demo API. "
            "No broker execution endpoints are provided."
        ),
    )

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return DASHBOARD_HTML

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        version = provisional_v0(datetime.now(timezone.utc))
        return {
            "status": "ok",
            "symbol": "XAUUSD",
            "strategy_version": version.name,
            "strategy_state": version.state.value,
            "execution_enabled": False,
            "mode": "planning_and_demo_only",
        }

    @app.get("/api/performance")
    def performance() -> dict[str, Any]:
        rows = _read_rows(root)
        ready = [row for row in rows if row.get("status") == "PLAN_READY"]
        primary = [
            row
            for row in ready
            if row.get("cluster_primary", "").lower() == "true"
        ]
        outcomes = Counter(row.get("outcome_status") or "UNRESOLVED" for row in ready)
        primary_outcomes = Counter(
            row.get("outcome_status") or "UNRESOLVED" for row in primary
        )
        forward_outcomes: Counter[str] = Counter()
        if forward_results.exists():
            import json

            payload = json.loads(forward_results.read_text(encoding="utf-8"))
            forward_outcomes.update(
                item.get("outcome_status", "UNRESOLVED")
                for item in payload.values()
            )

        return {
            "source": "historical_calibration_plus_forward_demo",
            "candidate_count": len(rows),
            "ready_zone_count": len(ready),
            "independent_event_count": len(primary),
            "secondary_zone_count": max(len(ready) - len(primary), 0),
            "outcomes_all_ready_zones": dict(outcomes),
            "outcomes_primary_events": dict(primary_outcomes),
            "forward_demo_outcomes": dict(forward_outcomes),
            "metric_note": (
                "Historical R uses provisional zone-width normalization; "
                "it is not broker-realized P&L."
            ),
        }

    @app.get("/api/history")
    def history(
        limit: int = Query(default=50, ge=1, le=500),
        primary_only: bool = True,
    ) -> dict[str, Any]:
        rows = [
            row
            for row in _read_rows(root)
            if row.get("status") == "PLAN_READY"
        ]
        if primary_only:
            rows = [
                row
                for row in rows
                if row.get("cluster_primary", "").lower() == "true"
            ]
        rows.sort(
            key=lambda row: row.get("retest_at") or row.get("created_at") or "",
            reverse=True,
        )
        return {
            "count": min(len(rows), limit),
            "primary_only": primary_only,
            "items": [_history_row(row) for row in rows[:limit]],
        }

    @app.get("/api/plans")
    def plans() -> dict[str, Any]:
        if not forward_path.exists():
            return {
                "mode": "forward_demo",
                "execution_enabled": False,
                "count": 0,
                "items": [],
            }

        results_payload: dict[str, Any] = {}
        if forward_results.exists():
            import json

            results_payload = json.loads(forward_results.read_text(encoding="utf-8"))

        items: list[dict[str, Any]] = []
        with forward_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                import json

                row = json.loads(stripped)
                plan = row.get("plan", {})
                items.append(
                    {
                        "plan_id": row.get("plan_id"),
                        "created_at": row.get("created_at"),
                        "direction": plan.get("direction"),
                        "entry_timeframe": plan.get("entry_timeframe"),
                        "confirmation_timeframe": plan.get("confirmation_timeframe"),
                        "zone_lower": plan.get("entry_low"),
                        "zone_upper": plan.get("entry_high"),
                        "minimum_rr": plan.get("minimum_rr"),
                        "risk_percent": plan.get("risk_percent"),
                        "sizing_reference_price": plan.get("sizing_reference_price"),
                        "execution_number": plan.get("execution_number"),
                        "invalidation_rule": plan.get("invalidation_rule"),
                        "outcome_status": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("outcome_status", "OPEN"),
                        "max_favorable_r": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("max_favorable_r"),
                        "max_adverse_r": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("max_adverse_r"),
                        "outcome_resolved_at": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("outcome_resolved_at"),
                    }
                )

        items.sort(key=lambda row: row.get("created_at") or "", reverse=True)
        return {
            "mode": "forward_demo",
            "execution_enabled": False,
            "count": len(items),
            "items": items,
        }

    @app.get("/api/live")
    def live(
        entry_timeframe: str = Query(default="5M"),
        bars: int = Query(default=500, ge=100, le=5000),
    ) -> dict[str, Any]:
        timeframe = entry_timeframe.upper()
        if timeframe not in SUPPORTED_ENTRY_TIMEFRAMES:
            return {
                "status": "error",
                "error": "unsupported_entry_timeframe",
                "supported": list(SUPPORTED_ENTRY_TIMEFRAMES),
            }

        provider = market_data
        if provider is None:
            try:
                provider = TwelveDataXauUsdProvider()
            except ValueError:
                return {
                    "status": "not_configured",
                    "symbol": "XAUUSD",
                    "entry_timeframe": timeframe,
                    "execution_enabled": False,
                }

        scanner = ProvisionalBacktester()
        confirmation = scanner.strategy_config.confirmation_timeframe[timeframe]
        entry = provider.fetch_candles(timeframe=timeframe, outputsize=bars)
        htf = provider.fetch_candles(timeframe=confirmation, outputsize=bars)
        setups = scanner.scan(
            {timeframe: entry, confirmation: htf},
            entry_timeframe=timeframe,
            planned_rr=5.0,
        )
        clusters = cluster_lookup(setups)

        ready = [
            setup
            for setup in setups
            if setup.decision.plan is not None
        ]
        ready.sort(key=lambda setup: setup.retest_at or setup.zone.created_at)
        latest = ready[-1] if ready else None

        latest_payload = None
        if latest is not None:
            cluster = clusters.get(latest.zone.id)
            latest_payload = {
                "zone_id": latest.zone.id,
                "cluster_id": cluster[0] if cluster else None,
                "cluster_rank": cluster[1] if cluster else None,
                "cluster_primary": cluster[2] if cluster else None,
                "direction": latest.zone.direction.value,
                "entry_timeframe": latest.zone.timeframe.value,
                "confirmation_timeframe": confirmation,
                "zone_lower": latest.zone.lower_price,
                "zone_upper": latest.zone.upper_price,
                "rejection_score": round(latest.rejection_score, 4),
                "retest_at": latest.retest_at,
                "structure_kind": latest.structure.kind if latest.structure else None,
                "structure_observed_at": (
                    latest.structure.observed_at if latest.structure else None
                ),
                "minimum_rr": latest.decision.plan.minimum_rr,
                "risk_percent": latest.decision.plan.risk_percent,
                "sizing_reference_price": latest.decision.plan.sizing_reference_price,
                "invalidation_rule": latest.decision.plan.invalidation_rule,
            }

        return {
            "status": "ok",
            "symbol": "XAUUSD",
            "entry_timeframe": timeframe,
            "confirmation_timeframe": confirmation,
            "latest_candle_at": entry[-1].timestamp if entry else None,
            "candidate_count": len(setups),
            "ready_zone_count": len(ready),
            "latest_ready_plan": latest_payload,
            "news_gate": "not_connected",
            "execution_enabled": False,
            "warning": (
                "Latest READY plan is a planning signal from the current "
                "provisional detector, not an executed trade."
            ),
        }

    return app


app = create_app()

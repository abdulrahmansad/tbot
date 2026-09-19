from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse

from .access import BasicAccessConfig, basic_authorized, private_access_from_env
from .account_simulator import DEFAULT_OUTCOME_R, simulate_account
from .calibration_status import evaluate_calibration_readiness
from .dashboard_html import DASHBOARD_HTML
from .data.provider import MarketDataProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.clustering import cluster_lookup
from .live_snapshot import LiveSnapshotStore
from .runtime_status import evaluate_worker_snapshot
from .strategy_version import candidate_v1


DEFAULT_CALIBRATION_DIR = Path("data/runtime/calibration")
DEFAULT_FORWARD_PLANS_PATH = Path("data/runtime/forward-plans.jsonl")
DEFAULT_FORWARD_RESULTS_PATH = Path("data/runtime/forward-results.json")
DEFAULT_LIVE_SNAPSHOT_PATH = Path("data/runtime/live-snapshot.json")
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
        "terminal": row.get("outcome_terminal", "").lower() == "true",
        "terminal_reason": row.get("outcome_terminal_reason") or None,
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
    live_snapshot_path: str | Path = DEFAULT_LIVE_SNAPSHOT_PATH,
    access_config: BasicAccessConfig | None = None,
) -> FastAPI:
    root = Path(calibration_dir)
    forward_path = Path(forward_plans_path)
    forward_results = Path(forward_results_path)
    live_snapshot = LiveSnapshotStore(live_snapshot_path)
    app = FastAPI(
        title="TBOT Phase 0 API",
        version="0.1.0",
        description=(
            "Read-only XAUUSD Flip & Dip planning/demo API. "
            "No broker execution endpoints are provided."
        ),
    )

    if access_config is not None:
        @app.middleware("http")
        async def private_demo_access(request: Request, call_next):
            if request.url.path == "/api/health":
                return await call_next(request)
            if not basic_authorized(
                request.headers.get("Authorization"),
                access_config,
            ):
                return Response(
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                )
            return await call_next(request)

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return DASHBOARD_HTML

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        version = candidate_v1(datetime.now(timezone.utc))
        snapshot = live_snapshot.read()
        worker = evaluate_worker_snapshot(snapshot)
        return {
            "status": "ok",
            "symbol": "XAUUSD",
            "strategy_version": version.name,
            "strategy_state": version.state.value,
            "execution_enabled": False,
            "mode": "planning_and_demo_only",
            "worker": {
                "status": worker.status,
                "fresh": worker.fresh,
                "last_scan_at": worker.last_scan_at,
                "age_seconds": worker.age_seconds,
                "news_provider_connected": snapshot.get(
                    "news_provider_connected", False
                ),
                "news_provider_name": snapshot.get("news_provider_name"),
                "news_provider_failures": snapshot.get(
                    "news_provider_failures", []
                ),
            },
        }

    @app.get("/api/calibration/status")
    def calibration_status() -> dict[str, Any]:
        readiness = evaluate_calibration_readiness(root / "summary.json")
        return {
            "ready_for_forward_demo": readiness.ready_for_forward_demo,
            "reasons": list(readiness.reasons),
            "bars_requested": readiness.bars_requested,
            "primary_events": readiness.primary_events,
            "ambiguous_primary_events": readiness.ambiguous_primary_events,
            "risk_model": readiness.risk_model,
            "schema_version": readiness.schema_version,
            "strategy_contract_version": readiness.strategy_contract_version,
            "execution_model": readiness.execution_model,
            "does_not_claim_profitability": True,
        }

    @app.get("/api/performance")
    def performance(
        starting_balance: Annotated[
            float, Query(gt=0, le=1_000_000_000)
        ] = 100.0,
        risk_percent: Annotated[
            float, Query(gt=0, le=100)
        ] = 5.0,
    ) -> dict[str, Any]:
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

        simulation_rows = [
            row
            for row in primary
            if row.get("outcome_status") in DEFAULT_OUTCOME_R
        ]
        simulation_rows.sort(
            key=lambda row: row.get("retest_at") or row.get("created_at") or ""
        )
        simulation = simulate_account(
            simulation_rows,
            starting_balance=starting_balance,
            risk_percent=risk_percent,
        )
        readiness = evaluate_calibration_readiness(root / "summary.json")

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
            "account_simulation": {
                "valid_for_current_strategy_contract": readiness.ready_for_forward_demo,
                "calibration_reasons": list(readiness.reasons),
                "strategy_profit_estimate_available": False,
                "strategy_profit_estimate_reason": (
                    "Owner partial TP percentages/levels are not configured; "
                    "this is a milestone-payout scenario, not exact strategy P&L."
                ),
                "starting_balance": simulation.starting_balance,
                "ending_balance": simulation.ending_balance,
                "net_profit": simulation.net_profit,
                "return_percent": simulation.return_percent,
                "risk_percent": simulation.risk_percent,
                "event_count": simulation.event_count,
                "winning_events": simulation.winning_events,
                "losing_events": simulation.losing_events,
                "flat_events": simulation.flat_events,
                "max_drawdown_percent": simulation.max_drawdown_percent,
                "lowest_balance": simulation.lowest_balance,
                "highest_balance": simulation.highest_balance,
                "equity_curve": [
                    {
                        "index": point.index,
                        "event_time": point.event_time,
                        "outcome_status": point.outcome_status,
                        "r_multiple": point.r_multiple,
                        "balance_before": point.balance_before,
                        "pnl": point.pnl,
                        "balance_after": point.balance_after,
                    }
                    for point in simulation.points
                ],
                "assumptions": {
                    "compounding": True,
                    "primary_events_only": True,
                    "TARGET_5R": 5.0,
                    "TARGET_3_5R": 3.5,
                    "TARGET_2R": 2.0,
                    "INVALIDATED": -1.0,
                    "AMBIGUOUS": 0.0,
                    "note": (
                        "Hypothetical scenario only. Historical candle-close "
                        "invalidation does not guarantee an exact -1R realized loss."
                    ),
                },
            },
            "metric_note": (
                "Historical R uses stabilized structural sizing distance; "
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
                        "terminal": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("terminal", False),
                        "terminal_reason": results_payload.get(
                            row.get("plan_id"), {}
                        ).get("terminal_reason"),
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

        snapshot = live_snapshot.read()
        timeframe_payload = (snapshot.get("timeframes") or {}).get(timeframe)
        if timeframe_payload is not None:
            return {
                **timeframe_payload,
                "symbol": "XAUUSD",
                "scanned_at": snapshot.get("scanned_at"),
                "news_clear": snapshot.get("news_clear"),
                "news_reason": snapshot.get("news_reason"),
                "news_provider_connected": snapshot.get(
                    "news_provider_connected", False
                ),
                "execution_enabled": False,
                "source": "worker_snapshot",
                "warning": (
                    "Latest READY plan is a planning signal from the v1 candidate "
                    "detector, not an executed trade."
                ),
            }

        # Explicitly injected market_data is retained as a development/test
        # fallback. Production web service does not hold the market-data key.
        provider = market_data
        if provider is None:
            return {
                "status": "worker_snapshot_unavailable",
                "symbol": "XAUUSD",
                "entry_timeframe": timeframe,
                "execution_enabled": False,
                "source": "worker_snapshot",
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
        by_zone = {setup.zone.id: setup for setup in setups}
        primary = [
            by_zone[cluster.primary_zone_id]
            for cluster in clusters
            if cluster.primary_zone_id in by_zone
        ]
        primary = [setup for setup in primary if setup.retest_at is not None]
        latest = (
            max(primary, key=lambda setup: setup.retest_at)
            if primary
            else None
        )

        latest_payload = None
        if latest is not None and latest.decision.plan is not None:
            plan = latest.decision.plan
            latest_payload = {
                "zone_id": latest.zone.id,
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
                "minimum_rr": plan.minimum_rr,
                "risk_percent": plan.risk_percent,
                "sizing_reference_price": plan.sizing_reference_price,
                "invalidation_rule": plan.invalidation_rule,
            }

        return {
            "status": "ok",
            "symbol": "XAUUSD",
            "entry_timeframe": timeframe,
            "confirmation_timeframe": confirmation,
            "latest_candle_at": entry[-1].timestamp if entry else None,
            "candidate_count": len(setups),
            "ready_primary_count": len(clusters),
            "latest_ready_plan": latest_payload,
            "news_provider_connected": False,
            "execution_enabled": False,
            "source": "injected_provider_fallback",
            "warning": (
                "Latest READY plan is a planning signal from the v1 candidate "
                "detector, not an executed trade."
            ),
        }

    return app


app = create_app(access_config=private_access_from_env())

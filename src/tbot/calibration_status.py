from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


EXPECTED_SCHEMA_VERSION = 3
EXPECTED_CONTRACT_VERSION = "owner-flip-dip-2026-09-19"
EXPECTED_RISK_MODEL = "structural_rejection_plus_median20_range_floor"
EXPECTED_EXECUTION_MODEL = "distinct_retest_episodes_with_correct_side_rearm"
EXPECTED_PRIMARY_TIMEFRAMES = ("5M", "15M")


@dataclass(frozen=True)
class CalibrationReadiness:
    ready_for_forward_demo: bool
    reasons: tuple[str, ...]
    bars_requested: int
    primary_events: int
    ambiguous_primary_events: int
    risk_model: str | None
    schema_version: int | None
    strategy_contract_version: str | None = None
    execution_model: str | None = None


def evaluate_calibration_readiness(
    summary_path: str | Path,
    *,
    minimum_bars: int = 2000,
    minimum_primary_events: int = 150,
    maximum_ambiguity_rate: float = 0.05,
) -> CalibrationReadiness:
    path = Path(summary_path)
    if not path.exists():
        return CalibrationReadiness(
            ready_for_forward_demo=False,
            reasons=("calibration_summary_missing",),
            bars_requested=0,
            primary_events=0,
            ambiguous_primary_events=0,
            risk_model=None,
            schema_version=None,
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    contract_version = payload.get("strategy_contract_version")
    risk_model = payload.get("risk_model")
    execution_model = payload.get("execution_model")
    bars_requested = int(payload.get("bars_requested") or 0)
    timeframes = payload.get("timeframes") or []

    primary_events = sum(
        int(item.get("independent_event_count") or 0)
        for item in timeframes
        if item.get("entry_timeframe") in EXPECTED_PRIMARY_TIMEFRAMES
    )
    ambiguous = sum(
        int((item.get("primary_outcomes") or {}).get("AMBIGUOUS", 0))
        for item in timeframes
        if item.get("entry_timeframe") in EXPECTED_PRIMARY_TIMEFRAMES
    )

    reasons: list[str] = []
    if schema_version != EXPECTED_SCHEMA_VERSION:
        reasons.append("unsupported_calibration_schema")
    if contract_version != EXPECTED_CONTRACT_VERSION:
        reasons.append("unexpected_strategy_contract")
    if risk_model != EXPECTED_RISK_MODEL:
        reasons.append("unexpected_risk_model")
    if execution_model != EXPECTED_EXECUTION_MODEL:
        reasons.append("unexpected_execution_model")
    if tuple(payload.get("primary_entry_timeframes") or ()) != EXPECTED_PRIMARY_TIMEFRAMES:
        reasons.append("unexpected_primary_entry_timeframes")
    if int(payload.get("max_executions_per_zone") or 0) != 3:
        reasons.append("unexpected_max_executions_per_zone")
    if payload.get("partial_tp_owner_configured") not in (False, True):
        reasons.append("partial_tp_configuration_state_missing")

    observed_primary = {
        item.get("entry_timeframe")
        for item in timeframes
        if item.get("entry_timeframe") in EXPECTED_PRIMARY_TIMEFRAMES
    }
    if observed_primary != set(EXPECTED_PRIMARY_TIMEFRAMES):
        reasons.append("primary_timeframe_calibration_missing")

    if any(
        not bool(item.get("news_filter_applied"))
        for item in timeframes
        if item.get("entry_timeframe") in EXPECTED_PRIMARY_TIMEFRAMES
    ):
        reasons.append("historical_news_filter_missing")

    if bars_requested < minimum_bars:
        reasons.append("insufficient_history_bars")
    if primary_events < minimum_primary_events:
        reasons.append("insufficient_primary_events")

    ambiguity_rate = ambiguous / primary_events if primary_events else 1.0
    if ambiguity_rate > maximum_ambiguity_rate:
        reasons.append("too_many_ambiguous_primary_events")

    return CalibrationReadiness(
        ready_for_forward_demo=not reasons,
        reasons=tuple(reasons),
        bars_requested=bars_requested,
        primary_events=primary_events,
        ambiguous_primary_events=ambiguous,
        risk_model=risk_model,
        schema_version=schema_version,
        strategy_contract_version=contract_version,
        execution_model=execution_model,
    )

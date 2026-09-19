from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class StrategyVersionState(str, Enum):
    DRAFT = "DRAFT"
    CALIBRATING = "CALIBRATING"
    DEMO_ACTIVE = "DEMO_ACTIVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    OWNER_APPROVED = "OWNER_APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class StrategyVersion:
    name: str
    state: StrategyVersionState
    created_at: datetime
    detector_version: str
    notes: str = ""


def provisional_v0(created_at: datetime) -> StrategyVersion:
    return StrategyVersion(
        name="flip-dip-v0-provisional",
        state=StrategyVersionState.CALIBRATING,
        created_at=created_at,
        detector_version="provisional-v0",
        notes="Legacy provisional rules retained only for historical reference.",
    )


def candidate_v1(created_at: datetime) -> StrategyVersion:
    """Legacy candidate retained for old report compatibility only."""
    return StrategyVersion(
        name="flip-dip-v1-candidate-legacy",
        state=StrategyVersionState.REJECTED,
        created_at=created_at,
        detector_version="strict-sequence-stabilized-risk-v1-legacy",
        notes=(
            "Superseded by the authoritative owner strategy contract because "
            "the legacy calibration modeled only first executions per zone."
        ),
    )


def authoritative_v1(
    created_at: datetime,
    *,
    calibration_ready: bool,
    demo_active: bool,
) -> StrategyVersion:
    if not calibration_ready:
        state = StrategyVersionState.CALIBRATING
    elif demo_active:
        state = StrategyVersionState.DEMO_ACTIVE
    else:
        state = StrategyVersionState.REVIEW_REQUIRED

    return StrategyVersion(
        name="flip-dip-v1-authoritative",
        state=state,
        created_at=created_at,
        detector_version="owner-contract-multi-execution-v1",
        notes=(
            "Owner strategy contract applied: XAUUSD, primary 5M/15M entries, "
            "optional 1H, up to three distinct retest executions, strict HTF "
            "CHOCH/BOS chronology, candle-close invalidation, 5% risk cap, "
            "minimum 5R, trading-hours gate and high-impact-news gate."
        ),
    )

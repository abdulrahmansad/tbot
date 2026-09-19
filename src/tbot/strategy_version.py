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
        notes="Temporary rules pending historical calibration and owner review.",
    )


def candidate_v1(created_at: datetime) -> StrategyVersion:
    return StrategyVersion(
        name="flip-dip-v1-candidate",
        state=StrategyVersionState.REVIEW_REQUIRED,
        created_at=created_at,
        detector_version="strict-sequence-stabilized-risk-v1",
        notes=(
            "Historical calibration and 2,000-bar validation completed. "
            "No timeframe/direction hard filters promoted from sample-specific behavior. "
            "Requires forward-demo validation before owner approval."
        ),
    )

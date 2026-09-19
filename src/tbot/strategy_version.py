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

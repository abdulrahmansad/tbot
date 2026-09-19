from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class EntryTimeframe(str, Enum):
    M5 = "5M"
    M15 = "15M"
    H1 = "1H"


class SetupState(str, Enum):
    ZONE_CANDIDATE = "ZONE_CANDIDATE"
    ZONE_VALID = "ZONE_VALID"
    FLIP_OCCURRED = "FLIP_OCCURRED"
    RETURN_CONFIRMED = "RETURN_CONFIRMED"
    REJECTION_CONFIRMED = "REJECTION_CONFIRMED"
    HTF_STRUCTURE_CONFIRMED = "HTF_STRUCTURE_CONFIRMED"
    WAITING_FOR_RETEST = "WAITING_FOR_RETEST"
    PLAN_READY = "PLAN_READY"
    PLAN_TRACKING = "PLAN_TRACKING"
    COMPLETED = "COMPLETED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    EXHAUSTED = "EXHAUSTED"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class FlipZone:
    id: str
    direction: Direction
    timeframe: EntryTimeframe
    lower_price: float
    upper_price: float
    created_at: datetime
    state: SetupState = SetupState.ZONE_CANDIDATE
    rejection_score: float | None = None
    execution_count: int = 0

    def __post_init__(self) -> None:
        if self.lower_price >= self.upper_price:
            raise ValueError("lower_price must be below upper_price")
        if self.execution_count < 0:
            raise ValueError("execution_count cannot be negative")


@dataclass(frozen=True)
class NewsGate:
    clear: bool
    reason: str | None = None
    event_time: datetime | None = None


@dataclass(frozen=True)
class StructureConfirmation:
    confirmed: bool
    timeframe: str
    direction: Direction
    kind: str | None = None  # CHOCH or BOS when known
    observed_at: datetime | None = None


@dataclass(frozen=True)
class TradePlan:
    zone_id: str
    symbol: str
    direction: Direction
    entry_timeframe: EntryTimeframe
    confirmation_timeframe: str
    entry_low: float
    entry_high: float
    invalidation_rule: str
    minimum_rr: float
    risk_percent: float
    execution_number: int
    sizing_reference_price: float | None = None
    status: SetupState = SetupState.PLAN_READY
    notes: tuple[str, ...] = field(default_factory=tuple)

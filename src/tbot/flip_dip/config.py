from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Mapping


@dataclass(frozen=True)
class FlipDipConfig:
    """Authoritative configurable Phase 0 strategy parameters.

    Defaults preserve the owner's written strategy. Ambiguous numerical rules
    remain explicit candidate parameters rather than hidden assumptions.
    """

    strategy_contract_version: str = "owner-flip-dip-2026-09-19"
    symbol: str = "XAUUSD"
    risk_percent: float = 5.0
    minimum_rr: float = 5.0
    max_executions_per_zone: int = 3

    # Owner names 5M/15M as primary. 1H->4H logic exists but is optional.
    primary_entry_timeframes: tuple[str, ...] = ("5M", "15M")
    enable_1h_entries: bool = False

    # Istanbul local time. 23:00 -> 20:00 crosses midnight.
    trading_start: time = time(23, 0)
    trading_end: time = time(20, 0)
    timezone: str = "Europe/Istanbul"

    # Configurable because the owner did not prescribe exact minutes.
    news_blackout_before_minutes: int = 30
    news_blackout_after_minutes: int = 15

    confirmation_timeframe: Mapping[str, str] = field(
        default_factory=lambda: {
            "5M": "15M",
            "15M": "1H",
            "1H": "4H",
        }
    )

    # Candidate quantitative definitions. These are configurable and remain
    # subject to owner/example calibration rather than being immutable rules.
    rejection_min_score: float = 0.60
    flip_zone_definition_version: str = "pivot-zone-candidate-v1"
    structure_definition_version: str = "pivot-break-bos-candidate-v1"

    # Distinct retest episodes: after an execution, price must leave the zone
    # on the correct side before another retest is counted.
    require_rearm_between_retests: bool = True

    # Owner requires partial exits but did not specify percentages/levels.
    # None means "required but not owner-configured"; Phase 0 may track
    # milestones without pretending this is a final exit ladder.
    partial_tp_levels: tuple[tuple[float, float], ...] | None = None

    @property
    def enabled_entry_timeframes(self) -> tuple[str, ...]:
        if self.enable_1h_entries:
            return (*self.primary_entry_timeframes, "1H")
        return self.primary_entry_timeframes

    def validate(self) -> None:
        if self.symbol != "XAUUSD":
            raise ValueError("Phase 0 supports XAUUSD only.")
        if not (0 < self.risk_percent <= 5):
            raise ValueError("risk_percent must be > 0 and cannot exceed the owner's 5% cap")
        if self.minimum_rr < 5:
            raise ValueError("Flip & Dip requires minimum_rr >= 5")
        if not (1 <= self.max_executions_per_zone <= 3):
            raise ValueError("max_executions_per_zone must be between 1 and the owner's cap of 3")
        if self.news_blackout_before_minutes < 0 or self.news_blackout_after_minutes < 0:
            raise ValueError("news blackout values cannot be negative")
        if not (0 <= self.rejection_min_score <= 1):
            raise ValueError("rejection_min_score must be within 0..1")
        if tuple(self.primary_entry_timeframes) != ("5M", "15M"):
            raise ValueError("Owner strategy primary entries must be 5M and 15M")
        required_mapping = {"5M": "15M", "15M": "1H", "1H": "4H"}
        if dict(self.confirmation_timeframe) != required_mapping:
            raise ValueError("confirmation timeframe mapping must match owner strategy")
        if self.partial_tp_levels is not None:
            total = sum(percent for _, percent in self.partial_tp_levels)
            if abs(total - 100.0) > 1e-6:
                raise ValueError("partial TP percentages must total 100")
            if max((r for r, _ in self.partial_tp_levels), default=0) < self.minimum_rr:
                raise ValueError("partial TP plan must include at least the minimum R target")

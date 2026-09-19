from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class PartialTakeProfitNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class TakeProfitLevel:
    r_multiple: float
    close_percent: float


@dataclass(frozen=True)
class TakeProfitPlan:
    levels: tuple[TakeProfitLevel, ...]

    def validate(self, *, minimum_rr: float = 5.0) -> None:
        if not self.levels:
            raise ValueError("At least one take-profit level is required")
        total = sum(level.close_percent for level in self.levels)
        if abs(total - 100.0) > 1e-6:
            raise ValueError("Partial take-profit percentages must total 100%")
        if any(level.close_percent <= 0 for level in self.levels):
            raise ValueError("Each partial percentage must be positive")
        if any(level.r_multiple <= 0 for level in self.levels):
            raise ValueError("Each R target must be positive")
        if max(level.r_multiple for level in self.levels) < minimum_rr:
            raise ValueError("At least one target must reach the minimum R requirement")


def plan_from_levels(
    levels: Iterable[tuple[float, float]],
    *,
    minimum_rr: float = 5.0,
) -> TakeProfitPlan:
    plan = TakeProfitPlan(
        levels=tuple(
            TakeProfitLevel(r_multiple=float(r), close_percent=float(percent))
            for r, percent in levels
        )
    )
    plan.validate(minimum_rr=minimum_rr)
    return plan


def default_provisional_tp_plan() -> TakeProfitPlan:
    """Compatibility guard: no owner-approved default partial ladder exists."""
    raise PartialTakeProfitNotConfigured(
        "Owner strategy requires partial exits, but exact TP levels/percentages "
        "are not defined. Configure FlipDipConfig.partial_tp_levels explicitly."
    )

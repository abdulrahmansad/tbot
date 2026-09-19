from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


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


def default_provisional_tp_plan() -> TakeProfitPlan:
    """Temporary configurable v0 partial exits.

    This is not claimed as the trader's final TP method. It exists so demo and
    reporting logic can operate until the owner defines exact partials.
    """
    plan = TakeProfitPlan(
        levels=(
            TakeProfitLevel(r_multiple=2.0, close_percent=25.0),
            TakeProfitLevel(r_multiple=3.5, close_percent=25.0),
            TakeProfitLevel(r_multiple=5.0, close_percent=50.0),
        )
    )
    plan.validate(minimum_rr=5.0)
    return plan

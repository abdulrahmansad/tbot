from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .config import FlipDipConfig
from .models import (
    FlipZone,
    NewsGate,
    SetupState,
    StructureConfirmation,
    TradePlan,
)
from .time_rules import is_within_trading_window


@dataclass
class PlanDecision:
    plan: TradePlan | None
    reasons: tuple[str, ...]


class FlipDipPlanner:
    def __init__(self, config: FlipDipConfig) -> None:
        config.validate()
        self.config = config

    def build_plan(
        self,
        *,
        zone: FlipZone,
        now: datetime,
        structure: StructureConfirmation,
        rejection_is_healthy: bool,
        news: NewsGate,
        planned_rr: float,
        sizing_reference_price: float | None = None,
    ) -> PlanDecision:
        reasons: list[str] = []

        if zone.state != SetupState.WAITING_FOR_RETEST:
            reasons.append("zone_not_waiting_for_retest")

        if zone.execution_count >= self.config.max_executions_per_zone:
            reasons.append("zone_exhausted")

        if not rejection_is_healthy:
            reasons.append("rejection_not_healthy")

        required_htf = self.config.confirmation_timeframe[zone.timeframe.value]
        if not structure.confirmed:
            reasons.append("htf_structure_not_confirmed")
        elif structure.timeframe != required_htf:
            reasons.append("wrong_confirmation_timeframe")
        elif structure.direction != zone.direction:
            reasons.append("structure_direction_mismatch")

        if planned_rr < self.config.minimum_rr:
            reasons.append("rr_below_minimum")

        if not news.clear:
            reasons.append("high_impact_news_blackout")

        if not is_within_trading_window(
            now,
            timezone=self.config.timezone,
            start=self.config.trading_start,
            end=self.config.trading_end,
        ):
            reasons.append("outside_trading_window")

        if reasons:
            return PlanDecision(plan=None, reasons=tuple(reasons))

        invalidation = (
            f"{zone.timeframe.value} candle CLOSE "
            + ("above" if zone.direction.value == "SELL" else "below")
            + " the Flip & Dip zone"
        )

        return PlanDecision(
            plan=TradePlan(
                zone_id=zone.id,
                symbol=self.config.symbol,
                direction=zone.direction,
                entry_timeframe=zone.timeframe,
                confirmation_timeframe=required_htf,
                entry_low=zone.lower_price,
                entry_high=zone.upper_price,
                invalidation_rule=invalidation,
                minimum_rr=self.config.minimum_rr,
                risk_percent=self.config.risk_percent,
                execution_number=zone.execution_count + 1,
                sizing_reference_price=sizing_reference_price,
            ),
            reasons=(),
        )

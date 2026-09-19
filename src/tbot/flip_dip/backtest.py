from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .config import FlipDipConfig
from .models import Candle, FlipZone, NewsGate, SetupState
from .planner import FlipDipPlanner, PlanDecision
from .provisional import (
    ProvisionalFlipZoneDetector,
    ProvisionalRejectionEvaluator,
    ProvisionalStructureDetector,
)
from .retest import first_retest_after


@dataclass(frozen=True)
class HistoricalSetup:
    zone: FlipZone
    rejection_score: float
    decision: PlanDecision


class ProvisionalBacktester:
    def __init__(
        self,
        *,
        strategy_config: FlipDipConfig | None = None,
        zone_detector: ProvisionalFlipZoneDetector | None = None,
        rejection_evaluator: ProvisionalRejectionEvaluator | None = None,
        structure_detector: ProvisionalStructureDetector | None = None,
    ) -> None:
        self.strategy_config = strategy_config or FlipDipConfig()
        self.planner = FlipDipPlanner(self.strategy_config)
        self.zone_detector = zone_detector or ProvisionalFlipZoneDetector()
        self.rejection_evaluator = rejection_evaluator or ProvisionalRejectionEvaluator()
        self.structure_detector = structure_detector or ProvisionalStructureDetector()

    def scan(
        self,
        candles_by_timeframe: Mapping[str, Sequence[Candle]],
        *,
        entry_timeframe: str,
        planned_rr: float = 5.0,
    ) -> list[HistoricalSetup]:
        entry_candles = list(candles_by_timeframe.get(entry_timeframe, []))
        if not entry_candles:
            return []

        zones = self.zone_detector.detect(entry_candles)
        required_htf = self.strategy_config.confirmation_timeframe[entry_timeframe]
        htf_candles = list(candles_by_timeframe.get(required_htf, []))
        output: list[HistoricalSetup] = []

        for zone in zones:
            rejection_score = self.rejection_evaluator.score(zone, entry_candles)
            healthy = rejection_score >= self.rejection_evaluator.config.minimum_rejection_score

            structure = self.structure_detector.confirm(
                [c for c in htf_candles if c.timestamp <= zone.created_at],
                direction=zone.direction,
                timeframe=required_htf,
            )

            retest = first_retest_after(zone, entry_candles)
            if retest is None:
                decision = PlanDecision(plan=None, reasons=("no_retest_found",))
            else:
                zone.state = SetupState.WAITING_FOR_RETEST
                decision = self.planner.build_plan(
                    zone=zone,
                    now=retest.timestamp,
                    structure=structure,
                    rejection_is_healthy=healthy,
                    news=NewsGate(clear=True),
                    planned_rr=planned_rr,
                )

            output.append(
                HistoricalSetup(
                    zone=zone,
                    rejection_score=rejection_score,
                    decision=decision,
                )
            )

        return output

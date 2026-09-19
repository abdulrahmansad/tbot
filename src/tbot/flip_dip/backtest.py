from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .config import FlipDipConfig
from .models import Candle, FlipZone, NewsGate, SetupState, StructureConfirmation
from .outcome import HistoricalOutcome, simulate_historical_outcome
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
    rejection_observed_at: datetime | None = None
    retest_at: datetime | None = None
    structure: StructureConfirmation | None = None
    outcome: HistoricalOutcome | None = None


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
            rejection = self.rejection_evaluator.evaluate(zone, entry_candles)
            rejection_score = rejection.score
            healthy = (
                rejection_score
                >= self.rejection_evaluator.config.minimum_rejection_score
            )
            structure: StructureConfirmation | None = None
            retest = None
            outcome: HistoricalOutcome | None = None

            if rejection.observed_at is None:
                decision = PlanDecision(
                    plan=None,
                    reasons=("rejection_window_incomplete",),
                )
            else:
                htf_end = htf_candles[-1].timestamp if htf_candles else rejection.observed_at
                structure = self.structure_detector.confirm_between(
                    htf_candles,
                    direction=zone.direction,
                    timeframe=required_htf,
                    start=rejection.observed_at,
                    end=htf_end,
                )

                if not structure.confirmed or structure.observed_at is None:
                    reasons = []
                    if not healthy:
                        reasons.append("rejection_not_healthy")
                    reasons.append("htf_structure_not_confirmed")
                    decision = PlanDecision(plan=None, reasons=tuple(reasons))
                else:
                    retest = first_retest_after(
                        zone,
                        entry_candles,
                        after=structure.observed_at,
                    )
                    if retest is None:
                        reasons = []
                        if not healthy:
                            reasons.append("rejection_not_healthy")
                        reasons.append("no_retest_found")
                        decision = PlanDecision(plan=None, reasons=tuple(reasons))
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
                        if decision.plan is not None:
                            outcome = simulate_historical_outcome(
                                zone=zone,
                                candles=entry_candles,
                                activated_at=retest.timestamp,
                            )

            output.append(
                HistoricalSetup(
                    zone=zone,
                    rejection_score=rejection_score,
                    decision=decision,
                    rejection_observed_at=rejection.observed_at,
                    retest_at=retest.timestamp if retest is not None else None,
                    structure=structure,
                    outcome=outcome,
                )
            )

        return output

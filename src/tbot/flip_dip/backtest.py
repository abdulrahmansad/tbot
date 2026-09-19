from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping, Sequence

from .config import FlipDipConfig
from .models import Candle, FlipZone, NewsGate, SetupState, StructureConfirmation
from .outcome import HistoricalOutcome, simulate_historical_outcome
from .planner import FlipDipPlanner, PlanDecision
from .provisional import (
    ProvisionalDetectorConfig,
    ProvisionalFlipZoneDetector,
    ProvisionalRejectionEvaluator,
    ProvisionalStructureDetector,
)
from .retest import retest_episodes_after
from .sizing import stabilized_sizing_reference


@dataclass(frozen=True)
class HistoricalSetup:
    zone: FlipZone
    rejection_score: float
    decision: PlanDecision
    execution_number: int = 0
    rejection_observed_at: datetime | None = None
    retest_at: datetime | None = None
    structure: StructureConfirmation | None = None
    outcome: HistoricalOutcome | None = None

    @property
    def setup_key(self) -> str:
        if self.execution_number <= 0:
            return f"{self.zone.id}:pre"
        return f"{self.zone.id}:e{self.execution_number}"


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
        self.strategy_config.validate()
        detector_config = ProvisionalDetectorConfig(
            minimum_rejection_score=self.strategy_config.rejection_min_score
        )
        self.planner = FlipDipPlanner(self.strategy_config)
        self.zone_detector = zone_detector or ProvisionalFlipZoneDetector(detector_config)
        self.rejection_evaluator = rejection_evaluator or ProvisionalRejectionEvaluator(
            detector_config
        )
        self.structure_detector = structure_detector or ProvisionalStructureDetector(
            detector_config
        )

    def scan(
        self,
        candles_by_timeframe: Mapping[str, Sequence[Candle]],
        *,
        entry_timeframe: str,
        planned_rr: float | None = None,
        news_gate_at: Callable[[datetime], NewsGate] | None = None,
    ) -> list[HistoricalSetup]:
        if entry_timeframe not in self.strategy_config.confirmation_timeframe:
            raise ValueError(f"unsupported entry timeframe: {entry_timeframe}")

        entry_candles = list(candles_by_timeframe.get(entry_timeframe, []))
        if not entry_candles:
            return []

        zones = self.zone_detector.detect(entry_candles)
        required_htf = self.strategy_config.confirmation_timeframe[entry_timeframe]
        htf_candles = list(candles_by_timeframe.get(required_htf, []))
        output: list[HistoricalSetup] = []
        rr = self.strategy_config.minimum_rr if planned_rr is None else planned_rr
        news_gate_at = news_gate_at or (lambda _: NewsGate(clear=True))

        for zone in zones:
            rejection = self.rejection_evaluator.evaluate(zone, entry_candles)
            rejection_score = rejection.score
            healthy = rejection_score >= self.strategy_config.rejection_min_score

            if rejection.observed_at is None:
                output.append(
                    HistoricalSetup(
                        zone=zone,
                        rejection_score=rejection_score,
                        decision=PlanDecision(
                            plan=None,
                            reasons=("rejection_window_incomplete",),
                        ),
                        rejection_observed_at=None,
                    )
                )
                continue

            if not healthy:
                output.append(
                    HistoricalSetup(
                        zone=zone,
                        rejection_score=rejection_score,
                        decision=PlanDecision(
                            plan=None,
                            reasons=("rejection_not_healthy",),
                        ),
                        rejection_observed_at=rejection.observed_at,
                    )
                )
                continue

            htf_end = (
                htf_candles[-1].timestamp
                if htf_candles
                else rejection.observed_at
            )
            structure = self.structure_detector.confirm_between(
                htf_candles,
                direction=zone.direction,
                timeframe=required_htf,
                start=rejection.observed_at,
                end=htf_end,
            )

            if not structure.confirmed or structure.observed_at is None:
                reasons = ["htf_structure_not_confirmed"]
                output.append(
                    HistoricalSetup(
                        zone=zone,
                        rejection_score=rejection_score,
                        decision=PlanDecision(plan=None, reasons=tuple(reasons)),
                        rejection_observed_at=rejection.observed_at,
                        structure=structure,
                    )
                )
                continue

            retests = retest_episodes_after(
                zone,
                entry_candles,
                after=structure.observed_at,
                max_retests=self.strategy_config.max_executions_per_zone,
                require_rearm=self.strategy_config.require_rearm_between_retests,
            )
            if not retests:
                reasons = ["no_retest_found"]
                output.append(
                    HistoricalSetup(
                        zone=zone,
                        rejection_score=rejection_score,
                        decision=PlanDecision(plan=None, reasons=tuple(reasons)),
                        rejection_observed_at=rejection.observed_at,
                        structure=structure,
                    )
                )
                continue

            for execution_number, retest in enumerate(retests, start=1):
                sizing_reference = stabilized_sizing_reference(
                    zone=zone,
                    structural_reference=rejection.sizing_reference_price,
                    candles=entry_candles,
                    before=retest.timestamp,
                )
                execution_zone = FlipZone(
                    id=zone.id,
                    direction=zone.direction,
                    timeframe=zone.timeframe,
                    lower_price=zone.lower_price,
                    upper_price=zone.upper_price,
                    created_at=zone.created_at,
                    state=SetupState.WAITING_FOR_RETEST,
                    rejection_score=rejection_score,
                    execution_count=execution_number - 1,
                )
                decision = self.planner.build_plan(
                    zone=execution_zone,
                    now=retest.timestamp,
                    structure=structure,
                    rejection_is_healthy=healthy,
                    news=news_gate_at(retest.timestamp),
                    planned_rr=rr,
                    sizing_reference_price=sizing_reference,
                )
                outcome = None
                if decision.plan is not None:
                    outcome = simulate_historical_outcome(
                        zone=execution_zone,
                        candles=entry_candles,
                        activated_at=retest.timestamp,
                        sizing_reference_price=sizing_reference,
                    )

                output.append(
                    HistoricalSetup(
                        zone=execution_zone,
                        rejection_score=rejection_score,
                        decision=decision,
                        execution_number=execution_number,
                        rejection_observed_at=rejection.observed_at,
                        retest_at=retest.timestamp,
                        structure=structure,
                        outcome=outcome,
                    )
                )

        return output

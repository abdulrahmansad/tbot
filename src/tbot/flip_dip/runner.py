from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from .demo import InMemoryDemoTracker
from .models import FlipZone, NewsGate, StructureConfirmation
from .planner import FlipDipPlanner, PlanDecision


@dataclass(frozen=True)
class ForwardTestResult:
    decision: PlanDecision
    plan_id: str | None = None


class ForwardTestRunner:
    """Creates and records hypothetical plans. Never sends orders."""

    def __init__(
        self,
        *,
        planner: FlipDipPlanner,
        tracker: InMemoryDemoTracker,
    ) -> None:
        self.planner = planner
        self.tracker = tracker

    def evaluate_retest(
        self,
        *,
        zone: FlipZone,
        now: datetime,
        structure: StructureConfirmation,
        rejection_is_healthy: bool,
        news: NewsGate,
        planned_rr: float,
    ) -> ForwardTestResult:
        decision = self.planner.build_plan(
            zone=zone,
            now=now,
            structure=structure,
            rejection_is_healthy=rejection_is_healthy,
            news=news,
            planned_rr=planned_rr,
        )

        if decision.plan is None:
            return ForwardTestResult(decision=decision)

        plan_id = f"demo-{uuid4().hex}"
        self.tracker.create(plan_id=plan_id, plan=decision.plan, created_at=now)
        return ForwardTestResult(decision=decision, plan_id=plan_id)

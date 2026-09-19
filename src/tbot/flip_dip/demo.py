from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .models import TradePlan


class DemoEventType(str, Enum):
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_ACTIVATED = "PLAN_ACTIVATED"
    PARTIAL_TP = "PARTIAL_TP"
    COMPLETED = "COMPLETED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class DemoEvent:
    plan_id: str
    event_type: DemoEventType
    timestamp: datetime
    price: float | None = None
    r_multiple: float | None = None
    note: str | None = None


@dataclass
class DemoPlanRecord:
    plan_id: str
    plan: TradePlan
    created_at: datetime
    events: list[DemoEvent]
    session_id: str | None = None
    session_name: str | None = None
    session_start: str | None = None
    session_end: str | None = None

    @property
    def terminal(self) -> bool:
        terminal_events = {
            DemoEventType.COMPLETED,
            DemoEventType.INVALIDATED,
            DemoEventType.EXPIRED,
        }
        return any(event.event_type in terminal_events for event in self.events)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "created_at": self.created_at.isoformat(),
            "plan": asdict(self.plan),
            "session_id": self.session_id,
            "session_name": self.session_name,
            "session_start": self.session_start,
            "session_end": self.session_end,
            "events": [
                {
                    **asdict(event),
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                }
                for event in self.events
            ],
        }


class InMemoryDemoTracker:
    """Persistence-free Phase 0 tracker.

    This intentionally records hypothetical outcomes only. It has no broker
    interface and no order-placement method.
    """

    def __init__(self) -> None:
        self._records: dict[str, DemoPlanRecord] = {}

    def create(
        self,
        *,
        plan_id: str,
        plan: TradePlan,
        created_at: datetime,
        session_id: str | None = None,
        session_name: str | None = None,
        session_start: str | None = None,
        session_end: str | None = None,
    ) -> DemoPlanRecord:
        if plan_id in self._records:
            raise ValueError(f"Duplicate plan_id: {plan_id}")

        event = DemoEvent(
            plan_id=plan_id,
            event_type=DemoEventType.PLAN_CREATED,
            timestamp=created_at,
        )
        record = DemoPlanRecord(
            plan_id=plan_id,
            plan=plan,
            created_at=created_at,
            events=[event],
            session_id=session_id,
            session_name=session_name,
            session_start=session_start,
            session_end=session_end,
        )
        self._records[plan_id] = record
        return record

    def append(self, event: DemoEvent) -> DemoPlanRecord:
        record = self._records[event.plan_id]
        if record.terminal:
            raise ValueError("Cannot append events to a terminal demo plan")
        record.events.append(event)
        return record

    def get(self, plan_id: str) -> DemoPlanRecord:
        return self._records[plan_id]

    def all(self) -> list[DemoPlanRecord]:
        return list(self._records.values())

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .demo import DemoEventType, DemoPlanRecord


@dataclass(frozen=True)
class DemoSummary:
    total_plans: int
    completed: int
    invalidated: int
    expired: int
    open_plans: int
    realized_r_sum: float
    realized_r_average: float | None
    by_execution_number: dict[int, dict[str, float | int]]


def summarize_demo(records: list[DemoPlanRecord]) -> DemoSummary:
    status_counts: Counter[str] = Counter()
    realized_rs: list[float] = []
    buckets: dict[int, dict[str, float | int]] = defaultdict(
        lambda: {
            "plans": 0,
            "completed": 0,
            "invalidated": 0,
            "expired": 0,
            "realized_r_sum": 0.0,
        }
    )

    for record in records:
        bucket = buckets[record.plan.execution_number]
        bucket["plans"] = int(bucket["plans"]) + 1

        terminal = None
        terminal_r = None
        for event in record.events:
            if event.event_type in {
                DemoEventType.COMPLETED,
                DemoEventType.INVALIDATED,
                DemoEventType.EXPIRED,
            }:
                terminal = event.event_type
                terminal_r = event.r_multiple

        if terminal is None:
            status_counts["open"] += 1
            continue

        if terminal is DemoEventType.COMPLETED:
            status_counts["completed"] += 1
            bucket["completed"] = int(bucket["completed"]) + 1
        elif terminal is DemoEventType.INVALIDATED:
            status_counts["invalidated"] += 1
            bucket["invalidated"] = int(bucket["invalidated"]) + 1
        else:
            status_counts["expired"] += 1
            bucket["expired"] = int(bucket["expired"]) + 1

        if terminal_r is not None:
            realized_rs.append(terminal_r)
            bucket["realized_r_sum"] = float(bucket["realized_r_sum"]) + terminal_r

    total_r = sum(realized_rs)
    average = total_r / len(realized_rs) if realized_rs else None

    return DemoSummary(
        total_plans=len(records),
        completed=status_counts["completed"],
        invalidated=status_counts["invalidated"],
        expired=status_counts["expired"],
        open_plans=status_counts["open"],
        realized_r_sum=total_r,
        realized_r_average=average,
        by_execution_number=dict(buckets),
    )

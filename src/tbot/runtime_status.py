from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class WorkerSnapshotHealth:
    status: str
    last_scan_at: str | None
    age_seconds: float | None
    fresh: bool


def evaluate_worker_snapshot(
    snapshot: dict[str, Any],
    *,
    now: datetime | None = None,
    stale_after_seconds: int = 180,
) -> WorkerSnapshotHealth:
    if stale_after_seconds < 1:
        raise ValueError("stale_after_seconds must be positive")

    scanned_at = snapshot.get("scanned_at")
    if not scanned_at:
        return WorkerSnapshotHealth(
            status="missing",
            last_scan_at=None,
            age_seconds=None,
            fresh=False,
        )

    try:
        parsed = datetime.fromisoformat(str(scanned_at).replace("Z", "+00:00"))
    except ValueError:
        return WorkerSnapshotHealth(
            status="invalid_timestamp",
            last_scan_at=str(scanned_at),
            age_seconds=None,
            fresh=False,
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    age = (moment.astimezone(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    if age < -60:
        return WorkerSnapshotHealth(
            status="clock_skew",
            last_scan_at=parsed.isoformat(),
            age_seconds=age,
            fresh=False,
        )

    age = max(age, 0.0)
    fresh = age <= stale_after_seconds
    return WorkerSnapshotHealth(
        status="fresh" if fresh else "stale",
        last_scan_at=parsed.isoformat(),
        age_seconds=round(age, 1),
        fresh=fresh,
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Sequence

from .backtest import HistoricalSetup


@dataclass(frozen=True)
class SetupCluster:
    cluster_id: str
    member_zone_ids: tuple[str, ...]
    primary_zone_id: str


def _timeframe_minutes(value: str) -> int:
    return {"5M": 5, "15M": 15, "1H": 60}[value]


def cluster_ready_setups(setups: Sequence[HistoricalSetup]) -> tuple[SetupCluster, ...]:
    """Group READY setups triggered by the same directional market event.

    We do not delete secondary zones. Clustering is an audit/reporting layer so
    multiple genuinely useful zones remain visible while performance reporting
    can avoid treating one market event as many independent opportunities.
    """
    ready = [
        setup
        for setup in setups
        if setup.decision.plan is not None and setup.retest_at is not None
    ]
    ready.sort(key=lambda s: (s.retest_at, s.zone.direction.value, s.zone.created_at))

    clusters: list[list[HistoricalSetup]] = []
    for setup in ready:
        window = timedelta(minutes=_timeframe_minutes(setup.zone.timeframe.value))
        placed = False
        for cluster in reversed(clusters):
            anchor = cluster[0]
            if setup.retest_at - anchor.retest_at > window:
                break
            if anchor.zone.direction is not setup.zone.direction:
                continue
            if anchor.zone.timeframe is not setup.zone.timeframe:
                continue
            cluster.append(setup)
            placed = True
            break
        if not placed:
            clusters.append([setup])

    output: list[SetupCluster] = []
    for index, members in enumerate(clusters, start=1):
        ranked = sorted(
            members,
            key=lambda s: (
                -s.rejection_score,
                s.zone.upper_price - s.zone.lower_price,
                s.zone.created_at,
            ),
        )
        output.append(
            SetupCluster(
                cluster_id=f"{members[0].zone.timeframe.value.lower()}-{index:04d}",
                member_zone_ids=tuple(member.zone.id for member in ranked),
                primary_zone_id=ranked[0].zone.id,
            )
        )
    return tuple(output)


def cluster_lookup(setups: Sequence[HistoricalSetup]) -> dict[str, tuple[str, int, bool]]:
    lookup: dict[str, tuple[str, int, bool]] = {}
    for cluster in cluster_ready_setups(setups):
        for rank, zone_id in enumerate(cluster.member_zone_ids, start=1):
            lookup[zone_id] = (cluster.cluster_id, rank, zone_id == cluster.primary_zone_id)
    return lookup

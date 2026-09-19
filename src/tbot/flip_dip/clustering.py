from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Sequence

from .backtest import HistoricalSetup


@dataclass(frozen=True)
class SetupCluster:
    cluster_id: str
    member_setup_keys: tuple[str, ...]
    primary_setup_key: str

    @property
    def member_zone_ids(self) -> tuple[str, ...]:
        # Backward-compatible display helper.
        return tuple(key.split(":e", 1)[0] for key in self.member_setup_keys)

    @property
    def primary_zone_id(self) -> str:
        return self.primary_setup_key.split(":e", 1)[0]


def _timeframe_minutes(value: str) -> int:
    return {"5M": 5, "15M": 15, "1H": 60}[value]


def cluster_ready_setups(setups: Sequence[HistoricalSetup]) -> tuple[SetupCluster, ...]:
    """Group READY executions triggered by the same directional market event.

    Executions from the same zone retain distinct setup keys. Clustering is
    only an audit/reporting layer and never deletes valid retest executions.
    """
    ready = [
        setup
        for setup in setups
        if setup.decision.plan is not None and setup.retest_at is not None
    ]
    ready.sort(
        key=lambda s: (
            s.retest_at,
            s.zone.direction.value,
            s.zone.created_at,
            s.effective_execution_number,
        )
    )

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
                s.execution_number,
                s.zone.created_at,
            ),
        )
        output.append(
            SetupCluster(
                cluster_id=f"{members[0].zone.timeframe.value.lower()}-{index:04d}",
                member_setup_keys=tuple(member.setup_key for member in ranked),
                primary_setup_key=ranked[0].setup_key,
            )
        )
    return tuple(output)


def cluster_lookup(
    setups: Sequence[HistoricalSetup],
) -> dict[str, tuple[str, int, bool]]:
    lookup: dict[str, tuple[str, int, bool]] = {}
    for cluster in cluster_ready_setups(setups):
        for rank, setup_key in enumerate(cluster.member_setup_keys, start=1):
            lookup[setup_key] = (
                cluster.cluster_id,
                rank,
                setup_key == cluster.primary_setup_key,
            )
    return lookup

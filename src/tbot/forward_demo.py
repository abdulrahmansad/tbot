from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .data.provider import MarketDataProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.clustering import cluster_ready_setups
from .flip_dip.demo import InMemoryDemoTracker
from .flip_dip.persistence import JsonlDemoStore
from .news import NewsBlackoutEngine
from .news_provider import EconomicCalendarProvider


_TIMEFRAME_MINUTES = {"5M": 5, "15M": 15, "1H": 60}


@dataclass(frozen=True)
class ForwardDemoPollResult:
    scanned_at: datetime
    created_plan_ids: tuple[str, ...]
    ready_primary_count: int
    fresh_primary_count: int
    news_clear: bool
    news_reason: str | None = None


class SeenZoneStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read(self) -> set[str]:
        if not self.path.exists():
            return set()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return set(payload.get("zone_ids", []))

    def write(self, zone_ids: Iterable[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"zone_ids": sorted(set(zone_ids))}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ForwardDemoService:
    """Discover fresh hypothetical plans and persist them once.

    This service has no broker client, order API, or execution method.
    """

    def __init__(
        self,
        *,
        market_data: MarketDataProvider,
        calendar: EconomicCalendarProvider | None = None,
        plans_path: str | Path = "data/runtime/forward-plans.jsonl",
        seen_path: str | Path = "data/runtime/seen-zones.json",
    ) -> None:
        self.market_data = market_data
        self.calendar = calendar
        self.scanner = ProvisionalBacktester()
        self.store = JsonlDemoStore(plans_path)
        self.seen = SeenZoneStore(seen_path)
        config = self.scanner.strategy_config
        self.news_engine = NewsBlackoutEngine(
            before_minutes=config.news_blackout_before_minutes,
            after_minutes=config.news_blackout_after_minutes,
        )

    def poll_once(
        self,
        *,
        entry_timeframes: tuple[str, ...] = ("5M", "15M", "1H"),
        bars: int = 500,
        fresh_bars: int = 2,
        now: datetime | None = None,
    ) -> ForwardDemoPollResult:
        moment = now or datetime.now(timezone.utc)
        if fresh_bars < 1:
            raise ValueError("fresh_bars must be >= 1")

        news_clear = True
        news_reason = None
        if self.calendar is not None:
            events = self.calendar.fetch_events(
                start=moment - timedelta(hours=2),
                end=moment + timedelta(hours=2),
            )
            gate = self.news_engine.evaluate(now=moment, events=events)
            news_clear = gate.clear
            news_reason = gate.reason

        seen = self.seen.read()
        created: list[str] = []
        ready_primary_count = 0
        fresh_primary_count = 0

        for entry_tf in entry_timeframes:
            confirmation = self.scanner.strategy_config.confirmation_timeframe[entry_tf]
            entry = self.market_data.fetch_candles(
                timeframe=entry_tf,
                outputsize=bars,
            )
            htf = self.market_data.fetch_candles(
                timeframe=confirmation,
                outputsize=bars,
            )
            if not entry:
                continue

            setups = self.scanner.scan(
                {entry_tf: entry, confirmation: htf},
                entry_timeframe=entry_tf,
                planned_rr=5.0,
            )
            by_zone = {setup.zone.id: setup for setup in setups}
            clusters = cluster_ready_setups(setups)
            ready_primary_count += len(clusters)

            freshness = timedelta(
                minutes=_TIMEFRAME_MINUTES[entry_tf] * fresh_bars
            )
            newest_candle_at = entry[-1].timestamp

            for cluster in clusters:
                setup = by_zone[cluster.primary_zone_id]
                if setup.retest_at is None:
                    continue
                if newest_candle_at - setup.retest_at > freshness:
                    continue

                fresh_primary_count += 1
                if not news_clear or setup.zone.id in seen:
                    continue

                plan = setup.decision.plan
                if plan is None:
                    continue

                plan_id = f"demo-{setup.zone.id}"
                tracker = InMemoryDemoTracker()
                record = tracker.create(
                    plan_id=plan_id,
                    plan=plan,
                    created_at=setup.retest_at,
                )
                self.store.append_record(record)
                seen.add(setup.zone.id)
                created.append(plan_id)

        self.seen.write(seen)

        return ForwardDemoPollResult(
            scanned_at=moment,
            created_plan_ids=tuple(created),
            ready_primary_count=ready_primary_count,
            fresh_primary_count=fresh_primary_count,
            news_clear=news_clear,
            news_reason=news_reason,
        )

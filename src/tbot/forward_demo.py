from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .data.provider import MarketDataProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.config import FlipDipConfig
from .flip_dip.clustering import cluster_ready_setups
from .flip_dip.demo import InMemoryDemoTracker
from .flip_dip.persistence import JsonlDemoStore
from .flip_dip.time_rules import is_within_trading_window
from .live_snapshot import LiveSnapshotStore
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
    """Persistent execution-level de-duplication.

    Legacy zone_ids are read only for compatibility. New writes use
    setup_keys so retest #2/#3 remain eligible after retest #1.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read(self) -> set[str]:
        if not self.path.exists():
            return set()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return set(payload.get("setup_keys", []))

    def write(self, setup_keys: Iterable[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"setup_keys": sorted(set(setup_keys))}
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
        snapshot_path: str | Path = "data/runtime/live-snapshot.json",
        strategy_config: FlipDipConfig | None = None,
    ) -> None:
        self.market_data = market_data
        self.calendar = calendar
        self.scanner = ProvisionalBacktester(strategy_config=strategy_config)
        self.store = JsonlDemoStore(plans_path)
        self.seen = SeenZoneStore(seen_path)
        self.snapshot = LiveSnapshotStore(snapshot_path)
        config = self.scanner.strategy_config
        self.news_engine = NewsBlackoutEngine(
            before_minutes=config.news_blackout_before_minutes,
            after_minutes=config.news_blackout_after_minutes,
        )

    def poll_once(
        self,
        *,
        entry_timeframes: tuple[str, ...] | None = None,
        bars: int = 500,
        fresh_bars: int = 2,
        now: datetime | None = None,
    ) -> ForwardDemoPollResult:
        moment = now or datetime.now(timezone.utc)
        if entry_timeframes is None:
            entry_timeframes = self.scanner.strategy_config.enabled_entry_timeframes
        if fresh_bars < 1:
            raise ValueError("fresh_bars must be >= 1")

        news_clear = True
        news_reason = None
        events = []
        config = self.scanner.strategy_config
        trading_window_open = is_within_trading_window(
            moment,
            timezone=config.timezone,
            start=config.trading_start,
            end=config.trading_end,
        )
        if self.calendar is not None:
            events = self.calendar.fetch_events(
                start=moment - timedelta(hours=3),
                end=moment + timedelta(hours=2),
            )
            gate = self.news_engine.evaluate(now=moment, events=events)
            news_clear = gate.clear
            news_reason = gate.reason

        upcoming_events = sorted(
            (
                event
                for event in events
                if event.scheduled_at >= moment
                and event.impact.value == "HIGH"
                and event.currency.upper() == "USD"
                and event.xauusd_relevant
            ),
            key=lambda event: event.scheduled_at,
        )
        next_event = upcoming_events[0] if upcoming_events else None

        seen = self.seen.read()
        created: list[str] = []
        ready_primary_count = 0
        fresh_primary_count = 0
        timeframe_snapshots: dict[str, dict] = {}

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
                timeframe_snapshots[entry_tf] = {
                    "status": "no_data",
                    "entry_timeframe": entry_tf,
                    "confirmation_timeframe": confirmation,
                    "execution_enabled": False,
                }
                continue

            setups = self.scanner.scan(
                {entry_tf: entry, confirmation: htf},
                entry_timeframe=entry_tf,
                planned_rr=5.0,
            )
            by_key = {setup.setup_key: setup for setup in setups}
            clusters = cluster_ready_setups(setups)
            ready_primary_count += len(clusters)

            freshness = timedelta(
                minutes=_TIMEFRAME_MINUTES[entry_tf] * fresh_bars
            )
            newest_candle_at = entry[-1].timestamp
            freshness_reference = max(newest_candle_at, moment)

            latest_primary = None
            if clusters:
                primary_setups = [
                    by_key[cluster.primary_setup_key]
                    for cluster in clusters
                    if cluster.primary_setup_key in by_key
                ]
                primary_setups = [
                    setup
                    for setup in primary_setups
                    if setup.retest_at is not None
                    and freshness_reference - setup.retest_at <= freshness
                ]
                if primary_setups:
                    latest_primary = max(
                        primary_setups,
                        key=lambda setup: setup.retest_at,
                    )

            latest_payload = None
            if latest_primary is not None and latest_primary.decision.plan is not None:
                plan = latest_primary.decision.plan
                latest_payload = {
                    "zone_id": latest_primary.zone.id,
                    "setup_key": latest_primary.setup_key,
                    "execution_number": latest_primary.effective_execution_number,
                    "direction": latest_primary.zone.direction.value,
                    "entry_timeframe": latest_primary.zone.timeframe.value,
                    "confirmation_timeframe": plan.confirmation_timeframe,
                    "zone_lower": latest_primary.zone.lower_price,
                    "zone_upper": latest_primary.zone.upper_price,
                    "rejection_score": round(latest_primary.rejection_score, 4),
                    "retest_at": latest_primary.retest_at.isoformat(),
                    "structure_kind": (
                        latest_primary.structure.kind
                        if latest_primary.structure is not None
                        else None
                    ),
                    "structure_observed_at": (
                        latest_primary.structure.observed_at.isoformat()
                        if latest_primary.structure is not None
                        and latest_primary.structure.observed_at is not None
                        else None
                    ),
                    "minimum_rr": plan.minimum_rr,
                    "risk_percent": plan.risk_percent,
                    "entry_reference_price": plan.entry_reference_price,
                    "sizing_reference_price": plan.sizing_reference_price,
                    "target_5r_price": plan.target_5r_price,
                    "partial_tp_configured": plan.partial_tp_configured,
                    "plan_notes": list(plan.notes),
                    "invalidation_rule": plan.invalidation_rule,
                }

            skip_reasons = Counter(
                reason
                for setup in setups
                if setup.decision.plan is None
                for reason in setup.decision.reasons
            )
            ready_execution_counts = Counter(
                setup.effective_execution_number
                for setup in setups
                if setup.decision.plan is not None
            )

            timeframe_snapshots[entry_tf] = {
                "status": "ok",
                "entry_timeframe": entry_tf,
                "confirmation_timeframe": confirmation,
                "latest_candle_at": entry[-1].timestamp.isoformat(),
                "latest_close": entry[-1].close,
                "candidate_count": len(setups),
                "skip_reason_counts": dict(skip_reasons),
                "ready_execution_counts": {
                    str(key): value
                    for key, value in sorted(ready_execution_counts.items())
                },
                "ready_primary_count": len(clusters),
                "fresh_primary_count": sum(
                    1
                    for cluster in clusters
                    if cluster.primary_setup_key in by_key
                    and by_key[cluster.primary_setup_key].retest_at is not None
                    and freshness_reference
                    - by_key[cluster.primary_setup_key].retest_at
                    <= freshness
                ),
                "latest_ready_plan": latest_payload,
                "execution_enabled": False,
            }

            for cluster in clusters:
                setup = by_key[cluster.primary_setup_key]
                if setup.retest_at is None:
                    continue
                if freshness_reference - setup.retest_at > freshness:
                    continue

                fresh_primary_count += 1

                setup_news_clear = True
                if self.calendar is not None:
                    setup_gate = self.news_engine.evaluate(
                        now=setup.retest_at,
                        events=events,
                    )
                    setup_news_clear = setup_gate.clear

                if not setup_news_clear or setup.setup_key in seen:
                    continue

                plan = setup.decision.plan
                if plan is None:
                    continue

                plan_id = f"demo-{setup.zone.id}-e{setup.effective_execution_number}"
                tracker = InMemoryDemoTracker()
                record = tracker.create(
                    plan_id=plan_id,
                    plan=plan,
                    created_at=setup.retest_at,
                )
                self.store.append_record(record)
                seen.add(setup.setup_key)
                created.append(plan_id)

        self.seen.write(seen)

        news_provider_name = None
        news_provider_failures = []
        calendar = self.calendar
        if calendar is not None:
            upstream = getattr(calendar, "upstream", None)
            news_provider_name = getattr(upstream, "last_provider_name", None)
            news_provider_failures = list(
                getattr(upstream, "last_failures", []) or []
            )
            if news_provider_name is None:
                news_provider_name = type(upstream or calendar).__name__

        self.snapshot.write(
            {
                "scanned_at": moment.isoformat(),
                "strategy_contract_version": config.strategy_contract_version,
                "active_entry_timeframes": list(entry_timeframes),
                "primary_entry_timeframes": list(config.primary_entry_timeframes),
                "secondary_entry_timeframes": ["1H"],
                "trading_window_open": trading_window_open,
                "trading_window_timezone": config.timezone,
                "trading_window_start": config.trading_start.strftime("%H:%M"),
                "trading_window_end": config.trading_end.strftime("%H:%M"),
                "news_clear": news_clear,
                "news_reason": news_reason,
                "next_high_impact_event": (
                    {
                        "title": next_event.title,
                        "scheduled_at": next_event.scheduled_at.isoformat(),
                        "currency": next_event.currency,
                    }
                    if next_event is not None
                    else None
                ),
                "news_provider_connected": self.calendar is not None,
                "news_provider_name": news_provider_name,
                "news_provider_failures": news_provider_failures,
                "execution_enabled": False,
                "timeframes": timeframe_snapshots,
            }
        )

        return ForwardDemoPollResult(
            scanned_at=moment,
            created_plan_ids=tuple(created),
            ready_primary_count=ready_primary_count,
            fresh_primary_count=fresh_primary_count,
            news_clear=news_clear,
            news_reason=news_reason,
        )

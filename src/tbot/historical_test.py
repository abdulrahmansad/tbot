from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .account_simulator import simulate_account
from .data.provider import MarketDataProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.clustering import cluster_ready_setups
from .flip_dip.config import FlipDipConfig
from .flip_dip.models import NewsGate
from .news import NewsBlackoutEngine
from .news_provider import EconomicCalendarProvider


@dataclass(frozen=True)
class HistoricalTestRequest:
    start: datetime
    end: datetime
    starting_balance: float = 100.0
    risk_percent: float = 5.0
    include_1h: bool = False


class HistoricalTestService:
    """On-demand historical strategy replay for local Phase 0 review."""

    def __init__(
        self,
        *,
        market_data: MarketDataProvider,
        calendar: EconomicCalendarProvider | None,
    ) -> None:
        self.market_data = market_data
        self.calendar = calendar

    def run(self, request: HistoricalTestRequest) -> dict[str, Any]:
        if request.start.tzinfo is None or request.end.tzinfo is None:
            raise ValueError("start/end must be timezone-aware")
        if request.end <= request.start:
            raise ValueError("end must be after start")
        if request.starting_balance <= 0:
            raise ValueError("starting_balance must be positive")
        if not 0 < request.risk_percent <= 5:
            raise ValueError("risk_percent must be > 0 and <= 5")

        # Twelve Data's Phase 0 adapter caps a single response at 5,000 bars.
        # With 5M included, keep interactive tests inside a conservative 14-day
        # window rather than silently truncating history.
        duration = request.end - request.start
        if duration > timedelta(days=14):
            raise ValueError(
                "Interactive Phase 0 tests are limited to 14 days when 5M is included. "
                "Choose a shorter range so the result is not silently truncated."
            )

        config = FlipDipConfig(enable_1h_entries=request.include_1h)
        scanner = ProvisionalBacktester(strategy_config=config)
        engine = NewsBlackoutEngine(
            before_minutes=config.news_blackout_before_minutes,
            after_minutes=config.news_blackout_after_minutes,
        )

        events = []
        news_filter_applied = False
        if self.calendar is not None:
            events = self.calendar.fetch_events(
                start=request.start - timedelta(hours=3),
                end=request.end + timedelta(hours=3),
            )
            news_filter_applied = True

        def news_gate_at(moment: datetime) -> NewsGate:
            if not news_filter_applied:
                return NewsGate(clear=False, reason="historical_news_provider_unavailable")
            return engine.evaluate(now=moment, events=events)

        all_setups = []
        timeframe_results: dict[str, Any] = {}

        for entry_tf in config.enabled_entry_timeframes:
            confirmation_tf = config.confirmation_timeframe[entry_tf]
            entry = self.market_data.fetch_candles(
                timeframe=entry_tf,
                outputsize=5000,
                start=request.start,
                end=request.end,
            )
            htf = self.market_data.fetch_candles(
                timeframe=confirmation_tf,
                outputsize=5000,
                start=request.start,
                end=request.end,
            )
            setups = scanner.scan(
                {entry_tf: entry, confirmation_tf: htf},
                entry_timeframe=entry_tf,
                planned_rr=config.minimum_rr,
                news_gate_at=news_gate_at,
            )
            all_setups.extend(setups)

            clusters = cluster_ready_setups(setups)
            by_key = {setup.setup_key: setup for setup in setups}
            primary = [
                by_key[cluster.primary_setup_key]
                for cluster in clusters
                if cluster.primary_setup_key in by_key
            ]
            outcomes = Counter(
                setup.outcome.status.value
                for setup in primary
                if setup.outcome is not None
            )
            execution_counts = Counter(
                setup.effective_execution_number
                for setup in setups
                if setup.decision.plan is not None
            )
            skip_reasons = Counter(
                reason
                for setup in setups
                if setup.decision.plan is None
                for reason in setup.decision.reasons
            )

            timeframe_results[entry_tf] = {
                "confirmation_timeframe": confirmation_tf,
                "entry_candles": len(entry),
                "confirmation_candles": len(htf),
                "candidate_count": len(setups),
                "ready_executions": sum(execution_counts.values()),
                "independent_events": len(primary),
                "execution_counts": {
                    str(k): v for k, v in sorted(execution_counts.items())
                },
                "outcomes": dict(outcomes),
                "skip_reasons": dict(skip_reasons),
            }

        clusters = cluster_ready_setups(all_setups)
        by_key = {setup.setup_key: setup for setup in all_setups}
        primary = [
            by_key[cluster.primary_setup_key]
            for cluster in clusters
            if cluster.primary_setup_key in by_key
        ]
        primary.sort(key=lambda setup: setup.retest_at or setup.zone.created_at)

        sim_events = [
            {
                "outcome_status": setup.outcome.status.value,
                "outcome_resolved_at": (
                    setup.outcome.resolved_at.isoformat()
                    if setup.outcome and setup.outcome.resolved_at is not None
                    else None
                ),
                "retest_at": setup.retest_at.isoformat() if setup.retest_at else None,
            }
            for setup in primary
            if setup.outcome is not None
        ]
        simulation = simulate_account(
            sim_events,
            starting_balance=request.starting_balance,
            risk_percent=request.risk_percent,
        )

        outcomes = Counter(event["outcome_status"] for event in sim_events)
        return {
            "status": "ok",
            "strategy_contract_version": config.strategy_contract_version,
            "start": request.start.isoformat(),
            "end": request.end.isoformat(),
            "starting_balance": request.starting_balance,
            "risk_percent": request.risk_percent,
            "include_1h": request.include_1h,
            "news_filter_applied": news_filter_applied,
            "historical_news_events_loaded": len(events),
            "timeframes": timeframe_results,
            "independent_events": len(primary),
            "outcomes": dict(outcomes),
            "account_scenario": {
                "ending_balance": simulation.ending_balance,
                "net_profit": simulation.net_profit,
                "return_percent": simulation.return_percent,
                "max_drawdown_percent": simulation.max_drawdown_percent,
                "highest_balance": simulation.highest_balance,
                "lowest_balance": simulation.lowest_balance,
                "event_count": simulation.event_count,
                "equity_curve": [
                    {
                        "index": point.index,
                        "event_time": point.event_time,
                        "outcome_status": point.outcome_status,
                        "r_multiple": point.r_multiple,
                        "balance_after": point.balance_after,
                    }
                    for point in simulation.points
                ],
                "note": (
                    "Milestone payout scenario only until the owner supplies the "
                    "exact partial take-profit ladder."
                ),
            },
            "setups": [
                {
                    "setup_key": setup.setup_key,
                    "direction": setup.zone.direction.value,
                    "entry_timeframe": setup.zone.timeframe.value,
                    "execution_number": setup.effective_execution_number,
                    "retest_at": setup.retest_at.isoformat() if setup.retest_at else None,
                    "zone_lower": setup.zone.lower_price,
                    "zone_upper": setup.zone.upper_price,
                    "outcome_status": setup.outcome.status.value if setup.outcome else None,
                    "terminal": setup.outcome.terminal if setup.outcome else None,
                    "max_favorable_r": (
                        round(setup.outcome.max_favorable_r, 4)
                        if setup.outcome else None
                    ),
                    "max_adverse_r": (
                        round(setup.outcome.max_adverse_r, 4)
                        if setup.outcome else None
                    ),
                }
                for setup in primary
            ],
        }

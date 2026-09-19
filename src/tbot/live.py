from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .data.provider import MarketDataProvider
from .flip_dip.backtest import ProvisionalBacktester
from .flip_dip.config import FlipDipConfig
from .news import NewsBlackoutEngine
from .news_provider import EconomicCalendarProvider


@dataclass(frozen=True)
class LiveScanResult:
    scanned_at: datetime
    entry_timeframe: str
    confirmation_timeframe: str
    candidate_count: int
    ready_count: int


class LivePlanningService:
    """Polls market data and produces plans only. Never places broker orders."""

    def __init__(
        self,
        *,
        market_data: MarketDataProvider,
        calendar: EconomicCalendarProvider | None = None,
        strategy_config: FlipDipConfig | None = None,
    ) -> None:
        self.market_data = market_data
        self.calendar = calendar
        self.strategy_config = strategy_config or FlipDipConfig()
        self.backtester = ProvisionalBacktester(strategy_config=self.strategy_config)
        self.news_engine = NewsBlackoutEngine(
            before_minutes=self.strategy_config.news_blackout_before_minutes,
            after_minutes=self.strategy_config.news_blackout_after_minutes,
        )

    def scan_once(
        self,
        *,
        entry_timeframe: str = "5M",
        bars: int = 500,
        planned_rr: float = 5.0,
        now: datetime | None = None,
    ) -> LiveScanResult:
        moment = now or datetime.now(timezone.utc)
        if entry_timeframe not in self.strategy_config.enabled_entry_timeframes:
            raise ValueError(
                f"{entry_timeframe} entry is not enabled by the current strategy config"
            )
        confirmation = self.strategy_config.confirmation_timeframe[entry_timeframe]

        entry = self.market_data.fetch_candles(
            timeframe=entry_timeframe,
            outputsize=bars,
        )
        htf = self.market_data.fetch_candles(
            timeframe=confirmation,
            outputsize=bars,
        )

        events = []
        if self.calendar is not None:
            events = self.calendar.fetch_events(
                start=(entry[0].timestamp if entry else moment) - timedelta(hours=3),
                end=moment + timedelta(hours=2),
            )

        def news_gate_at(retest_at):
            if self.calendar is None:
                from .flip_dip.models import NewsGate
                return NewsGate(clear=True)
            return self.news_engine.evaluate(now=retest_at, events=events)

        setups = self.backtester.scan(
            {
                entry_timeframe: entry,
                confirmation: htf,
            },
            entry_timeframe=entry_timeframe,
            planned_rr=planned_rr,
            news_gate_at=news_gate_at,
        )
        ready = sum(1 for setup in setups if setup.decision.plan is not None)

        return LiveScanResult(
            scanned_at=moment,
            entry_timeframe=entry_timeframe,
            confirmation_timeframe=confirmation,
            candidate_count=len(setups),
            ready_count=ready,
        )

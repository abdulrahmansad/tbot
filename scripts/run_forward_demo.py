from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from tbot.data.cached import TimeframeCachedMarketDataProvider
from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.fallback_calendar import FallbackEconomicCalendarProvider
from tbot.finance_calendar import FinanceCalendarProvider
from tbot.fmp_calendar import FmpEconomicCalendarProvider
from tbot.forward_demo import ForwardDemoService
from tbot.news_cache import CachedEconomicCalendarProvider
from tbot.forward_tracking import ForwardOutcomeTracker


def run_cycle(discovery: ForwardDemoService, tracker: ForwardOutcomeTracker) -> None:
    result = discovery.poll_once(now=datetime.now(timezone.utc))
    outcomes = tracker.update()
    print(
        f"scan={result.scanned_at.isoformat()} "
        f"fresh={result.fresh_primary_count} "
        f"created={len(result.created_plan_ids)} "
        f"tracked={len(outcomes)} "
        f"news_clear={result.news_clear}"
    )
    if result.news_reason:
        print(f"  news_reason={result.news_reason}")
    for plan_id in result.created_plan_ids:
        print(f"  created {plan_id}")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Run TBOT forward-demo monitoring. No broker execution."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one discovery/tracking cycle and exit.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between cycles in continuous mode (minimum 60).",
    )
    parser.add_argument(
        "--allow-no-news",
        action="store_true",
        help=(
            "Development only: allow monitoring without FMP news protection. "
            "Do not use for the validation demo week."
        ),
    )
    args = parser.parse_args()
    if args.interval < 60:
        parser.error("--interval must be at least 60 seconds")

    raw_provider = TwelveDataXauUsdProvider()
    provider = TimeframeCachedMarketDataProvider(raw_provider)

    calendar = None
    providers = []
    if os.getenv("FMP_API_KEY"):
        providers.append(FmpEconomicCalendarProvider())
    providers.append(FinanceCalendarProvider())

    if providers:
        calendar = CachedEconomicCalendarProvider(
            FallbackEconomicCalendarProvider(providers),
            ttl_minutes=10,
            padding_minutes=60,
        )
    elif not args.allow_no_news:
        parser.error(
            "No economic-calendar provider is available. "
            "Use --allow-no-news only for development/testing."
        )

    discovery = ForwardDemoService(market_data=provider, calendar=calendar)
    tracker = ForwardOutcomeTracker(market_data=provider)

    if args.once:
        run_cycle(discovery, tracker)
        return

    while True:
        try:
            run_cycle(discovery, tracker)
        except Exception as exc:
            print(f"cycle_error={type(exc).__name__}: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

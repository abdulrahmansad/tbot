from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone

from tbot.data.cached import TimeframeCachedMarketDataProvider
from tbot.data.twelve_data import TwelveDataXauUsdProvider
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
    if os.getenv("FMP_API_KEY"):
        calendar = CachedEconomicCalendarProvider(
            FmpEconomicCalendarProvider(),
            ttl_minutes=15,
            padding_minutes=60,
        )
    elif not args.allow_no_news:
        parser.error(
            "FMP_API_KEY is required for the forward-demo validation period. "
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

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.forward_demo import ForwardDemoService
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
        help="Seconds between cycles in continuous mode (minimum 30).",
    )
    args = parser.parse_args()
    if args.interval < 30:
        parser.error("--interval must be at least 30 seconds")

    provider = TwelveDataXauUsdProvider()
    discovery = ForwardDemoService(market_data=provider)
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

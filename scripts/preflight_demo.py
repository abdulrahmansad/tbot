from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from tbot.calibration_status import evaluate_calibration_readiness
from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.fallback_calendar import FallbackEconomicCalendarProvider
from tbot.finance_calendar import FinanceCalendarProvider
from tbot.fmp_calendar import FmpEconomicCalendarProvider
from tbot.xoomar_calendar import XoomarEconomicCalendarProvider


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Validate TBOT forward-demo prerequisites."
    )
    parser.add_argument(
        "--hosted",
        action="store_true",
        help="Also require private dashboard credentials for hosted demo.",
    )
    parser.add_argument(
        "--summary",
        default="data/runtime/calibration/summary.json",
        help="Calibration summary path.",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip live provider smoke tests.",
    )
    args = parser.parse_args()

    checks: dict[str, dict[str, object]] = {}

    twelve_configured = bool(os.getenv("TWELVE_DATA_API_KEY"))
    twelve_ok = twelve_configured
    twelve_reason = None if twelve_configured else "TWELVE_DATA_API_KEY missing"
    twelve_smoke_candles = 0
    if twelve_configured and not args.skip_network:
        try:
            candles = TwelveDataXauUsdProvider().fetch_candles(
                timeframe="5M",
                outputsize=5,
            )
            twelve_smoke_candles = len(candles)
            twelve_ok = bool(candles)
            if not twelve_ok:
                twelve_reason = "Twelve Data returned no candles"
        except Exception as exc:
            twelve_ok = False
            twelve_reason = f"{type(exc).__name__}: {exc}"
    checks["twelve_data"] = {
        "ok": twelve_ok,
        "configured": twelve_configured,
        "smoke_tested": not args.skip_network and twelve_configured,
        "smoke_candles": twelve_smoke_candles,
        "reason": twelve_reason,
    }

    fmp_configured = bool(os.getenv("FMP_API_KEY"))
    calendar_providers = [
        XoomarEconomicCalendarProvider(),
        FinanceCalendarProvider(),
    ]
    if fmp_configured:
        calendar_providers.append(FmpEconomicCalendarProvider())
    calendar_chain = FallbackEconomicCalendarProvider(calendar_providers)
    news_ok = True
    news_reason = None
    active_news_provider = None
    news_failures = []
    event_count = None
    if not args.skip_network:
        try:
            now = datetime.now(timezone.utc)
            events = calendar_chain.fetch_events(
                start=now - timedelta(hours=3),
                end=now + timedelta(hours=24),
            )
            event_count = len(events)
            active_news_provider = calendar_chain.last_provider_name
            news_failures = list(calendar_chain.last_failures)
        except Exception as exc:
            news_ok = False
            news_reason = f"{type(exc).__name__}: {exc}"
            news_failures = list(calendar_chain.last_failures)
    checks["news_calendar"] = {
        "ok": news_ok,
        "fmp_configured": fmp_configured,
        "smoke_tested": not args.skip_network,
        "active_provider": active_news_provider,
        "provider_failures": news_failures,
        "events_in_smoke_window": event_count,
        "reason": news_reason,
    }

    username = bool(os.getenv("TBOT_DASHBOARD_USERNAME"))
    password = bool(os.getenv("TBOT_DASHBOARD_PASSWORD"))
    auth_pair_valid = username == password
    auth_enabled = username and password
    auth_ok = auth_pair_valid and (auth_enabled if args.hosted else True)
    if not auth_pair_valid:
        auth_reason = "dashboard username/password must be set together"
    elif args.hosted and not auth_enabled:
        auth_reason = "hosted private demo requires dashboard credentials"
    else:
        auth_reason = None
    checks["private_dashboard_auth"] = {
        "ok": auth_ok,
        "enabled": auth_enabled,
        "reason": auth_reason,
    }

    readiness = evaluate_calibration_readiness(Path(args.summary))
    checks["historical_calibration"] = {
        "ok": readiness.ready_for_forward_demo,
        "reasons": list(readiness.reasons),
        "bars_requested": readiness.bars_requested,
        "primary_events": readiness.primary_events,
        "ambiguous_primary_events": readiness.ambiguous_primary_events,
        "risk_model": readiness.risk_model,
    }

    ready = all(bool(item.get("ok")) for item in checks.values())
    result = {
        "ready": ready,
        "mode": "hosted_private_demo" if args.hosted else "local_forward_demo",
        "execution_enabled": False,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

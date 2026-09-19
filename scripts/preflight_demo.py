from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tbot.calibration_status import evaluate_calibration_readiness


def main() -> None:
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
    args = parser.parse_args()

    checks: dict[str, dict[str, object]] = {}

    twelve_ok = bool(os.getenv("TWELVE_DATA_API_KEY"))
    checks["twelve_data"] = {
        "ok": twelve_ok,
        "reason": None if twelve_ok else "TWELVE_DATA_API_KEY missing",
    }

    fmp_ok = bool(os.getenv("FMP_API_KEY"))
    checks["news_calendar"] = {
        "ok": fmp_ok,
        "reason": None if fmp_ok else "FMP_API_KEY missing",
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

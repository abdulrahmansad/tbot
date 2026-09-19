from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from urllib.request import urlopen


ENDPOINTS = (
    ("/api/health", "health"),
    ("/api/calibration/status", "calibration"),
    ("/api/live?entry_timeframe=5M&bars=500", "live_5m"),
    ("/api/live?entry_timeframe=15M&bars=500", "live_15m"),
    ("/api/plans", "plans"),
    ("/api/performance", "performance"),
    ("/api/history?limit=10&primary_only=true", "history"),
)


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test a running local TBOT dashboard and worker."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Running TBOT web base URL.",
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    payloads: dict[str, dict] = {}
    failures: list[str] = []

    for path, name in ENDPOINTS:
        try:
            payloads[name] = get_json(base + path)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            failures.append(f"{name}: {type(exc).__name__}: {exc}")

    health = payloads.get("health", {})
    worker = health.get("worker") or {}
    calibration = payloads.get("calibration", {})

    checks = {
        "web_reachable": not any(
            failure.startswith("health:") for failure in failures
        ),
        "execution_disabled": health.get("execution_enabled") is False,
        "strategy_version": health.get("strategy_version") == "flip-dip-v1-candidate",
        "worker_fresh": worker.get("fresh") is True,
        "news_provider_connected": worker.get("news_provider_connected") is True,
        "news_provider_named": bool(worker.get("news_provider_name")),
        "calibration_ready": calibration.get("ready_for_forward_demo") is True,
    }

    timeframe_minutes = {"5M": 5, "15M": 15}
    for tf, key in (("5M", "live_5m"), ("15M", "live_15m")):
        payload = payloads.get(key, {})
        checks[f"live_{tf.lower()}_ok"] = payload.get("status") == "ok"
        checks[f"live_{tf.lower()}_execution_disabled"] = (
            payload.get("execution_enabled") is False
        )

        plan = payload.get("latest_ready_plan")
        if plan is None:
            checks[f"live_{tf.lower()}_plan_fresh_or_absent"] = True
        else:
            retest_at = plan.get("retest_at")
            try:
                parsed = datetime.fromisoformat(
                    str(retest_at).replace("Z", "+00:00")
                )
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                age_minutes = (
                    datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
                ).total_seconds() / 60.0
                checks[f"live_{tf.lower()}_plan_fresh_or_absent"] = (
                    age_minutes <= timeframe_minutes[tf] * 2 + 1
                )
            except Exception:
                checks[f"live_{tf.lower()}_plan_fresh_or_absent"] = False

    ready = not failures and all(checks.values())

    result = {
        "ready": ready,
        "base_url": base,
        "checks": checks,
        "worker": {
            "status": worker.get("status"),
            "age_seconds": worker.get("age_seconds"),
            "news_provider_name": worker.get("news_provider_name"),
            "news_provider_failures": worker.get("news_provider_failures", []),
        },
        "live": {
            "5M": {
                "status": payloads.get("live_5m", {}).get("status"),
                "fresh_primary_count": payloads.get("live_5m", {}).get("fresh_primary_count"),
                "latest_ready_plan": payloads.get("live_5m", {}).get("latest_ready_plan"),
            },
            "15M": {
                "status": payloads.get("live_15m", {}).get("status"),
                "fresh_primary_count": payloads.get("live_15m", {}).get("fresh_primary_count"),
                "latest_ready_plan": payloads.get("live_15m", {}).get("latest_ready_plan"),
            },
        },
        "failures": failures,
    }

    print(json.dumps(result, indent=2, default=str))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

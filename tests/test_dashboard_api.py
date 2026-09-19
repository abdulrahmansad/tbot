import csv

from tbot.api import create_app


def endpoint(app, path):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")


def test_health_is_read_only():
    app = create_app(calibration_dir="does-not-exist")
    result = endpoint(app, "/api/health")()

    assert result["status"] == "ok"
    assert result["execution_enabled"] is False
    assert result["strategy_version"] == "flip-dip-v1-authoritative"


def test_performance_reads_calibration_rows(tmp_path):
    path = tmp_path / "review-5m.csv"
    fieldnames = [
        "zone_id",
        "status",
        "cluster_primary",
        "outcome_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "zone_id": "z1",
                "status": "PLAN_READY",
                "cluster_primary": "True",
                "outcome_status": "TARGET_5R",
            }
        )
        writer.writerow(
            {
                "zone_id": "z2",
                "status": "PLAN_READY",
                "cluster_primary": "False",
                "outcome_status": "TARGET_2R",
            }
        )
        writer.writerow(
            {
                "zone_id": "z3",
                "status": "SKIP",
                "cluster_primary": "",
                "outcome_status": "",
            }
        )

    app = create_app(calibration_dir=tmp_path)
    result = endpoint(app, "/api/performance")()

    assert result["candidate_count"] == 3
    assert result["ready_zone_count"] == 2
    assert result["independent_event_count"] == 1
    assert result["secondary_zone_count"] == 1
    assert result["outcomes_primary_events"] == {"TARGET_5R": 1}


def test_live_reports_worker_snapshot_unavailable_without_market_provider(tmp_path):
    app = create_app(
        calibration_dir=tmp_path,
        live_snapshot_path=tmp_path / "live.json",
    )
    result = endpoint(app, "/api/live")(entry_timeframe="5M", bars=500)

    assert result["status"] == "worker_snapshot_unavailable"
    assert result["execution_enabled"] is False
    assert result["source"] == "worker_snapshot"


def test_live_reads_worker_snapshot(tmp_path):
    snapshot = tmp_path / "live.json"
    snapshot.write_text(
        """{
          "scanned_at": "2026-09-19T10:00:00+00:00",
          "news_clear": true,
          "news_reason": null,
          "news_provider_connected": true,
          "execution_enabled": false,
          "timeframes": {
            "5M": {
              "status": "ok",
              "entry_timeframe": "5M",
              "confirmation_timeframe": "15M",
              "latest_candle_at": "2026-09-19T09:55:00+00:00",
              "candidate_count": 12,
              "ready_primary_count": 2,
              "latest_ready_plan": null,
              "execution_enabled": false
            }
          }
        }""",
        encoding="utf-8",
    )
    app = create_app(
        calibration_dir=tmp_path,
        live_snapshot_path=snapshot,
    )

    result = endpoint(app, "/api/live")(entry_timeframe="5M", bars=500)

    assert result["status"] == "ok"
    assert result["source"] == "worker_snapshot"
    assert result["ready_primary_count"] == 2
    assert result["news_provider_connected"] is True


def test_dashboard_root_contains_user_tabs(tmp_path):
    app = create_app(calibration_dir=tmp_path)
    html = endpoint(app, "/")()

    assert "Live" in html
    assert "Plans" in html
    assert "Performance" in html
    assert "History" in html
    assert "execution disabled" in html.lower()


def test_calibration_status_missing_summary_is_not_ready(tmp_path):
    app = create_app(calibration_dir=tmp_path)
    result = endpoint(app, "/api/calibration/status")()

    assert result["ready_for_forward_demo"] is False
    assert "calibration_summary_missing" in result["reasons"]
    assert result["does_not_claim_profitability"] is True


def test_performance_exposes_hypothetical_account_simulation(tmp_path):
    csv_path = tmp_path / "review-5m.csv"
    csv_path.write_text(
        "status,cluster_primary,outcome_status,retest_at,created_at\n"
        "PLAN_READY,true,TARGET_5R,2026-01-01T00:00:00+00:00,2025-12-31T00:00:00+00:00\n"
        "PLAN_READY,true,INVALIDATED,2026-01-02T00:00:00+00:00,2026-01-01T00:00:00+00:00\n",
        encoding="utf-8",
    )
    app = create_app(calibration_dir=tmp_path)
    result = endpoint(app, "/api/performance")(
        starting_balance=100.0,
        risk_percent=5.0,
    )

    sim = result["account_simulation"]
    assert sim["starting_balance"] == 100.0
    assert sim["ending_balance"] == 118.75
    assert sim["event_count"] == 2
    assert sim["assumptions"]["INVALIDATED"] == -1.0

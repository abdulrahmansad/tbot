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
    assert result["strategy_version"] == "flip-dip-v0-provisional"


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


def test_live_reports_not_configured_without_market_provider(monkeypatch, tmp_path):
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    monkeypatch.setattr("tbot.api.TwelveDataXauUsdProvider", lambda: (_ for _ in ()).throw(ValueError("missing")))

    app = create_app(calibration_dir=tmp_path)
    result = endpoint(app, "/api/live")(entry_timeframe="5M", bars=500)

    assert result["status"] == "not_configured"
    assert result["execution_enabled"] is False


def test_dashboard_root_contains_user_tabs(tmp_path):
    app = create_app(calibration_dir=tmp_path)
    html = endpoint(app, "/")()

    assert "Live" in html
    assert "Plans" in html
    assert "Performance" in html
    assert "History" in html
    assert "execution disabled" in html.lower()

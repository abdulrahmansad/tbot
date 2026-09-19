from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import timedelta
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from dotenv import load_dotenv

from tbot.data.twelve_data import TwelveDataXauUsdProvider
from tbot.fallback_calendar import FallbackEconomicCalendarProvider
from tbot.finance_calendar import FinanceCalendarProvider
from tbot.flip_dip.backtest import ProvisionalBacktester
from tbot.flip_dip.calibration import export_calibration_csv, export_calibration_json
from tbot.flip_dip.clustering import cluster_ready_setups
from tbot.flip_dip.config import FlipDipConfig
from tbot.fmp_calendar import FmpEconomicCalendarProvider
from tbot.news import NewsBlackoutEngine, NewsGate
from tbot.xoomar_calendar import XoomarEconomicCalendarProvider


def calendar_chain() -> FallbackEconomicCalendarProvider:
    providers = [
        XoomarEconomicCalendarProvider(),
        FinanceCalendarProvider(),
    ]
    if os.getenv("FMP_API_KEY"):
        providers.append(FmpEconomicCalendarProvider())
    return FallbackEconomicCalendarProvider(providers)


def run_one(
    provider,
    calendar,
    scanner,
    entry_tf,
    confirmation_tf,
    bars,
    out_dir,
    *,
    allow_no_news: bool,
):
    entry = provider.fetch_candles(timeframe=entry_tf, outputsize=bars)
    htf = provider.fetch_candles(timeframe=confirmation_tf, outputsize=bars)

    events = []
    news_provider_name = None
    news_failures: list[str] = []
    news_filter_applied = False

    if entry:
        try:
            events = calendar.fetch_events(
                start=entry[0].timestamp - timedelta(hours=3),
                end=entry[-1].timestamp + timedelta(hours=3),
            )
            news_provider_name = calendar.last_provider_name
            news_failures = list(calendar.last_failures)
            news_filter_applied = True
        except Exception:
            news_failures = list(calendar.last_failures)
            if not allow_no_news:
                raise

    engine = NewsBlackoutEngine(
        before_minutes=scanner.strategy_config.news_blackout_before_minutes,
        after_minutes=scanner.strategy_config.news_blackout_after_minutes,
    )

    def news_gate_at(moment):
        if not news_filter_applied:
            return NewsGate(clear=True)
        return engine.evaluate(now=moment, events=events)

    setups = scanner.scan(
        {entry_tf: entry, confirmation_tf: htf},
        entry_timeframe=entry_tf,
        planned_rr=scanner.strategy_config.minimum_rr,
        news_gate_at=news_gate_at,
    )

    csv_path = export_calibration_csv(
        setups,
        out_dir / f"review-{entry_tf.lower()}.csv",
    )
    json_path = export_calibration_json(
        setups,
        out_dir / f"review-{entry_tf.lower()}.json",
    )

    reasons = Counter()
    outcomes = Counter()
    ready = 0
    execution_counts = Counter()
    for setup in setups:
        if setup.decision.plan is not None:
            ready += 1
            execution_counts[setup.execution_number] += 1
            if setup.outcome is not None:
                outcomes[setup.outcome.status.value] += 1
        else:
            reasons.update(setup.decision.reasons)

    clusters = cluster_ready_setups(setups)
    primary_setup_keys = {cluster.primary_setup_key for cluster in clusters}
    primary_outcomes = Counter(
        setup.outcome.status.value
        for setup in setups
        if setup.setup_key in primary_setup_keys and setup.outcome is not None
    )

    return {
        "entry_timeframe": entry_tf,
        "confirmation_timeframe": confirmation_tf,
        "entry_candles": len(entry),
        "confirmation_candles": len(htf),
        "candidate_count": len(setups),
        "ready_count": ready,
        "ready_by_execution_number": {
            str(key): value for key, value in sorted(execution_counts.items())
        },
        "independent_event_count": len(clusters),
        "secondary_setup_count": max(ready - len(clusters), 0),
        "skipped_count": len(setups) - ready,
        "outcomes": dict(outcomes.most_common()),
        "primary_outcomes": dict(primary_outcomes.most_common()),
        "skip_reasons": dict(reasons.most_common()),
        "news_filter_applied": news_filter_applied,
        "news_provider_name": news_provider_name,
        "news_provider_failures": news_failures,
        "historical_news_events_loaded": len(events),
        "csv": str(csv_path),
        "json": str(json_path),
    }


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Run authoritative Phase 0 XAUUSD Flip & Dip calibration."
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=1000,
        help="Candles fetched per entry/confirmation timeframe (default 1000).",
    )
    parser.add_argument(
        "--label",
        default="latest",
        help="Optional label recorded in summary metadata.",
    )
    parser.add_argument(
        "--include-1h",
        action="store_true",
        help="Also calibrate optional 1H entries with 4H confirmation.",
    )
    parser.add_argument(
        "--allow-no-news",
        action="store_true",
        help=(
            "Development only: continue if historical calendar providers fail. "
            "Do not use this for Phase 0 validation."
        ),
    )
    args = parser.parse_args()

    if args.bars < 500:
        parser.error("--bars must be at least 500")
    if args.bars > 5000:
        parser.error("--bars cannot exceed 5000")

    out_dir = Path("data/runtime/calibration")
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in (
        *out_dir.glob("review-*.csv"),
        *out_dir.glob("review-*.json"),
        *out_dir.glob("summary.json"),
    ):
        stale.unlink(missing_ok=True)

    provider = TwelveDataXauUsdProvider()
    strategy_config = FlipDipConfig(enable_1h_entries=args.include_1h)
    scanner = ProvisionalBacktester(strategy_config=strategy_config)
    calendar = calendar_chain()

    timeframe_pairs = [
        (entry_tf, strategy_config.confirmation_timeframe[entry_tf])
        for entry_tf in strategy_config.enabled_entry_timeframes
    ]

    summaries = []
    for entry_tf, confirmation_tf in timeframe_pairs:
        print(f"Running {entry_tf} -> {confirmation_tf}...")
        summary = run_one(
            provider,
            calendar,
            scanner,
            entry_tf,
            confirmation_tf,
            args.bars,
            out_dir,
            allow_no_news=args.allow_no_news,
        )
        summaries.append(summary)
        print(
            f"  candidates={summary['candidate_count']} "
            f"ready={summary['ready_count']} "
            f"events={summary['independent_event_count']} "
            f"skipped={summary['skipped_count']}"
        )
        print(f"  executions={summary['ready_by_execution_number']}")
        print(f"  outcomes={summary['outcomes']}")
        print(f"  primary_outcomes={summary['primary_outcomes']}")
        print(
            f"  news={summary['news_provider_name']} "
            f"events_loaded={summary['historical_news_events_loaded']}"
        )

    summary_path = out_dir / "summary.json"
    summary_payload = {
        "schema_version": 3,
        "strategy_contract_version": "owner-flip-dip-2026-09-19",
        "risk_model": "structural_rejection_plus_median20_range_floor",
        "risk_floor_multiple": 1.0,
        "bars_requested": args.bars,
        "sample_label": args.label,
        "primary_entry_timeframes": list(strategy_config.primary_entry_timeframes),
        "optional_1h_enabled": strategy_config.enable_1h_entries,
        "max_executions_per_zone": strategy_config.max_executions_per_zone,
        "execution_model": "distinct_retest_episodes_with_correct_side_rearm",
        "rejection_min_score": strategy_config.rejection_min_score,
        "news_blackout_before_minutes": strategy_config.news_blackout_before_minutes,
        "news_blackout_after_minutes": strategy_config.news_blackout_after_minutes,
        "partial_tp_owner_configured": strategy_config.partial_tp_levels is not None,
        "entry_reference": "near_side_zone_edge",
        "strategy_invalidation": "entry_timeframe_candle_close_beyond_zone",
        "timeframes": summaries,
    }
    summary_path.write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    zip_path = Path("data/runtime/tbot-calibration.zip")
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(out_dir.glob("*")):
            archive.write(path, arcname=path.name)

    print(f"Summary: {summary_path}")
    print(f"Calibration bundle: {zip_path}")


if __name__ == "__main__":
    main()

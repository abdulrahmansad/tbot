from datetime import datetime, timezone

from tbot.flip_dip.backtest import HistoricalSetup
from tbot.flip_dip.calibration import export_calibration_csv, export_calibration_json
from tbot.flip_dip.models import Direction, EntryTimeframe, FlipZone
from tbot.flip_dip.planner import PlanDecision


def test_exports_review_files(tmp_path):
    setup = HistoricalSetup(
        zone=FlipZone(
            id="z1",
            direction=Direction.SELL,
            timeframe=EntryTimeframe.M5,
            lower_price=2300,
            upper_price=2302,
            created_at=datetime.now(timezone.utc),
        ),
        rejection_score=0.72,
        decision=PlanDecision(plan=None, reasons=("htf_structure_not_confirmed",)),
    )

    csv_path = export_calibration_csv([setup], tmp_path / "review.csv")
    json_path = export_calibration_json([setup], tmp_path / "review.json")

    assert "htf_structure_not_confirmed" in csv_path.read_text(encoding="utf-8")
    assert '"status": "SKIP"' in json_path.read_text(encoding="utf-8")

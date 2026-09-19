from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .flip_dip.models import (
    Direction,
    EntryTimeframe,
    FlipZone,
    NewsGate,
    SetupState,
    StructureConfirmation,
)


def load_manual_scenario(path: str | Path) -> dict:
    """Load an owner/manual calibration scenario.

    This lets us test the planning engine before automated Flip Zone,
    rejection, and CHoCH/BOS recognition are calibrated.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    zone_data = payload["zone"]
    zone = FlipZone(
        id=zone_data["id"],
        direction=Direction(zone_data["direction"]),
        timeframe=EntryTimeframe(zone_data["timeframe"]),
        lower_price=float(zone_data["lower_price"]),
        upper_price=float(zone_data["upper_price"]),
        created_at=datetime.fromisoformat(zone_data["created_at"]),
        state=SetupState(zone_data.get("state", "WAITING_FOR_RETEST")),
        rejection_score=zone_data.get("rejection_score"),
        execution_count=int(zone_data.get("execution_count", 0)),
    )

    structure_data = payload["structure"]
    structure = StructureConfirmation(
        confirmed=bool(structure_data["confirmed"]),
        timeframe=structure_data["timeframe"],
        direction=Direction(structure_data["direction"]),
        kind=structure_data.get("kind"),
        observed_at=(
            datetime.fromisoformat(structure_data["observed_at"])
            if structure_data.get("observed_at")
            else None
        ),
    )

    news_data = payload.get("news", {"clear": True})
    news = NewsGate(
        clear=bool(news_data["clear"]),
        reason=news_data.get("reason"),
        event_time=(
            datetime.fromisoformat(news_data["event_time"])
            if news_data.get("event_time")
            else None
        ),
    )

    return {
        "zone": zone,
        "structure": structure,
        "news": news,
        "rejection_is_healthy": bool(payload["rejection_is_healthy"]),
        "planned_rr": float(payload["planned_rr"]),
        "now": datetime.fromisoformat(payload["now"]),
    }

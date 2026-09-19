from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def is_within_trading_window(
    moment: datetime,
    *,
    timezone: str,
    start: time,
    end: time,
) -> bool:
    """Return True when moment is within the configured local trading window.

    Handles windows that cross midnight, including 23:00 -> 20:00.
    """
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")

    local = moment.astimezone(ZoneInfo(timezone)).time()

    if start == end:
        return True

    if start < end:
        return start <= local < end

    # Cross-midnight window.
    return local >= start or local < end

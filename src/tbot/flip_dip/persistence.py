from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .demo import DemoPlanRecord


class JsonlDemoStore:
    """Append-only local persistence for demo records.

    This store is intentionally simple for Phase 0. It writes hypothetical
    trade-plan records only and contains no broker or execution integration.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append_record(self, record: DemoPlanRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            json.dump(record.to_dict(), handle, default=str, separators=(",", ":"))
            handle.write("\n")

    def read_raw(self) -> list[dict]:
        if not self.path.exists():
            return []

        rows: list[dict] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    rows.append(json.loads(stripped))
        return rows

    def replace_all(self, records: Iterable[DemoPlanRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            for record in records:
                json.dump(record.to_dict(), handle, default=str, separators=(",", ":"))
                handle.write("\n")

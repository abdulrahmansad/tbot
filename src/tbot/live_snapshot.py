from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LiveSnapshotStore:
    """Shared read/write store for the worker-produced live planning snapshot."""

    def __init__(self, path: str | Path = "data/runtime/live-snapshot.json") -> None:
        self.path = Path(path)

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        temporary.replace(self.path)

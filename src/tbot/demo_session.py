from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DemoSession:
    name: str
    start: datetime
    end: datetime

    def status_at(self, moment: datetime) -> str:
        if moment < self.start:
            return "SCHEDULED"
        if moment > self.end:
            return "ENDED"
        return "ACTIVE"


class DemoSessionStore:
    def __init__(self, path: str | Path = "data/runtime/demo-session.json") -> None:
        self.path = Path(path)

    def read(self) -> DemoSession | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return DemoSession(
            name=str(payload["name"]),
            start=datetime.fromisoformat(payload["start"]),
            end=datetime.fromisoformat(payload["end"]),
        )

    def write(self, session: DemoSession) -> None:
        if session.start.tzinfo is None or session.end.tzinfo is None:
            raise ValueError("session dates must be timezone-aware")
        if session.end <= session.start:
            raise ValueError("session end must be after start")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {
                    "name": session.name,
                    "start": session.start.isoformat(),
                    "end": session.end.isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def describe(self, *, now: datetime | None = None) -> dict[str, Any]:
        session = self.read()
        moment = now or datetime.now(timezone.utc)
        if session is None:
            return {
                "configured": False,
                "status": "UNBOUNDED",
                "name": None,
                "start": None,
                "end": None,
            }
        return {
            "configured": True,
            "status": session.status_at(moment),
            "name": session.name,
            "start": session.start.isoformat(),
            "end": session.end.isoformat(),
        }

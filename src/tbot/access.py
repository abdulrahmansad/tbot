from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class BasicAccessConfig:
    username: str
    password: str


def private_access_from_env() -> BasicAccessConfig | None:
    username = os.getenv("TBOT_DASHBOARD_USERNAME")
    password = os.getenv("TBOT_DASHBOARD_PASSWORD")

    if bool(username) != bool(password):
        raise ValueError(
            "TBOT_DASHBOARD_USERNAME and TBOT_DASHBOARD_PASSWORD must be set together"
        )
    if not username:
        return None
    return BasicAccessConfig(username=username, password=password)


def basic_authorized(
    authorization_header: str | None,
    config: BasicAccessConfig,
) -> bool:
    if not authorization_header or not authorization_header.startswith("Basic "):
        return False

    encoded = authorization_header[6:].strip()
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except Exception:
        return False

    if ":" not in decoded:
        return False
    username, password = decoded.split(":", 1)
    return (
        secrets.compare_digest(username, config.username)
        and secrets.compare_digest(password, config.password)
    )

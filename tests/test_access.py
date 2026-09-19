import base64

import pytest

from tbot.access import BasicAccessConfig, basic_authorized, private_access_from_env


def auth_header(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def test_basic_auth_accepts_exact_credentials():
    config = BasicAccessConfig(username="demo", password="secret")

    assert basic_authorized(auth_header("demo", "secret"), config) is True


def test_basic_auth_rejects_wrong_credentials():
    config = BasicAccessConfig(username="demo", password="secret")

    assert basic_authorized(auth_header("demo", "wrong"), config) is False
    assert basic_authorized(None, config) is False


def test_private_access_env_requires_both_values(monkeypatch):
    monkeypatch.setenv("TBOT_DASHBOARD_USERNAME", "demo")
    monkeypatch.delenv("TBOT_DASHBOARD_PASSWORD", raising=False)

    with pytest.raises(ValueError):
        private_access_from_env()


def test_private_access_env_can_be_disabled(monkeypatch):
    monkeypatch.delenv("TBOT_DASHBOARD_USERNAME", raising=False)
    monkeypatch.delenv("TBOT_DASHBOARD_PASSWORD", raising=False)

    assert private_access_from_env() is None

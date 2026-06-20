"""Generic manifest save endpoint (POST /api/config/manifest) — the backbone that lets the
web + TUI settings forms edit ANY of the 64 settings, not just hand-listed ones.

update_env_values is monkeypatched so the test never touches the real .env; we assert the
validated set that would be persisted + hot-applied to os.environ.
"""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "src.api.web_ui.update_env_values",
        lambda updates, verbose=True: captured.update(updates) or True,
    )
    from src.main import app
    c = TestClient(app)
    c._captured = captured
    return c


def test_valid_settings_are_typed_persisted_and_applied(client, monkeypatch):
    # pick a real bool + a real int setting from the manifest
    from src.core import config_manifest as M
    a_bool = next(s for s in M.SETTINGS if s.type is bool)
    an_int = next(s for s in M.SETTINGS if s.type is int)

    r = client.post("/api/config/manifest", json={
        a_bool.env_var.lower(): True,
        an_int.env_var.lower(): 7,
    }).json()

    assert r["status"] == "success"
    assert a_bool.env_var in r["saved"] and an_int.env_var in r["saved"]
    assert client._captured[a_bool.env_var] == "true"
    assert client._captured[an_int.env_var] == "7"
    assert os.environ[an_int.env_var] == "7"


def test_unknown_key_rejected_not_dropped(client):
    r = client.post("/api/config/manifest", json={"definitely_not_a_setting": "x"}).json()
    assert r["saved"] == []
    assert "definitely_not_a_setting" in r["rejected"]


def test_masked_secret_is_skipped(client):
    from src.core import config_manifest as M
    secret = next((s for s in M.SETTINGS if s.secret), None)
    if secret is None:
        pytest.skip("no secret settings in manifest")
    r = client.post("/api/config/manifest", json={secret.env_var.lower(): "***"}).json()
    assert secret.env_var not in r["saved"]            # unchanged secret not overwritten
    assert secret.env_var not in client._captured

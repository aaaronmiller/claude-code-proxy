"""Config-schema surface for the manifest-driven settings UIs (web + TUI).

`/api/config` returns values only; the generic UIs also need each setting's metadata
(group, render widget, choices, secret) to render the form. That metadata comes from
`config_manifest.as_schema_response()` and is served at `GET /api/config/schema`.
"""
from src.core import config_manifest as M


def test_schema_covers_every_setting_grouped():
    schema = M.as_schema_response()
    groups = schema["groups"]
    flat = [s for g in groups for s in g["settings"]]
    assert len(flat) == len(M.SETTINGS)                       # nothing dropped
    assert {g["name"] for g in groups} == {s.group for s in M.SETTINGS}


def test_each_setting_carries_render_metadata():
    flat = [s for g in M.as_schema_response()["groups"] for s in g["settings"]]
    for s in flat:
        assert s["key"] == s["env_var"].lower()
        assert s["type"] in ("str", "int", "float", "bool")
        assert s["web_component"] in ("input", "switch", "select", "number", "textarea", "slider")
        assert s["tui_widget"] in ("input", "toggle", "select", "number", "textarea")
        assert "description" in s and "group" in s


def test_secret_defaults_are_not_leaked():
    flat = [s for g in M.as_schema_response()["groups"] for s in g["settings"]]
    for s in flat:
        if s["secret"]:
            assert s["default"] in (None, "", "***")          # never the raw secret default

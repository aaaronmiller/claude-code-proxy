"""S1-02: the config manifest is the single source that drives all 4 surfaces
(.env / CLI / TUI / Web). One Setting entry => every surface. Characterization test for the
parity guarantee (specs/001). See ai-gateway/plan/05-CONFIG-SCHEMA.md + RECON-03."""
from src.core import config_manifest as M

_TUI = {"input", "toggle", "select", "number", "textarea"}
_WEB = {"input", "switch", "select", "number", "textarea", "slider"}


def test_every_setting_carries_all_surface_metadata():
    assert M.SETTINGS, "manifest must not be empty"
    for s in M.SETTINGS:
        assert s.env_var and s.env_var.isupper()        # .env surface
        assert s.tui_widget in _TUI                      # TUI surface
        assert s.web_component in _WEB                   # Web surface
        if s.cli_flag is not None:                       # CLI surface (optional per setting)
            assert s.cli_flag.startswith("--")


def test_cli_flags_round_trip_and_are_unique():
    flagged = [s for s in M.SETTINGS if s.cli_flag]
    assert flagged
    seen = set()
    for s in flagged:
        assert M.get_by_cli_flag(s.cli_flag) is s        # flag resolves to its own setting
        assert s.cli_flag not in seen, f"duplicate cli_flag {s.cli_flag}"
        seen.add(s.cli_flag)


def test_env_var_lookup():
    s0 = M.SETTINGS[0]
    assert M.get_by_env_var(s0.env_var) is s0
    assert M.get_by_env_var("NOPE_NOT_A_SETTING") is None


def test_surfaces_cover_the_same_setting_set():
    setting_envs = {s.env_var for s in M.SETTINGS}
    assert set(M.current_env_dict().keys()) == setting_envs
    assert set(M.as_config_response().keys()) == {e.lower() for e in setting_envs}


def test_secret_settings_are_masked(monkeypatch):
    secret = next((s for s in M.SETTINGS if s.secret), None)
    if secret is None:
        return  # no secret-flagged settings; nothing to assert
    monkeypatch.setenv(secret.env_var, "supersecretvalue")
    assert M.as_config_response()[secret.env_var.lower()] == "***"

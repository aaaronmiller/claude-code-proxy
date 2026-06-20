"""Settings TUI: the pure change-detection logic must never wipe secrets and must send
only real edits. (The Textual UI itself is thin glue over this + the config API.)"""
from src.cli.settings_tui import collect_changes


def test_only_changed_values_are_sent():
    loaded = {"host": "127.0.0.1", "port": 8082, "track_usage": True}
    current = {"host": "0.0.0.0", "port": 8082, "track_usage": True}
    assert collect_changes(loaded, current) == {"host": "0.0.0.0"}


def test_bool_toggle_detected():
    assert collect_changes({"track_usage": True}, {"track_usage": False}) == {"track_usage": False}


def test_masked_secret_never_sent():
    # "***" placeholder and an untouched-blank secret must both be skipped
    loaded = {"proxy_auth_key": "***"}
    assert collect_changes(loaded, {"proxy_auth_key": "***"}) == {}
    assert collect_changes(loaded, {"proxy_auth_key": ""}) == {}
    # a real new secret IS sent
    assert collect_changes(loaded, {"proxy_auth_key": "s3cr3t"}) == {"proxy_auth_key": "s3cr3t"}


def test_module_imports_without_textual_stack():
    # collect_changes + SettingsAPI must be usable even if the Textual app is never built
    import src.cli.settings_tui as m
    assert hasattr(m, "SettingsAPI") and hasattr(m, "main")

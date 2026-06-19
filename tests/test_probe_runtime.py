"""F03/F11 probe wiring: turn the active allocation/overlay into probe targets and run the
injectable probe over them. Offline — http_post and credential resolution are both injected."""
from src.core.model_scan_binder import BindResult, ResolvedBinding
from src.services.probe_runtime import ProbeTarget, probe_targets, targets_from_binding


def _ok_post(url, headers, json, timeout):
    return 200, {"usage": {"completion_tokens": 1}}, 0.12


def test_targets_from_binding_flattens_overlay():
    binding = BindResult(
        overlay={
            "rich": {"big": ResolvedBinding("anthropic/opus", "", (), "allocator", "anthropic", "big")},
            "econ": {"big": ResolvedBinding("or/free", "", (), "allocator", "openrouter", "big")},
        }
    )
    targets = targets_from_binding(binding)
    keys = {(t.profile, t.role, t.provider, t.api_model) for t in targets}
    assert keys == {
        ("rich", "big", "anthropic", "anthropic/opus"),
        ("econ", "big", "openrouter", "or/free"),
    }
    assert targets_from_binding(None) == []


def test_probe_targets_runs_injected_probe():
    targets = [ProbeTarget("rich", "big", "anthropic", "", "anthropic/opus")]
    creds = lambda provider, base_url: ("https://api.anthropic.test/v1", "sk-test")
    results = probe_targets(targets, creds, http_post=_ok_post)
    assert len(results) == 1
    r = results[0]
    assert r["profile"] == "rich" and r["role"] == "big"
    assert r["ok"] is True and r["status"] == 200
    assert r["tokens_out"] == 1 and r["error_class"] == "ok"


def test_probe_targets_skips_when_no_endpoint():
    targets = [ProbeTarget("p", "r", "ghost", "", "ghost/model")]
    creds = lambda provider, base_url: ("", "")  # provider not in registry
    results = probe_targets(targets, creds, http_post=_ok_post)
    assert results[0]["ok"] is False
    assert results[0]["error_class"] == "no_endpoint"

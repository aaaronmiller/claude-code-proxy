"""S1-07: F18 greedy allocator dry-run. Verifies satisfice-then-maximize, floor gates,
and scarce-capacity contention. See ai-gateway/plan/F18 + 04-DATA-CONTRACTS.md."""
from src.core.quota_sources import QuotaMeter
from src.services.allocator import Candidate, RoleSpec, allocate


def _meter(provider, limit, remaining, unit="calls"):
    return QuotaMeter(id=f"{provider}:{unit}", provider=provider, unit=unit,
                      window_seconds=86400, limit=limit, remaining=remaining)


# cerebras is scarcer (30% left) than openrouter (full)
SCARCE = _meter("cerebras", 1000, 300)
ABUNDANT = _meter("openrouter", 100000, 100000)

TOP = Candidate("cer/top", "cerebras", fitness=95, has_tools=True)
FREE_A = Candidate("or/free-a", "openrouter", fitness=60, has_tools=True)
FREE_B = Candidate("or/free-b", "openrouter", fitness=55, has_tools=True)
NOTOOLS = Candidate("x/notools", "openrouter", fitness=99, has_tools=False)


def test_maximizing_role_takes_top_fitness():
    role = RoleSpec("hermes-1", "primary", value_sensitivity=0.9, importance=0.9,
                    needs_tools=True, expected_calls_per_day=100)
    res = allocate([role], {"primary": [TOP, FREE_A, FREE_B]}, [SCARCE, ABUNDANT])
    a = res.allocations[0]
    assert a.primary == "cer/top"          # highest fitness, affordable
    assert a.cascade                        # has fallbacks


def test_satisficing_role_preserves_scarce_capacity():
    role = RoleSpec("pi-economy", "primary", value_sensitivity=0.1, importance=0.4,
                    expected_calls_per_day=100)
    res = allocate([role], {"primary": [TOP, FREE_A, FREE_B]}, [SCARCE, ABUNDANT])
    a = res.allocations[0]
    # cer/top is affordable but scarcer; satisfice must pick the abundant free model
    assert a.primary in ("or/free-a", "or/free-b")
    assert a.primary != "cer/top"


def test_floor_gate_excludes_no_tools_model():
    role = RoleSpec("s", "toolcall", value_sensitivity=0.9, needs_tools=True,
                    expected_calls_per_day=100)
    res = allocate([role], {"toolcall": [NOTOOLS, FREE_A]}, [ABUNDANT])
    a = res.allocations[0]
    assert a.primary == "or/free-a"        # NOTOOLS excluded despite fitness 99


def test_scarce_contention_two_maximizers():
    # cerebras only has room for one role's 100 calls
    scarce = _meter("cerebras", 1000, 150)
    a_role = RoleSpec("hermes-A", "primary", value_sensitivity=0.9, importance=0.9,
                      needs_tools=True, expected_calls_per_day=100)
    b_role = RoleSpec("hermes-B", "primary", value_sensitivity=0.9, importance=0.5,
                      needs_tools=True, expected_calls_per_day=100)
    res = allocate([a_role, b_role], {"primary": [TOP, FREE_A, FREE_B]}, [scarce, ABUNDANT])
    by_session = {a.session_id: a.primary for a in res.allocations}
    assert by_session["hermes-A"] == "cer/top"          # higher priority claims scarce
    assert by_session["hermes-B"] in ("or/free-a", "or/free-b")  # falls to free, still served


def test_bottleneck_report_present():
    role = RoleSpec("s", "primary", value_sensitivity=0.9, expected_calls_per_day=100)
    res = allocate([role], {"primary": [TOP, FREE_A]}, [SCARCE, ABUNDANT])
    assert res.bottleneck_meters
    assert res.bottleneck_meters[0][0] == "cerebras:calls"  # tightest after allocation


# --- S1-08: allocator -> snapshot mapping ---
import json
from src.services.allocator import allocation_to_snapshot_dict


def test_mapping_shape():
    role = RoleSpec("hermes-1", "primary", value_sensitivity=0.9, needs_tools=True,
                    expected_calls_per_day=100)
    cbr = {"primary": [TOP, FREE_A, FREE_B]}
    res = allocate([role], cbr, [SCARCE, ABUNDANT])
    snap = allocation_to_snapshot_dict(res, cbr, generated_at="2026-06-17T00:00:00Z", scan_id=1)
    assert "hermes-1:primary" in snap["slots"]
    slot = snap["slots"]["hermes-1:primary"]
    assert slot["best"]["model_id"] == "cer/top"
    assert slot["best"]["provider"] == "cerebras"
    assert slot["candidates"][0]["model_id"] == "cer/top"
    assert len(slot["candidates"]) >= 1


def test_mapping_parses_via_model_scan_snapshot(tmp_path):
    from src.services.models import model_scan_snapshot
    role = RoleSpec("pi-1", "primary", value_sensitivity=0.9, needs_tools=True,
                    expected_calls_per_day=100)
    cbr = {"primary": [TOP, FREE_A, FREE_B]}
    res = allocate([role], cbr, [SCARCE, ABUNDANT])
    snap = allocation_to_snapshot_dict(res, cbr, generated_at="2026-06-17T00:00:00Z", scan_id=2)
    p = tmp_path / "routing_snapshot.json"
    p.write_text(json.dumps(snap))
    loaded = model_scan_snapshot.load(str(p))
    assert loaded is not None, "augmented snapshot must parse via the real loader"
    assert "pi-1:primary" in loaded.slots
    assert loaded.slots["pi-1:primary"].best.model_id == "cer/top"


# --- S1-08 (integration core): real snapshot -> allocator -> augmented snapshot ---
from src.services.allocator import plan_from_snapshot


def _cand_dict(mid, prov, fit, tools=True):
    return {"model_id": mid, "provider": prov, "api_model": mid, "base_url": "",
            "fitness": fit, "price_blended": 0.0, "tier": "A",
            "has_tools": tools, "has_vision": False}


def _input_snapshot(tmp_path):
    from src.services.models import model_scan_snapshot
    data = {
        "schema_version": "1.0.0", "generated_at": "2026-06-17T00:00:00Z", "scan_id": 1,
        "slots": {"primary": {
            "label": "primary", "eval_mode": "cost_basis",
            "best": _cand_dict("cer/top", "cerebras", 95),
            "candidates": [_cand_dict("cer/top", "cerebras", 95),
                           _cand_dict("or/free-a", "openrouter", 60)],
        }},
        "provider_health": {}, "provider_quota": {}, "blocklist": [],
    }
    p = tmp_path / "in.json"
    p.write_text(json.dumps(data))
    return model_scan_snapshot.load(str(p))


def test_plan_from_snapshot_routes_sessions_differently(tmp_path):
    snap = _input_snapshot(tmp_path)
    assert snap is not None
    scarce = _meter("cerebras", 1000, 300)
    roles = [
        RoleSpec("hermes-1", "primary", value_sensitivity=0.9, importance=0.9,
                 needs_tools=True, expected_calls_per_day=100),
        RoleSpec("pi-econ", "primary", value_sensitivity=0.1, importance=0.4,
                 expected_calls_per_day=100),
    ]
    out = plan_from_snapshot(snap, roles, [scarce, ABUNDANT], generated_at="t", scan_id=2)
    slots = out["slots"]
    # maximizing session gets the scarce top model; satisficing session gets the free one
    assert slots["hermes-1:primary"]["best"]["model_id"] == "cer/top"
    assert slots["pi-econ:primary"]["best"]["model_id"] == "or/free-a"


def _snapshot_with(tmp_path, slot, cands):
    from src.services.models import model_scan_snapshot
    data = {"schema_version": "1.0.0", "generated_at": "t", "scan_id": 1,
            "slots": {slot: {"label": slot, "eval_mode": "cost_basis",
                             "best": cands[0], "candidates": cands}},
            "provider_health": {}, "provider_quota": {}, "blocklist": []}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(data))
    return model_scan_snapshot.load(str(p))


def test_named_floor_resolution(tmp_path):
    from src.services.allocator import resolve_named_floors
    cands = [_cand_dict("strong/y", "openrouter", 80),
             _cand_dict("openai/gpt-oss-120b", "openrouter", 30.2),
             _cand_dict("weak/x", "openrouter", 20)]
    snap = _snapshot_with(tmp_path, "primary", cands)
    role = RoleSpec("h", "primary", value_sensitivity=0.9, needs_tools=True)
    resolved = resolve_named_floors([role], {"primary": "openai/gpt-oss-120b"}, snap)
    assert resolved[0].floor_min_value == 30.2


def test_plan_named_floor_excludes_below(tmp_path):
    cands = [_cand_dict("strong/y", "openrouter", 80),
             _cand_dict("openai/gpt-oss-120b", "openrouter", 30.2),
             _cand_dict("weak/x", "openrouter", 20)]
    snap = _snapshot_with(tmp_path, "primary", cands)
    role = RoleSpec("h", "primary", value_sensitivity=0.9, needs_tools=True,
                    expected_calls_per_day=10)
    out = plan_from_snapshot(snap, [role], [ABUNDANT],
                             named_floors={"primary": "openai/gpt-oss-120b"})
    slot = out["slots"]["h:primary"]
    assert slot["best"]["model_id"] == "strong/y"
    assert "weak/x" not in [c["model_id"] for c in slot["candidates"]]  # below resolved floor


def test_named_floor_base_match_and_unknown(tmp_path):
    from src.services.allocator import resolve_named_floors
    snap = _snapshot_with(tmp_path, "aux", [_cand_dict("openai/gpt-oss-120b", "openrouter", 30.2)])
    aux1 = RoleSpec("h", "aux-1", value_sensitivity=0.05)
    assert resolve_named_floors([aux1], {"aux": "openai/gpt-oss-120b"}, snap)[0].floor_min_value == 30.2
    assert resolve_named_floors([aux1], {"aux": "nonexistent/model"}, snap)[0].floor_min_value == 0.0


def test_seam_is_noop_when_disabled(tmp_path):
    from src.services.allocator import apply_allocator_if_enabled
    snap = _input_snapshot(tmp_path)
    roles = [RoleSpec("s", "primary", value_sensitivity=0.9, needs_tools=True)]
    # disabled -> None (caller keeps original snapshot unchanged)
    assert apply_allocator_if_enabled(snap, roles, [ABUNDANT], enabled=False) is None
    # enabled but no roles configured -> safe no-op (never misroutes)
    assert apply_allocator_if_enabled(snap, [], [ABUNDANT], enabled=True) is None
    # enabled with roles -> produces augmented snapshot
    out = apply_allocator_if_enabled(snap, roles, [ABUNDANT], enabled=True)
    assert out is not None and "s:primary" in out["slots"]


def test_allocator_flag_registered_and_off_by_default():
    from src.core import config_manifest as M
    s = M.get_by_env_var("ALLOCATOR_ENABLED")
    assert s is not None and s.default is False
    assert M.get_by_cli_flag("--allocator-enabled") is s

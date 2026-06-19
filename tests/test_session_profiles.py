"""F18/F12: session-profile config -> RoleSpec plumbing. Pure, offline.
See ai-gateway/plan/05-CONFIG-SCHEMA.md."""
from src.services.session_profiles import role_specs_from_profile, named_floor_models

HERMES_FULL = {
    "start_mode": "rollup",
    "roles": {
        "primary": {"floor": {"min_tier": "A", "needs_tools": True}, "value_sensitivity": 1.0,
                    "importance": 1.0},
        "aux": {"floor": {"min_value": 30.2}, "value_sensitivity": 0.05, "count": 10},
        "vision": {"floor": {"needs_vision": True}, "value_sensitivity": 0.5},
    },
}


def test_expands_count_roles():
    specs = role_specs_from_profile("hermes-1", HERMES_FULL)
    by_id = {s.role_id for s in specs}
    assert "primary" in by_id and "vision" in by_id
    assert sum(1 for s in specs if s.role_id.startswith("aux-")) == 10  # count=10 expanded
    assert len(specs) == 12


def test_field_mapping_and_defaults():
    specs = {s.role_id: s for s in role_specs_from_profile("h", HERMES_FULL)}
    p = specs["primary"]
    assert p.session_id == "h" and p.needs_tools is True
    assert p.value_sensitivity == 1.0 and p.importance == 1.0
    assert p.diversity_cap == 0.6 and p.fallback_depth == 4   # defaults
    aux1 = specs["aux-1"]
    assert aux1.value_sensitivity == 0.05 and aux1.floor_min_value == 30.2
    assert specs["vision"].needs_vision is True


def test_named_floor_surfaced_not_silently_numeric():
    cfg = {"roles": {"primary": {"floor": {"min_value": "deepseek-v4-flash"}}}}
    specs = role_specs_from_profile("pi", cfg)
    # a model-NAME floor must not be coerced to a bogus number; stays 0.0 pending resolution
    assert specs[0].floor_min_value == 0.0
    # and it is surfaced for plan-time resolution against the snapshot
    assert named_floor_models(cfg) == {"primary": "deepseek-v4-flash"}

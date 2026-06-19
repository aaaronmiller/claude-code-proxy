import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "status" / "codex_status.py"


def load_module():
    spec = importlib.util.spec_from_file_location("codex_status", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_read_session_extracts_context_permissions_and_tokens(tmp_path):
    codex_status = load_module()
    session = tmp_path / "rollout.jsonl"
    session.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "turn_context",
                        "payload": {
                            "cwd": "/repo",
                            "approval_policy": "never",
                            "sandbox_policy": {"type": "danger-full-access"},
                            "permission_profile": {"type": "disabled"},
                            "model": "gpt-5.5",
                            "collaboration_mode": {
                                "settings": {"reasoning_effort": "medium"}
                            },
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "total_token_usage": {
                                    "input_tokens": 100_000,
                                    "cached_input_tokens": 80_000,
                                    "output_tokens": 10_000,
                                    "total_tokens": 110_000,
                                },
                                "last_token_usage": {
                                    "input_tokens": 40_000,
                                    "cached_input_tokens": 30_000,
                                    "output_tokens": 4_000,
                                    "total_tokens": 44_000,
                                },
                                "model_context_window": 200_000,
                            },
                            "rate_limits": {
                                "primary": {"used_percent": 12.0},
                                "secondary": {"used_percent": 34.0},
                                "plan_type": "plus",
                            },
                        },
                    }
                ),
            ]
        )
    )

    data = codex_status.read_session(session)

    assert data["model"] == "gpt-5.5"
    assert data["reasoning_effort"] == "medium"
    assert data["permission"] == "danger"
    assert data["approval"] == "never"
    assert data["context"]["used_pct"] == 22.0
    assert data["tokens"]["input"] == 100_000
    assert data["tokens"]["cached"] == 80_000
    assert data["limits"]["primary_pct"] == 12.0


def test_find_latest_session_prefers_matching_cwd(tmp_path):
    codex_status = load_module()
    old = tmp_path / "old.jsonl"
    new = tmp_path / "new.jsonl"
    old.write_text(json.dumps({"type": "turn_context", "payload": {"cwd": "/other"}}))
    new.write_text(json.dumps({"type": "turn_context", "payload": {"cwd": "/repo"}}))

    assert codex_status.find_latest_session(tmp_path, "/repo") == new


def test_format_right_contains_compact_operational_fields():
    codex_status = load_module()
    text = codex_status.format_right(
        {
            "model": "gpt-5.5",
            "reasoning_effort": "medium",
            "permission": "danger",
            "approval": "never",
            "context": {"used_pct": 76.1, "used_tokens": 196_000, "window": 258_400},
            "tokens": {
                "input": 9_000_000,
                "cached": 8_000_000,
                "output": 25_000,
                "total": 9_025_000,
            },
            "limits": {"primary_pct": 16.0, "secondary_pct": 9.0, "plan": "plus"},
            "estimated_cost_usd": 3.25,
        },
        now=lambda: "Fri 18:40",
    )

    assert "gpt-5.5/m" in text
    assert "perm:danger" in text
    assert "ctx:76%" in text
    assert "in:9.0M" in text
    assert "cache:8.0M" in text
    assert "$3.25" in text
    assert "Fri 18:40" in text

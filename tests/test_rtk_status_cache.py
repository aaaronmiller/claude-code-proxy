import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "status" / "rtk_status.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rtk_status", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_refresh_writes_normalized_project_cache(tmp_path):
    rtk_status = load_module()
    cache_path = tmp_path / "rtk-status.json"

    def runner(cmd, cwd, timeout):
        assert cmd == ["rtk", "gain", "--project", "--format", "json"]
        return 0, json.dumps(
            {
                "summary": {
                    "total_commands": 4,
                    "total_input": 1000,
                    "total_output": 250,
                    "total_saved": 750,
                    "avg_savings_pct": 75.0,
                    "total_time_ms": 120,
                    "avg_time_ms": 30,
                }
            }
        ), ""

    data = rtk_status.refresh_cache(
        cache_path=cache_path,
        scope="project",
        cwd="/repo",
        runner=runner,
        now=lambda: 1000.0,
    )

    assert data["status"] == "ok"
    assert data["scope"] == "project"
    assert data["stale"] is False
    assert data["summary"]["total_saved"] == 750
    assert data["summary"]["avg_savings_pct"] == 75.0
    assert json.loads(cache_path.read_text()) == data


def test_refresh_failure_returns_stale_cache(tmp_path):
    rtk_status = load_module()
    cache_path = tmp_path / "rtk-status.json"
    cache_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "scope": "project",
                "generated_at": "2026-05-30T00:00:00Z",
                "generated_at_unix": 900.0,
                "stale": False,
                "summary": {"total_saved": 123, "avg_savings_pct": 45.0, "total_commands": 2},
            }
        )
    )

    def runner(cmd, cwd, timeout):
        return 1, "", "rtk failed"

    data = rtk_status.refresh_cache(
        cache_path=cache_path,
        scope="project",
        cwd="/repo",
        runner=runner,
        now=lambda: 1000.0,
    )

    assert data["status"] == "stale"
    assert data["stale"] is True
    assert data["summary"]["total_saved"] == 123
    assert data["error"] == "rtk failed"


def test_get_stats_uses_fresh_cache_without_running_rtk(tmp_path):
    rtk_status = load_module()
    cache_path = tmp_path / "rtk-status.json"
    cache_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "scope": "project",
                "generated_at": "2026-05-30T00:00:00Z",
                "generated_at_unix": 995.0,
                "stale": False,
                "summary": {"total_saved": 999, "avg_savings_pct": 50.0, "total_commands": 3},
            }
        )
    )

    def runner(cmd, cwd, timeout):
        raise AssertionError("runner should not be called for fresh cache")

    data = rtk_status.get_stats(
        cache_path=cache_path,
        scope="project",
        cwd="/repo",
        ttl_seconds=10,
        runner=runner,
        now=lambda: 1000.0,
    )

    assert data["status"] == "ok"
    assert data["summary"]["total_saved"] == 999


def test_tmux_format_is_compact_and_stale_aware():
    rtk_status = load_module()
    rendered = rtk_status.format_tmux(
        {
            "status": "stale",
            "stale": True,
            "summary": {
                "total_saved": 12_561,
                "avg_savings_pct": 38.3,
                "total_commands": 40,
            },
        }
    )

    assert "RTK" in rendered
    assert "38%" in rendered
    assert "12.6Ktok saved" in rendered
    assert "stale" in rendered

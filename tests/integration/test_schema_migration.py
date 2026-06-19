"""Integration tests for schema migration (v1 → v2).

Covers:
  (a) happy path: v1 data is auto-migrated, file rewritten, log written
  (b) unsafe migration: unknown top-level keys present → startup halts, file preserved
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from src.core.proxy_chain import ProxyChain
from src.core.schema_migrations import migrate_if_needed


def _cleanup_migration_logs() -> None:
    """Remove any migration logs from previous test runs."""
    log_dir = Path("config/migrations")
    if log_dir.exists():
        for f in log_dir.glob("*.log"):
            try:
                f.unlink()
            except Exception:
                pass


def write_v1_config(path: Path, extra_keys: dict | None = None) -> None:
    """Write a minimal v1 proxy_chain.json to `path`."""
    v1 = {
        "entries": [
            {
                "id": "headroom",
                "name": "Headroom",
                "url": "http://127.0.0.1:8787/v1",
                "auth_key": "",
                "enabled": True,
                "order": 0,
                "service_cmd": "",
                "health_path": "/health",
                "port": 8787,
                "timeout": 90,
                "extra_headers": {},
                "type": "http",
                "model_prefixes": [],
            }
        ],
        "router": {
            "default": {"model": "openai/gpt-3.5-turbo", "base_url": "", "api_key": ""},
            "background": "nvidia/nemotron-nano-9b-v2:free",
            "think": "",
            "long_context": {
                "model": "minimax/minimax-m2.5:free",
                "base_url": "",
                "api_key": "",
            },
            "web_search": "",
            "image": "qwen/qwen2.5-vl-72b-instruct",
        },
    }
    if extra_keys:
        v1.update(extra_keys)
    path.write_text(json.dumps(v1, indent=2), encoding="utf-8")


def test_happy_migration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """v1 file migrates cleanly to v2; file and migration log written."""
    # Arrange
    _cleanup_migration_logs()
    config_file = tmp_path / "proxy_chain.json"
    write_v1_config(config_file)
    # Also include legacy tier field to test that path
    extra = {"big_model": "anthropic/claude-3", "big_endpoint": "", "big_api_key": ""}
    # We need to rewrite with extra
    config_file.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "headroom",
                        "name": "Headroom",
                        "url": "http://127.0.0.1:8787/v1",
                        "auth_key": "",
                        "enabled": True,
                        "order": 0,
                        "service_cmd": "",
                        "health_path": "/health",
                        "port": 8787,
                        "timeout": 90,
                        "extra_headers": {},
                        "type": "http",
                        "model_prefixes": [],
                    }
                ],
                "router": {
                    "default": {
                        "model": "openai/gpt-3.5-turbo",
                        "base_url": "",
                        "api_key": "",
                    },
                    "background": "nvidia/nemotron-nano-9b-v2:free",
                    "think": "",
                    "long_context": {"model": "minimax/minimax-m2.5:free"},
                    "web_search": "",
                    "image": "qwen/qwen2.5-vl-72b-instruct",
                },
                "big_model": "anthropic/claude-3",
                "big_endpoint": "",
                "big_api_key": "",
            },
            indent=2,
        )
    )

    # Point proxy chain file at our temp file
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(config_file))
    # Also ensure we write migrated file back to same location

    # Act: load chain
    chain = ProxyChain.load()

    # Assert schema version
    assert chain.schema_version == "2.0.0"
    # Check assignments populated
    assignment_ids = {a.id for a in chain.assignments}
    assert "big" in assignment_ids  # from legacy tier fields
    assert "default" in assignment_ids
    assert "background" in assignment_ids
    assert "long_context" in assignment_ids
    assert "image" in assignment_ids
    # Ensure identifier_mappings empty
    assert chain.identifier_mappings == []

    # Assert file on disk now contains v2 schema
    on_disk = json.loads(config_file.read_text())
    assert on_disk["schema_version"] == "2.0.0"
    assert "assignments" in on_disk

    # Migration log should exist under config/migrations/
    log_dir = Path("config/migrations")
    assert log_dir.is_dir()
    log_files = list(log_dir.glob("*-v1-to-v2.log"))
    assert len(log_files) >= 1
    log_content = log_files[0].read_text()
    assert "v1-to-v2" in log_content


def test_unsafe_migration_halts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown top-level keys trigger RuntimeError and leave file untouched."""
    _cleanup_migration_logs()
    config_file = tmp_path / "proxy_chain.json"
    write_v1_config(config_file, extra_keys={"mystery_field": "bad"})

    monkeypatch.setenv("PROXY_CHAIN_FILE", str(config_file))

    with pytest.raises(RuntimeError) as excinfo:
        ProxyChain.load()
    assert "Migration unsafe" in str(excinfo.value) or "Unknown" in str(excinfo.value)

    # File should remain unchanged (still v1 without schema_version)
    data = json.loads(config_file.read_text())
    assert "schema_version" not in data
    # No migration log should be written
    log_dir = Path("config/migrations")
    if log_dir.exists():
        log_files = list(log_dir.glob("*-v1-to-v2.log"))
        assert len(log_files) == 0

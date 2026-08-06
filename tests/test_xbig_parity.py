"""Four-tier parity checks for the XBIG configuration surface."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from src.core import config_manifest as manifest
from src.core.config_resolver import ConfigResolver
from src.core.model_manager import ModelManager
from src.models.reasoning import OpenAIReasoningConfig
from src.services.conversion import request_converter
from src.services.prompts import system_prompt_loader


ROOT = Path(__file__).resolve().parents[1]
TIERS = ("XBIG", "BIG", "MIDDLE", "SMALL")


def test_manifest_exposes_the_same_contract_for_all_four_tiers():
    env_vars = {setting.env_var for setting in manifest.SETTINGS}
    suffixes = (
        "MODEL",
        "CASCADE",
        "MODEL_REASONING",
        "ENDPOINT",
        "API_KEY",
        "SYSTEM_PROMPT_FILE",
        "SYSTEM_PROMPT",
    )
    for tier in TIERS:
        for suffix in suffixes:
            assert f"{tier}_{suffix}" in env_vars
        assert f"ENABLE_{tier}_ENDPOINT" in env_vars
        assert f"ENABLE_CUSTOM_{tier}_PROMPT" in env_vars


def test_xbig_secrets_are_masked(monkeypatch):
    monkeypatch.setenv("XBIG_API_KEY", "not-a-real-key")
    assert manifest.as_config_response()["xbig_api_key"] == "***"


def test_resolver_and_config_schema_accept_xbig_legacy_fields(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XBIG_MODEL", "provider/frontier-model")
    monkeypatch.setenv("XBIG_ENDPOINT", "https://provider.invalid/v1")
    monkeypatch.setenv("XBIG_API_KEY", "indirect-test-value")
    monkeypatch.setenv("XBIG_MODEL_REASONING", "high")
    monkeypatch.setenv("ENABLE_CUSTOM_XBIG_PROMPT", "true")
    monkeypatch.setenv("XBIG_SYSTEM_PROMPT", "Frontier planning prompt")

    resolver = ConfigResolver()

    assert resolver.resolve("assignments.xbig.model").value == "provider/frontier-model"
    assert resolver.resolve("assignments.xbig.base_url").value == "https://provider.invalid/v1"
    assert resolver.resolve("assignments.xbig.api_key").value == "indirect-test-value"
    assert resolver.resolve("xbig_model_reasoning").value == "high"
    assert resolver.resolve("enable_custom_xbig_prompt").value == "true"
    assert resolver.resolve("xbig_system_prompt").value == "Frontier planning prompt"


def _prompt_config(**overrides):
    values = {
        "enable_custom_xbig_prompt": False,
        "xbig_system_prompt_file": "",
        "xbig_system_prompt": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_xbig_prompt_uses_file_before_inline(monkeypatch):
    calls = []
    monkeypatch.setattr(
        system_prompt_loader,
        "load_system_prompt",
        lambda source: calls.append(source) or "loaded prompt",
    )
    cfg = _prompt_config(
        enable_custom_xbig_prompt=True,
        xbig_system_prompt_file="/safe/prompt.md",
        xbig_system_prompt="inline fallback",
    )

    assert system_prompt_loader.get_model_system_prompt("xbig", cfg) == "loaded prompt"
    assert calls == ["path:/safe/prompt.md"]


def test_explicit_xbig_model_is_classified_as_xbig(monkeypatch):
    cfg = SimpleNamespace(
        xbig_model="provider/frontier-model",
        big_model="provider/big-model",
        middle_model="provider/middle-model",
        small_model="provider/small-model",
    )
    monkeypatch.setattr(request_converter, "config", cfg)
    assert request_converter._get_model_size_from_model_id("provider/frontier-model") == "xbig"


def test_xbig_reasoning_override_reaches_request_configuration():
    cfg = SimpleNamespace(
        xbig_model="openai/gpt-5.5",
        big_model="openai/gpt-5",
        middle_model="openai/gpt-4.1",
        small_model="openai/gpt-4o-mini",
        xbig_model_reasoning="high",
        big_model_reasoning="",
        middle_model_reasoning="",
        small_model_reasoning="",
        reasoning_effort="low",
        reasoning_max_tokens=32000,
        reasoning_exclude=False,
    )

    resolved = ModelManager(cfg)._get_default_reasoning_config("openai/gpt-5.5")

    assert isinstance(resolved, OpenAIReasoningConfig)
    assert resolved.effort == "high"


def test_examples_document_all_xbig_surfaces():
    combined = (ROOT / ".env.example").read_text() + (ROOT / "config/env.example").read_text()
    for env_var in (
        "XBIG_MODEL",
        "XBIG_ENDPOINT",
        "XBIG_API_KEY",
        "XBIG_CASCADE",
        "XBIG_MODEL_REASONING",
        "ENABLE_CUSTOM_XBIG_PROMPT",
        "XBIG_SYSTEM_PROMPT_FILE",
        "XBIG_SYSTEM_PROMPT",
    ):
        assert env_var in combined


def test_xx_xbig_selector_dry_run_is_key_free(tmp_path):
    config_path = tmp_path / "xx.json"
    config_path.write_text(
        json.dumps(
            {
                "proxy": {"auto_start": False},
                "model_tiers": {"XBIG": {"default": "provider/frontier-model"}},
            }
        )
    )
    env = os.environ.copy()
    env["XX_CONFIG"] = str(config_path)

    result = subprocess.run(
        [str(ROOT / "scripts/xx"), "cix", "--dry-run"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--model provider/frontier-model" in result.stderr
    assert "API_KEY=pass" not in result.stderr
    assert "API_KEY=<set>" in result.stderr
    assert "not-a-real-key" not in result.stderr

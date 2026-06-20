"""OpenRouter Fusion request support.

Fusion is OpenRouter-specific. The proxy keeps this as a request mutation layer
so Claude, Codex, Hermes, Qwen, and other OpenAI-compatible clients can opt in
by asking for a local alias such as ``fusion``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


OPENROUTER_FUSION_MODEL = "openrouter/fusion"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


@dataclass(frozen=True)
class FusionProfile:
    """Concrete Fusion profile resolved from environment variables."""

    name: str
    model: str
    analysis_models: tuple[str, ...]
    preset: str | None = None
    max_tool_calls: int | None = None
    max_completion_tokens: int | None = None
    temperature: float | None = None
    force: bool = False
    enabled: bool = True

    def plugin(self) -> dict[str, Any]:
        plugin: dict[str, Any] = {"id": "fusion", "enabled": self.enabled}
        if self.preset:
            plugin["preset"] = self.preset
        if self.analysis_models:
            plugin["analysis_models"] = list(self.analysis_models)
        if self.model:
            plugin["model"] = self.model
        if self.max_tool_calls is not None:
            plugin["max_tool_calls"] = self.max_tool_calls
        if self.max_completion_tokens is not None:
            plugin["max_completion_tokens"] = self.max_completion_tokens
        if self.temperature is not None:
            plugin["temperature"] = self.temperature
        return plugin


def fusion_aliases() -> set[str]:
    aliases = {
        "fusion",
        "ccp/fusion",
        "openrouter/fusion",
    }
    aliases.update(alias.lower() for alias in _csv(os.getenv("FUSION_ALIASES")))
    return aliases


def is_fusion_model(model: str | None) -> bool:
    if not model:
        return False
    model_lower = model.lower()
    return model_lower in fusion_aliases() or model_lower.startswith("fusion/")


def fusion_profile_from_model(model: str | None) -> str | None:
    if not model:
        return None
    model_lower = model.lower()
    if model_lower.startswith("fusion/"):
        _, profile = model_lower.split("/", 1)
        return profile.strip() or None
    return None


def _profile_env(prefix: str, key: str) -> str | None:
    return os.getenv(f"{prefix}_{key}") or os.getenv(f"FUSION_{key}")


def _optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def get_fusion_profile(name: str | None = None) -> FusionProfile:
    """Resolve a Fusion profile from env.

    Supported env:
      FUSION_PROFILE=free
      FUSION_FREE_ANALYSIS_MODELS=model-a,model-b
      FUSION_FREE_MODEL=openrouter/free
      FUSION_FREE_PRESET=general-budget
      FUSION_FREE_FORCE=true

    FUSION_PROFILES may also contain JSON:
      {"free":{"analysis_models":["openrouter/free"],"model":"openrouter/free"}}
    """

    profile_name = (name or os.getenv("FUSION_PROFILE") or "free").strip().lower()
    json_profiles = os.getenv("FUSION_PROFILES", "").strip()
    raw: dict[str, Any] = {}
    if json_profiles:
        parsed = json.loads(json_profiles)
        if not isinstance(parsed, dict):
            raise ValueError("FUSION_PROFILES must be a JSON object")
        candidate = parsed.get(profile_name, {})
        if candidate and not isinstance(candidate, dict):
            raise ValueError(f"FUSION_PROFILES.{profile_name} must be an object")
        raw = candidate or {}

    prefix = f"FUSION_{profile_name.upper().replace('-', '_')}"
    raw_analysis_models = raw.get("analysis_models")
    if isinstance(raw_analysis_models, str):
        analysis_models_value = _csv(raw_analysis_models)
    elif raw_analysis_models:
        analysis_models_value = list(raw_analysis_models)
    else:
        analysis_models_value = _csv(_profile_env(prefix, "ANALYSIS_MODELS"))
    analysis_models = tuple(
        analysis_models_value or ("openrouter/free", "openrouter/free", "openrouter/free")
    )
    judge_model = raw.get("model") or _profile_env(prefix, "MODEL") or "openrouter/free"
    preset = raw.get("preset") or _profile_env(prefix, "PRESET")

    return FusionProfile(
        name=profile_name,
        model=str(judge_model),
        analysis_models=tuple(str(model) for model in analysis_models),
        preset=str(preset) if preset else None,
        max_tool_calls=raw.get("max_tool_calls")
        if "max_tool_calls" in raw
        else _optional_int(_profile_env(prefix, "MAX_TOOL_CALLS")),
        max_completion_tokens=raw.get("max_completion_tokens")
        if "max_completion_tokens" in raw
        else _optional_int(_profile_env(prefix, "MAX_COMPLETION_TOKENS")),
        temperature=raw.get("temperature")
        if "temperature" in raw
        else _optional_float(_profile_env(prefix, "TEMPERATURE")),
        force=bool(raw.get("force"))
        if "force" in raw
        else _truthy(_profile_env(prefix, "FORCE"), default=False),
        enabled=bool(raw.get("enabled"))
        if "enabled" in raw
        else _truthy(_profile_env(prefix, "ENABLED"), default=True),
    )


def apply_fusion_to_openai_request(
    request: dict[str, Any],
    profile_name: str | None = None,
) -> tuple[dict[str, Any], FusionProfile | None]:
    """Return a request mutated for OpenRouter Fusion when its model is an alias.

    For OpenAI SDK calls, OpenRouter-specific `plugins` is placed inside
    `extra_body`; the SDK merges that into the outgoing JSON.
    """

    if not is_fusion_model(request.get("model")):
        return request, None

    profile = get_fusion_profile(profile_name or fusion_profile_from_model(request.get("model")))
    next_request = dict(request)
    next_request["model"] = OPENROUTER_FUSION_MODEL

    extra_body = dict(next_request.get("extra_body") or {})
    plugins = list(extra_body.get("plugins") or [])
    plugins = [p for p in plugins if not (isinstance(p, dict) and p.get("id") == "fusion")]
    plugins.append(profile.plugin())
    extra_body["plugins"] = plugins
    next_request["extra_body"] = extra_body

    if profile.force and not next_request.get("tools"):
        next_request["tool_choice"] = "required"

    return next_request, profile


def openrouter_api_key(config: Any = None, fallback: str | None = None) -> str | None:
    for candidate in (
        os.getenv("OPENROUTER_API_KEY"),
        os.getenv("BIG_API_KEY"),
        getattr(config, "openai_api_key", None) if config is not None else None,
        fallback,
    ):
        if candidate:
            return str(candidate)
    return None


def openrouter_base_url(config: Any = None) -> str:
    for candidate in (
        os.getenv("OPENROUTER_BASE_URL"),
        os.getenv("FUSION_OPENROUTER_BASE_URL"),
        getattr(config, "openai_base_url", None) if config is not None else None,
        OPENROUTER_BASE_URL,
    ):
        if candidate and ("openrouter.ai" in str(candidate) or "8787" in str(candidate)):
            return str(candidate)
    return OPENROUTER_BASE_URL

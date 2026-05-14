"""
Model context window and output limits database.

Uses models.dev (https://models.dev) as the primary data source — a community-maintained
catalog of 2000+ LLM models from 75+ providers with metadata like pricing, context limits,
modalities, and capabilities. Updated hourly.

Fallback chain:
1. models.dev (primary — always try first)
2. OpenRouter cache (data/openrouter_models.json)
3. Static fallback entries (non-OpenRouter providers like opencode_go)

Run `python dev/scripts/scrape_openrouter_models.py` to update local cache.

Key features from models.dev:
- Context/output limits
- Pricing (input/output per million tokens)
- Capabilities: reasoning, tool_call, structured_output, attachment
- Modalities: input/output support (text, image, audio, video, pdf)
- Knowledge cutoff date
- Open weights indicator
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── models.dev integration ───────────────────────────────────────────────────

_MODELS_DEV_CACHE: Optional[Dict[str, Any]] = None
_MODELS_DEV_LOADED = False


def _load_models_dev() -> Tuple[Dict[str, Any], bool]:
    """
    Load models.dev data as the primary source.

    Returns:
        Tuple of (models_dev_data, was_loaded)
        - models_dev_data: Dict[provider_id][model_id] -> ModelMetadata
        - was_loaded: True if data was successfully loaded
    """
    global _MODELS_DEV_CACHE, _MODELS_DEV_LOADED

    if _MODELS_DEV_LOADED:
        return _MODELS_DEV_CACHE, True

    _MODELS_DEV_LOADED = True

    try:
        from models_dev import providers, get_provider

        data: Dict[str, Dict[str, Any]] = {}

        for p in providers():
            provider_models = {}
            for model_id, m in p.models.items():
                # Normalize: convert models_dev model ID to proxy format
                # models.dev uses "provider/model" format for OR models,
                # but some providers use bare model names

                # Build normalized entry
                provider_models[model_id] = {
                    # Limits (primary use case)
                    "context": m.limit.context,
                    "output": m.limit.output,
                    # Pricing (USD per million tokens)
                    "cost_input": m.cost.input if m.cost else None,
                    "cost_output": m.cost.output if m.cost else None,
                    # Capabilities
                    "reasoning": m.reasoning,
                    "tool_call": m.tool_call,
                    "structured_output": getattr(m, "structured_output", False),
                    "attachment": m.attachment,
                    "open_weights": m.open_weights,
                    # Modalities
                    "modalities_in": m.modalities.input if m.modalities else [],
                    "modalities_out": m.modalities.output if m.modalities else [],
                    # Metadata
                    "family": m.family,
                    "knowledge": m.knowledge,
                    "release_date": m.release_date,
                    "name": m.name,
                    # Provider info
                    "provider_id": p.id,
                    "provider_name": p.name,
                }

            data[p.id] = provider_models

        _MODELS_DEV_CACHE = data

        total_models = sum(len(v) for v in data.values())
        logger.info(
            f"Loaded {total_models} models from models.dev ({len(data)} providers)"
        )

        return data, True

    except ImportError:
        logger.warning("models-dev not installed. Run: pip install models-dev")
        return {}, False
    except Exception as e:
        logger.warning(f"Failed to load models.dev: {e}")
        return {}, False


def _lookup_models_dev(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Look up a model in models.dev with multi-format support.

    Handles:
    - openrouter/owl-alpha → openrouter provider, key "openrouter/owl-alpha"
    - opencode_go/qwen3.6-plus → opencode-go provider, key "qwen3.6-plus"
    - nvidia/nemotron-3-nano → nvidia provider, key "nemotron-3-nano"
    - openai/gpt-4o → openai provider, key "openai/gpt-4o" or "gpt-4o"
    """
    data, loaded = _load_models_dev()
    if not loaded or data is None:
        return None

    # Normalize model name
    clean_name = model_name.lower().strip()

    # Strategy 1: Try as-is (provider/model format)
    if clean_name in data.get(clean_name.split("/")[0], {}):
        provider = clean_name.split("/")[0]
        return data[provider].get(clean_name)

    # Strategy 2: Try without provider prefix against each provider
    if "/" in clean_name:
        bare_name = clean_name.split("/", 1)[1]
        for provider_id, models in data.items():
            if bare_name in models:
                return models[bare_name]
            # Also try with provider prefix
            prefixed = f"{provider_id}/{bare_name}"
            if prefixed in models:
                return models[prefixed]

    # Strategy 3: Try provider prefix variations
    provider_map = {
        "opencode_go": "opencode-go",
        "openai": "openai",
        "anthropic": "anthropic",
        "google": "google",
        "nvidia": "nvidia",
        "groq": "groq",
        "deepseek": "deepseek",
        "openrouter": "openrouter",
        "meta-llama": "meta-llama",
    }

    if "/" in clean_name:
        prefix, bare = clean_name.split("/", 1)
        normalized_provider = provider_map.get(prefix, prefix)

        if normalized_provider in data:
            # Try bare name first
            if bare in data[normalized_provider]:
                return data[normalized_provider].get(bare)
            # Try with provider prefix
            prefixed = f"{normalized_provider}/{bare}"
            if prefixed in data[normalized_provider]:
                return data[normalized_provider].get(prefixed)

    return None


# ─── Legacy fallback sources ───────────────────────────────────────────────────

# Path to model limits files (fallback for when models.dev unavailable)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
JSON_PATH = MODELS_DIR / "model_limits.json"
ENRICHED_PATH = PROJECT_ROOT / "data" / "openrouter_models_enriched.json"
OPENROUTER_CACHE_PATH = PROJECT_ROOT / "data" / "openrouter_models.json"

# Legacy fallback cache (for non-OpenRouter providers)
_LEGACY_LIMITS_CACHE: Optional[Dict[str, Dict[str, int]]] = None
_OPENROUTER_CACHE: Optional[Dict[str, Dict[str, int]]] = None


def _load_legacy_fallback() -> Dict[str, Dict[str, int]]:
    """Load legacy static fallback for non-OpenRouter providers."""
    global _LEGACY_LIMITS_CACHE
    if _LEGACY_LIMITS_CACHE is not None:
        return _LEGACY_LIMITS_CACHE

    _LEGACY_LIMITS_CACHE = {
        # OpenCode Go models (from opencode.ai/docs/go/)
        "opencode_go/qwen3.6-plus": {"context": 256000, "output": 32768},
        "opencode_go/qwen3.5-plus": {"context": 256000, "output": 32768},
        "opencode_go/deepseek-v4-flash": {"context": 1000000, "output": 32768},
        "opencode_go/deepseek-v4-pro": {"context": 1000000, "output": 32768},
        "opencode_go/kimi-k2.5": {"context": 262144, "output": 32768},
        "opencode_go/kimi-k2.6": {"context": 262144, "output": 32768},
        "opencode_go/glm-5": {"context": 202752, "output": 8192},
        # Azure (known context limits)
        "azure/gpt-4o": {"context": 128000, "output": 16384},
        "azure/gpt-4o-mini": {"context": 128000, "output": 16384},
        # Cerebras
        "cerebras/qwen-3-235b-a22b-instruct-2507": {"context": 32768, "output": 8192},
        "cerebras/llama3.1-8b": {"context": 128000, "output": 4096},
    }

    return _LEGACY_LIMITS_CACHE


def _load_openrouter_cache() -> Dict[str, Dict[str, int]]:
    """Load OpenRouter model cache from disk (cached after first load)."""
    global _OPENROUTER_CACHE
    if _OPENROUTER_CACHE is not None:
        return _OPENROUTER_CACHE

    limits = {}

    if OPENROUTER_CACHE_PATH.exists():
        try:
            with open(OPENROUTER_CACHE_PATH, "r") as f:
                data = json.load(f)
            if "models" in data:
                for model in data["models"]:
                    model_id = model.get("id", "")
                    if model_id:
                        limits[model_id] = {
                            "context": model.get("context_length") or 128000,
                            "output": model.get("max_completion_tokens") or 4096,
                        }
            logger.info(f"Loaded {len(limits)} model limits from OpenRouter cache")
        except Exception as e:
            logger.warning(f"Failed to load OpenRouter model cache: {e}")

    _OPENROUTER_CACHE = limits
    return limits


# ─── Main lookup function ──────────────────────────────────────────────────────


def get_model_limits(model_name: str) -> Tuple[int, int]:
    """
    Get context window and output limits for a model.

    Resolution order:
    1. models.dev (primary — 2000+ models, auto-updated hourly)
    2. OpenRouter cache (local disk cache)
    3. Legacy fallback (non-OpenRouter providers)
    4. Conservative default (1M context / 32k output)

    Args:
        model_name: Model identifier (e.g., "gpt-4o", "openai/gpt-4o", "opencode_go/qwen3.6-plus")

    Returns:
        Tuple of (context_limit, output_limit) in tokens
    """
    # Priority 1: models.dev (primary source)
    md = _lookup_models_dev(model_name)
    if md:
        return md["context"], md["output"]

    # Priority 2: OpenRouter cache
    or_cache = _load_openrouter_cache()
    # Try exact match
    if model_name in or_cache:
        return or_cache[model_name]["context"], or_cache[model_name]["output"]
    # Try without provider prefix
    if "/" in model_name:
        bare = model_name.split("/", 1)[1]
        if bare in or_cache:
            return or_cache[bare]["context"], or_cache[bare]["output"]

    # Priority 3: Legacy fallback
    legacy = _load_legacy_fallback()
    if model_name in legacy:
        return legacy[model_name]["context"], legacy[model_name]["output"]
    # Try provider prefix variations
    if "/" in model_name:
        prefix, bare = model_name.split("/", 1)
        for variant in [f"{prefix}/{bare}", bare, f"opencode_go/{bare}"]:
            if variant in legacy:
                return legacy[variant]["context"], legacy[variant]["output"]

    # Priority 4: Conservative default
    logger.debug(f"Model limits not found for {model_name}, using defaults (1M/32k)")
    return 1000000, 32768


# ─── Extended model info (pricing, capabilities, modalities) ─────────────────


def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    Get full model metadata from models.dev.

    Returns extended info including:
    - limits: context, output
    - cost: input, output (USD per million tokens)
    - capabilities: reasoning, tool_call, structured_output, attachment, open_weights
    - modalities: input/output support
    - metadata: family, knowledge, release_date, name

    Falls back to basic limits if model not in models.dev.

    Args:
        model_name: Model identifier

    Returns:
        Dict with model metadata (see _lookup_models_dev for full schema)
    """
    md = _lookup_models_dev(model_name)
    if md:
        return md

    # Fallback to basic limits
    ctx, out = get_model_limits(model_name)
    return {
        "context": ctx,
        "output": out,
        "cost_input": None,
        "cost_output": None,
        "reasoning": False,
        "tool_call": False,
        "structured_output": False,
        "attachment": False,
        "open_weights": False,
        "modalities_in": ["text"],
        "modalities_out": ["text"],
        "family": None,
        "knowledge": None,
        "release_date": None,
        "name": model_name.split("/")[-1] if "/" in model_name else model_name,
        "provider_id": None,
        "provider_name": None,
    }


def supports_reasoning(model_name: str) -> bool:
    """Check if model supports reasoning/thinking."""
    info = get_model_info(model_name)
    return bool(info.get("reasoning"))


def supports_tool_call(model_name: str) -> bool:
    """Check if model supports tool/function calling."""
    info = get_model_info(model_name)
    return bool(info.get("tool_call"))


def supports_vision(model_name: str) -> bool:
    """Check if model supports image input."""
    info = get_model_info(model_name)
    modalities = info.get("modalities_in", [])
    return (
        "image" in modalities or "text" in modalities
    )  # conservative: text models support text


def supports_pdf(model_name: str) -> bool:
    """Check if model supports PDF attachment."""
    info = get_model_info(model_name)
    modalities = info.get("modalities_in", [])
    return "pdf" in modalities


def supports_audio_input(model_name: str) -> bool:
    """Check if model supports audio input."""
    info = get_model_info(model_name)
    modalities = info.get("modalities_in", [])
    return "audio" in modalities


def supports_audio_output(model_name: str) -> bool:
    """Check if model supports audio output."""
    info = get_model_info(model_name)
    modalities = info.get("modalities_out", [])
    return "audio" in modalities


def get_pricing(model_name: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Get pricing for a model.

    Returns:
        Tuple of (input_cost_per_million, output_cost_per_million) or (None, None) if unavailable
    """
    info = get_model_info(model_name)
    return info.get("cost_input"), info.get("cost_output")


def estimate_cost(
    model_name: str, input_tokens: int, output_tokens: int
) -> Optional[float]:
    """
    Estimate cost for a request.

    Args:
        model_name: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD, or None if pricing not available
    """
    cost_in, cost_out = get_pricing(model_name)
    if cost_in is None or cost_out is None:
        return None

    return (input_tokens / 1_000_000 * cost_in) + (output_tokens / 1_000_000 * cost_out)


# ─── Legacy compatibility functions ────────────────────────────────────────────


def get_context_limit(model_name: str) -> int:
    """Get context window limit for a model."""
    context, _ = get_model_limits(model_name)
    return context


def get_output_limit(model_name: str) -> int:
    """Get max output tokens for a model."""
    _, output = get_model_limits(model_name)
    return output


def format_model_info(model_name: str) -> str:
    """Format model limits as a readable string."""
    context, output = get_model_limits(model_name)

    def format_tokens(count):
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1000:
            return f"{count / 1000:.0f}k"
        return str(count)

    return f"{format_tokens(context)} context / {format_tokens(output)} output"


def reload_model_limits() -> int:
    """
    Reload model limits from sources.

    For models.dev, this reinitializes the provider data.
    Returns total model count.
    """
    global _MODELS_DEV_LOADED, _MODELS_DEV_CACHE
    _MODELS_DEV_LOADED = False
    _MODELS_DEV_CACHE = None

    data, loaded = _load_models_dev()
    if loaded:
        return sum(len(v) for v in data.values())
    return 0


def check_model_limits(
    model_name: str, input_tokens: int, max_output_tokens: int = 0
) -> Tuple[bool, str]:
    """Check if request exceeds model limits."""
    context_limit, output_limit = get_model_limits(model_name)

    total_tokens = input_tokens + max_output_tokens
    if total_tokens > context_limit:
        return (
            False,
            f"Total tokens ({total_tokens}) exceeds model context limit ({context_limit})",
        )

    if max_output_tokens > output_limit:
        return (
            False,
            f"Requested output tokens ({max_output_tokens}) exceeds model output limit ({output_limit})",
        )

    return True, ""


def invalidate_model_limit(model_name: str) -> None:
    """No-op for models.dev (data is in-memory, refreshed on reload)."""
    pass


async def refresh_model_limit_from_api(
    model_name: str, api_key: Optional[str] = None
) -> bool:
    """
    No-op for models.dev (data is bundled in package, auto-updated hourly).

    Use `reload_model_limits()` to force refresh from package data.
    """
    return False


def get_largest_context_model(models: List[str]) -> str:
    """Get model with largest context window from list."""
    best = None
    best_ctx = 0
    for m in models:
        ctx, _ = get_model_limits(m)
        if ctx > best_ctx:
            best = m
            best_ctx = ctx
    return best or (models[0] if models else None)


def get_model_for_input_size(
    input_text: str, preferred_models: List[str], required_output: int = 4096
) -> str:
    """
    Select best model that can handle the input text size.

    Args:
        input_text: The prompt/text to send
        preferred_models: Models to choose from (in priority order)
        required_output: Minimum output tokens needed

    Returns:
        Best model that fits, or first model if none fit
    """
    estimated_input_tokens = len(input_text) // 4

    for model in preferred_models:
        ctx_limit, out_limit = get_model_limits(model)
        effective_context = int(ctx_limit * 0.8)  # 80% safe threshold

        if effective_context >= estimated_input_tokens and out_limit >= required_output:
            return model

    return preferred_models[0] if preferred_models else None


# ─── Capability filtering helpers ─────────────────────────────────────────────


def get_models_by_capability(
    capability: str,
    providers: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Get all models that support a specific capability.

    Args:
        capability: One of "reasoning", "tool_call", "structured_output",
                   "attachment", "open_weights", "vision", "pdf", "audio_input", "audio_output"
        providers: Optional list of provider IDs to filter (e.g., ["openai", "anthropic"])

    Returns:
        List of model info dicts matching the capability
    """
    data, loaded = _load_models_dev()
    if not loaded:
        return []

    results = []
    capability_map = {
        "reasoning": "reasoning",
        "tool_call": "tool_call",
        "structured_output": "structured_output",
        "attachment": "attachment",
        "open_weights": "open_weights",
        "vision": lambda m: "image" in m.get("modalities_in", []),
        "pdf": lambda m: "pdf" in m.get("modalities_in", []),
        "audio_input": lambda m: "audio" in m.get("modalities_in", []),
        "audio_output": lambda m: "audio" in m.get("modalities_out", []),
    }

    checker = capability_map.get(capability)
    if checker is None:
        return []

    for provider_id, models in data.items():
        if providers and provider_id not in providers:
            continue

        for model_id, info in models.items():
            if callable(checker):
                if checker(info):
                    results.append(
                        {"provider": provider_id, "model_id": model_id, **info}
                    )
            elif info.get(checker):
                results.append({"provider": provider_id, "model_id": model_id, **info})

    return results


def get_free_models(providers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get all free models (cost_input == 0 or cost_output == 0).

    Args:
        providers: Optional list of provider IDs to filter

    Returns:
        List of free model info dicts
    """
    data, loaded = _load_models_dev()
    if not loaded:
        return []

    results = []
    for provider_id, models in data.items():
        if providers and provider_id not in providers:
            continue

        for model_id, info in models.items():
            cost_in = info.get("cost_input")
            cost_out = info.get("cost_output")
            if cost_in == 0 or cost_out == 0 or cost_in is None or cost_out is None:
                results.append({"provider": provider_id, "model_id": model_id, **info})

    return results


def get_models_by_context_min(min_context: int) -> List[Dict[str, Any]]:
    """
    Get models with at least min_context tokens.

    Args:
        min_context: Minimum context window size in tokens

    Returns:
        List of model info dicts with context >= min_context
    """
    data, loaded = _load_models_dev()
    if not loaded:
        return []

    results = []
    for provider_id, models in data.items():
        for model_id, info in models.items():
            if info.get("context", 0) >= min_context:
                results.append({"provider": provider_id, "model_id": model_id, **info})

    return sorted(results, key=lambda x: -x[0].get("context", 0))


# ─── Provider info helpers ─────────────────────────────────────────────────────


def get_provider_info(provider_id: str) -> Optional[Dict[str, Any]]:
    """
    Get provider metadata from models.dev.

    Returns:
        Dict with provider info (name, env, doc, api, etc.) or None if not found
    """
    data, loaded = _load_models_dev()
    if not loaded:
        return None

    if provider_id not in data:
        return None

    # Get from provider-level data
    try:
        from models_dev import get_provider

        p = get_provider(provider_id)
        return {
            "id": p.id,
            "name": p.name,
            "api": p.api,
            "doc": p.doc,
            "env": p.env,
            "model_count": len(p.models),
        }
    except Exception:
        return {"id": provider_id, "model_count": len(data[provider_id])}


def list_providers() -> List[Dict[str, Any]]:
    """
    List all available providers from models.dev.

    Returns:
        List of provider info dicts with id, name, model_count
    """
    data, loaded = _load_models_dev()
    if not loaded:
        return []

    return [
        {"id": pid, "name": pid, "model_count": len(models)}
        for pid, models in sorted(data.items())
    ]

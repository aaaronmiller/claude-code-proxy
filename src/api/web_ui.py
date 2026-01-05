"""Web UI and Configuration API endpoints"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from src.core.config import config
from src.core.logging import logger

router = APIRouter()

# Profile storage path
PROFILES_DIR = Path("configs/profiles")
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


class ConfigUpdate(BaseModel):
    """Configuration update model - supports all web UI settings"""
    # Core settings
    provider_api_key: Optional[str] = None
    provider_base_url: Optional[str] = None
    proxy_auth_key: Optional[str] = None

    # Legacy fallback names
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None

    # Server settings
    host: Optional[str] = None
    port: Optional[str] = None
    log_level: Optional[str] = None

    # Model settings
    big_model: Optional[str] = None
    middle_model: Optional[str] = None
    small_model: Optional[str] = None

    # Reasoning settings
    reasoning_effort: Optional[str] = None
    reasoning_max_tokens: Optional[str] = None
    reasoning_exclude: Optional[str] = None

    # Token limits
    max_tokens_limit: Optional[str] = None
    min_tokens_limit: Optional[str] = None
    request_timeout: Optional[str] = None

    # Terminal display settings
    terminal_display_mode: Optional[str] = None
    terminal_color_scheme: Optional[str] = None
    log_style: Optional[str] = None
    terminal_show_workspace: Optional[str] = None
    terminal_show_context_pct: Optional[str] = None
    terminal_show_task_type: Optional[str] = None
    terminal_show_speed: Optional[str] = None
    terminal_show_cost: Optional[str] = None
    terminal_show_duration_colors: Optional[str] = None
    terminal_session_colors: Optional[str] = None
    compact_logger: Optional[str] = None

    # Dashboard settings
    track_usage: Optional[str] = None
    enable_dashboard: Optional[str] = None
    dashboard_layout: Optional[str] = None
    dashboard_refresh: Optional[str] = None

    # Hybrid mode settings
    enable_big_endpoint: Optional[str] = None
    big_endpoint: Optional[str] = None
    big_api_key: Optional[str] = None
    enable_middle_endpoint: Optional[str] = None
    middle_endpoint: Optional[str] = None
    middle_api_key: Optional[str] = None
    enable_small_endpoint: Optional[str] = None
    small_endpoint: Optional[str] = None
    small_api_key: Optional[str] = None

    # Legacy
    use_compact_logger: Optional[str] = None


class ProfileCreate(BaseModel):
    """Profile creation model"""
    name: str
    config: Dict[str, Any]


@router.get("/api/config")
async def get_config():
    """Get current configuration - returns all settings for web UI"""
    return {
        # ═══════════════════════════════════════════════════════════════════════════════
        # PROVIDER & AUTH
        # ═══════════════════════════════════════════════════════════════════════════════
        "provider_api_key": "***" if (os.getenv("PROVIDER_API_KEY") or config.openai_api_key) else "",
        "provider_base_url": os.getenv("PROVIDER_BASE_URL") or config.openai_base_url,
        "proxy_auth_key": "***" if (os.getenv("PROXY_AUTH_KEY") or config.anthropic_api_key) else "",
        "default_provider": os.getenv("DEFAULT_PROVIDER", "openrouter"),
        "azure_api_version": os.getenv("AZURE_API_VERSION", ""),
        "enable_openrouter_selection": os.getenv("ENABLE_OPENROUTER_SELECTION", "true"),

        # Legacy names (for backward compatibility)
        "openai_api_key": "***" if config.openai_api_key else "",
        "anthropic_api_key": "***" if config.anthropic_api_key else "",
        "openai_base_url": config.openai_base_url,

        # ═══════════════════════════════════════════════════════════════════════════════
        # SERVER CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════
        "host": os.getenv("HOST", config.host if hasattr(config, 'host') else "0.0.0.0"),
        "port": os.getenv("PORT", str(config.port) if hasattr(config, 'port') else "8082"),
        "log_level": os.getenv("LOG_LEVEL", config.log_level if hasattr(config, 'log_level') else "INFO"),

        # ═══════════════════════════════════════════════════════════════════════════════
        # MODEL SETTINGS
        # ═══════════════════════════════════════════════════════════════════════════════
        "big_model": config.big_model,
        "middle_model": config.middle_model,
        "small_model": config.small_model,

        # ═══════════════════════════════════════════════════════════════════════════════
        # REASONING CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════
        "reasoning_effort": config.reasoning_effort if hasattr(config, 'reasoning_effort') else "",
        "reasoning_max_tokens": str(config.reasoning_max_tokens) if hasattr(config, 'reasoning_max_tokens') and config.reasoning_max_tokens else "",
        "reasoning_exclude": os.getenv("REASONING_EXCLUDE", "false"),
        "verbosity": os.getenv("VERBOSITY", ""),
        # Per-tier reasoning overrides
        "big_model_reasoning": os.getenv("BIG_MODEL_REASONING", ""),
        "middle_model_reasoning": os.getenv("MIDDLE_MODEL_REASONING", ""),
        "small_model_reasoning": os.getenv("SMALL_MODEL_REASONING", ""),

        # ═══════════════════════════════════════════════════════════════════════════════
        # CUSTOM SYSTEM PROMPTS
        # ═══════════════════════════════════════════════════════════════════════════════
        "enable_custom_big_prompt": os.getenv("ENABLE_CUSTOM_BIG_PROMPT", "false"),
        "big_system_prompt": os.getenv("BIG_SYSTEM_PROMPT", ""),
        "big_system_prompt_file": os.getenv("BIG_SYSTEM_PROMPT_FILE", ""),
        "enable_custom_middle_prompt": os.getenv("ENABLE_CUSTOM_MIDDLE_PROMPT", "false"),
        "middle_system_prompt": os.getenv("MIDDLE_SYSTEM_PROMPT", ""),
        "middle_system_prompt_file": os.getenv("MIDDLE_SYSTEM_PROMPT_FILE", ""),
        "enable_custom_small_prompt": os.getenv("ENABLE_CUSTOM_SMALL_PROMPT", "false"),
        "small_system_prompt": os.getenv("SMALL_SYSTEM_PROMPT", ""),
        "small_system_prompt_file": os.getenv("SMALL_SYSTEM_PROMPT_FILE", ""),

        # ═══════════════════════════════════════════════════════════════════════════════
        # PERFORMANCE SETTINGS
        # ═══════════════════════════════════════════════════════════════════════════════
        "max_tokens_limit": str(config.max_tokens_limit) if hasattr(config, 'max_tokens_limit') else "65536",
        "min_tokens_limit": str(config.min_tokens_limit) if hasattr(config, 'min_tokens_limit') else "4096",
        "request_timeout": str(config.request_timeout) if hasattr(config, 'request_timeout') else "120",
        "max_retries": str(config.max_retries) if hasattr(config, 'max_retries') else "2",

        # ═══════════════════════════════════════════════════════════════════════════════
        # TERMINAL DISPLAY
        # ═══════════════════════════════════════════════════════════════════════════════
        "terminal_display_mode": os.getenv("TERMINAL_DISPLAY_MODE", "detailed"),
        "terminal_color_scheme": os.getenv("TERMINAL_COLOR_SCHEME", "auto"),
        "terminal_show_workspace": os.getenv("TERMINAL_SHOW_WORKSPACE", "true"),
        "terminal_show_context_pct": os.getenv("TERMINAL_SHOW_CONTEXT_PCT", "true"),
        "terminal_show_task_type": os.getenv("TERMINAL_SHOW_TASK_TYPE", "true"),
        "terminal_show_speed": os.getenv("TERMINAL_SHOW_SPEED", "true"),
        "terminal_show_cost": os.getenv("TERMINAL_SHOW_COST", "true"),
        "terminal_show_duration_colors": os.getenv("TERMINAL_SHOW_DURATION_COLORS", "true"),
        "terminal_session_colors": os.getenv("TERMINAL_SESSION_COLORS", "true"),

        # ═══════════════════════════════════════════════════════════════════════════════
        # LOGGING SETTINGS
        # ═══════════════════════════════════════════════════════════════════════════════
        "log_style": os.getenv("LOG_STYLE", "rich"),
        "compact_logger": os.getenv("COMPACT_LOGGER", "false"),
        "show_token_counts": os.getenv("SHOW_TOKEN_COUNTS", "true"),
        "show_performance": os.getenv("SHOW_PERFORMANCE", "true"),
        "color_scheme": os.getenv("COLOR_SCHEME", "auto"),

        # ═══════════════════════════════════════════════════════════════════════════════
        # USAGE & ANALYTICS
        # ═══════════════════════════════════════════════════════════════════════════════
        "track_usage": os.getenv("TRACK_USAGE", "false"),
        "usage_db_path": os.getenv("USAGE_DB_PATH", "usage_tracking.db"),

        # ═══════════════════════════════════════════════════════════════════════════════
        # DASHBOARD SETTINGS
        # ═══════════════════════════════════════════════════════════════════════════════
        "enable_dashboard": os.getenv("ENABLE_DASHBOARD", "false"),
        "dashboard_layout": os.getenv("DASHBOARD_LAYOUT", "default"),
        "dashboard_refresh": os.getenv("DASHBOARD_REFRESH", "0.5"),
        "dashboard_waterfall_size": os.getenv("DASHBOARD_WATERFALL_SIZE", "20"),

        # ═══════════════════════════════════════════════════════════════════════════════
        # HYBRID MODE (Per-tier routing)
        # ═══════════════════════════════════════════════════════════════════════════════
        "enable_big_endpoint": os.getenv("ENABLE_BIG_ENDPOINT", "false"),
        "big_endpoint": os.getenv("BIG_ENDPOINT", ""),
        "big_api_key": "***" if os.getenv("BIG_API_KEY") else "",
        "enable_middle_endpoint": os.getenv("ENABLE_MIDDLE_ENDPOINT", "false"),
        "middle_endpoint": os.getenv("MIDDLE_ENDPOINT", ""),
        "middle_api_key": "***" if os.getenv("MIDDLE_API_KEY") else "",
        "enable_small_endpoint": os.getenv("ENABLE_SMALL_ENDPOINT", "false"),
        "small_endpoint": os.getenv("SMALL_ENDPOINT", ""),
        "small_api_key": "***" if os.getenv("SMALL_API_KEY") else "",

        # ═══════════════════════════════════════════════════════════════════════════════
        # CASCADE (Fallback)
        # ═══════════════════════════════════════════════════════════════════════════════
        "model_cascade": os.getenv("MODEL_CASCADE", "false"),
        "big_cascade": os.getenv("BIG_CASCADE", ""),
        "middle_cascade": os.getenv("MIDDLE_CASCADE", ""),
        "small_cascade": os.getenv("SMALL_CASCADE", ""),

        # Mode indicator
        "passthrough_mode": config.passthrough_mode if hasattr(config, 'passthrough_mode') else False,
    }


@router.post("/api/config")
async def update_config(config_update: ConfigUpdate):
    """Update configuration (hot reload without restart)"""
    try:
        # Update config object
        if config_update.openai_api_key is not None:
            if config_update.openai_api_key:
                config.openai_api_key = config_update.openai_api_key
                config.passthrough_mode = False
            else:
                config.openai_api_key = None
                config.passthrough_mode = True

        if config_update.anthropic_api_key is not None:
            config.anthropic_api_key = config_update.anthropic_api_key or None

        if config_update.openai_base_url:
            config.openai_base_url = config_update.openai_base_url

        if config_update.big_model:
            config.big_model = config_update.big_model

        if config_update.middle_model:
            config.middle_model = config_update.middle_model

        if config_update.small_model:
            config.small_model = config_update.small_model

        if hasattr(config, 'reasoning_effort') and config_update.reasoning_effort is not None:
            config.reasoning_effort = config_update.reasoning_effort

        if hasattr(config, 'reasoning_max_tokens') and config_update.reasoning_max_tokens:
            config.reasoning_max_tokens = int(config_update.reasoning_max_tokens)

        # Update environment variables for persistence
        if config_update.track_usage is not None:
            os.environ["TRACK_USAGE"] = config_update.track_usage

        if config_update.use_compact_logger is not None:
            os.environ["USE_COMPACT_LOGGER"] = config_update.use_compact_logger

        logger.info("Configuration updated via Web UI")
        return {"status": "success", "message": "Configuration updated"}

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/reload")
async def reload_config():
    """Reload configuration from environment variables"""
    try:
        # Re-initialize config from environment
        config.openai_api_key = os.environ.get("OPENAI_API_KEY")
        config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        config.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        config.big_model = os.environ.get("BIG_MODEL", "gpt-4o")
        config.middle_model = os.environ.get("MIDDLE_MODEL", config.big_model)
        config.small_model = os.environ.get("SMALL_MODEL", "gpt-4o-mini")

        logger.info("Configuration reloaded from environment")
        return {"status": "success", "message": "Configuration reloaded"}

    except Exception as e:
        logger.error(f"Failed to reload config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profiles")
async def list_profiles():
    """List all saved profiles"""
    try:
        profiles = []
        for profile_file in PROFILES_DIR.glob("*.json"):
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
                profiles.append({
                    "name": profile_data["name"],
                    "modified": profile_data.get("modified", datetime.now().isoformat()),
                    "big_model": profile_data["config"].get("big_model", ""),
                    "middle_model": profile_data["config"].get("middle_model", ""),
                    "small_model": profile_data["config"].get("small_model", ""),
                })
        return profiles

    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        return []


@router.post("/api/profiles")
async def save_profile(profile: ProfileCreate):
    """Save a configuration profile"""
    try:
        profile_file = PROFILES_DIR / f"{profile.name}.json"
        profile_data = {
            "name": profile.name,
            "modified": datetime.now().isoformat(),
            "config": profile.config
        }

        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)

        logger.info(f"Profile '{profile.name}' saved")
        return {"status": "success", "message": f"Profile '{profile.name}' saved"}

    except Exception as e:
        logger.error(f"Failed to save profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/profiles/{profile_name}")
async def get_profile(profile_name: str):
    """Get a specific profile"""
    try:
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        if not profile_file.exists():
            raise HTTPException(status_code=404, detail="Profile not found")

        with open(profile_file, 'r') as f:
            return json.load(f)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to load profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/profiles/{profile_name}")
async def delete_profile(profile_name: str):
    """Delete a profile"""
    try:
        profile_file = PROFILES_DIR / f"{profile_name}.json"
        if not profile_file.exists():
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_file.unlink()
        logger.info(f"Profile '{profile_name}' deleted")
        return {"status": "success", "message": f"Profile '{profile_name}' deleted"}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models")
async def list_models(
    provider: Optional[str] = None,
    search: Optional[str] = None,
    supports_reasoning: Optional[bool] = None,
    supports_vision: Optional[bool] = None,
    supports_tools: Optional[bool] = None,
    is_free: Optional[bool] = None,
    min_context: Optional[int] = None,
    limit: Optional[int] = None,
    group_by_provider: bool = False
):
    """
    List available models with optional filtering and organization.

    Args:
        provider: Filter by provider (openai, anthropic, google, etc.)
        search: Search in model ID and name
        supports_reasoning: Filter by reasoning capability
        supports_vision: Filter by vision capability
        supports_tools: Filter by tool use capability
        is_free: Filter by free pricing
        min_context: Minimum context length
        limit: Maximum number of results
        group_by_provider: Return models organized by provider instead of flat list

    Returns:
        Either flat list or grouped structure based on group_by_provider
    """
    try:
        from src.services.models.openrouter_fetcher import filter_models, get_model_stats

        # Use the filter function from the fetcher
        models = filter_models(
            provider=provider,
            supports_reasoning=supports_reasoning,
            supports_vision=supports_vision,
            supports_tools=supports_tools,
            is_free=is_free,
            min_context=min_context,
            search=search
        )

        # Apply limit if specified
        if limit and len(models) > limit:
            models = models[:limit]

        # Group by provider if requested
        if group_by_provider:
            grouped = {}
            for model in models:
                model_provider = model.get('provider', 'unknown')
                if model_provider not in grouped:
                    grouped[model_provider] = []
                grouped[model_provider].append(model)

            # Get provider status for additional context
            try:
                from src.core.config import get_provider_status_cache
                provider_status = get_provider_status_cache()
            except:
                provider_status = {}

            # Format response for grouped UI
            grouped_response = []
            for provider_name, provider_models in grouped.items():
                status = provider_status.get(provider_name, {})
                grouped_response.append({
                    "provider": provider_name,
                    "is_available": status.get("is_valid", False),
                    "model_count": len(provider_models),
                    "models": provider_models,
                    "display_name": provider_name.replace("_", " ").title()
                })

            # Sort by availability and model count
            grouped_response.sort(key=lambda x: (not x["is_available"], -x["model_count"]))

            return {
                "grouped": grouped_response,
                "flat": models,
                "count": len(models),
                "stats": get_model_stats()
            }

        return {
            "models": models,
            "count": len(models),
            "stats": get_model_stats()
        }

    except ImportError:
        # Fallback to legacy models.json
        try:
            models_file = Path("models.json")
            if models_file.exists():
                with open(models_file, 'r') as f:
                    models_data = json.load(f)
                    return {"models": models_data.get("models", []), "count": 0}
            return {"models": [], "count": 0}
        except Exception:
            return {"models": [], "count": 0}

    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return {"models": [], "count": 0, "error": str(e)}


@router.post("/api/models/refresh")
async def refresh_models():
    """
    Force refresh models from OpenRouter API.

    Returns:
        Status of the refresh operation
    """
    try:
        from src.services.models.openrouter_fetcher import refresh_openrouter_models

        data, was_refreshed, error = await refresh_openrouter_models(force=True)

        if error:
            return {
                "success": False,
                "error": error,
                "models_count": len(data.get("models", []))
            }

        return {
            "success": True,
            "was_refreshed": was_refreshed,
            "models_count": len(data.get("models", [])),
            "stats": data.get("stats", {})
        }

    except Exception as e:
        logger.error(f"Failed to refresh models: {e}")
        return {"success": False, "error": str(e)}


@router.get("/api/providers")
async def list_providers():
    """
    List available providers with their connection status and model counts.

    Returns:
        Dict with providers list and summary statistics
    """
    try:
        from src.core.config import get_provider_status_cache
        from src.services.models.openrouter_fetcher import get_model_stats

        # Get cached provider status
        cached_status = get_provider_status_cache()

        # Get model stats (includes by_provider counts)
        model_stats = get_model_stats()
        provider_counts = model_stats.get("by_provider", {})

        # Define all known providers
        providers = [
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "description": "350+ models, aggregated access",
                "endpoint": "https://openrouter.ai/api/v1",
                "env_var": "OPENROUTER_API_KEY",
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "GPT-4, GPT-4o, o1 models",
                "endpoint": "https://api.openai.com/v1",
                "env_var": "OPENAI_API_KEY",
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "description": "Claude 3.5, Claude 4 models",
                "endpoint": "https://api.anthropic.com/v1",
                "env_var": "ANTHROPIC_API_KEY",
            },
            {
                "id": "google",
                "name": "Google Gemini",
                "description": "Gemini Pro, Gemini Flash",
                "endpoint": "https://generativelanguage.googleapis.com/v1beta",
                "env_var": "GOOGLE_API_KEY",
            },
            {
                "id": "vibeproxy",
                "name": "VibeProxy (Local)",
                "description": "Local OAuth proxy for Google models",
                "endpoint": "http://127.0.0.1:8317/v1",
                "env_var": None,
            },
        ]

        # Enrich with status and model counts
        for provider in providers:
            status = cached_status.get(provider["id"], {})
            provider["is_available"] = status.get("is_valid", False)
            provider["status"] = status.get("status", "unknown")
            provider["key_set"] = bool(os.getenv(provider["env_var"])) if provider["env_var"] else False
            provider["model_count"] = provider_counts.get(provider["id"], 0)

        # Also include model providers from OpenRouter data
        unique_providers = set()
        for provider in providers:
            unique_providers.add(provider["id"])

        # Add any additional providers from the model data
        for provider_id, count in provider_counts.items():
            if provider_id not in unique_providers:
                providers.append({
                    "id": provider_id,
                    "name": provider_id.capitalize(),
                    "description": f"Provider with {count} models",
                    "endpoint": None,
                    "env_var": None,
                    "is_available": True,  # Available via OpenRouter
                    "status": "via_openrouter",
                    "key_set": False,
                    "model_count": count,
                })

        # Sort by model count descending
        providers.sort(key=lambda p: p["model_count"], reverse=True)

        return {"providers": providers, "total_models": model_stats.get("total", 0)}

    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        return {"providers": [], "total_models": 0, "error": str(e)}


@router.get("/api/providers/{provider_id}/test")
async def test_provider(provider_id: str):
    """
    Test connection to a specific provider.

    Returns:
        Connection test result with model count if successful
    """
    # Provider endpoint mapping
    endpoints = {
        "openrouter": "https://openrouter.ai/api/v1",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "google": "https://generativelanguage.googleapis.com/v1beta/openai",
        "vibeproxy": "http://127.0.0.1:8317/v1",
    }

    env_vars = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    endpoint = endpoints.get(provider_id)
    if not endpoint:
        return {"success": False, "error": f"Unknown provider: {provider_id}"}

    env_var = env_vars.get(provider_id)
    api_key = os.getenv(env_var) if env_var else "dummy"

    if not api_key and provider_id != "vibeproxy":
        return {"success": False, "error": f"No API key set ({env_var})"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{endpoint}/models",
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    model_count = len(data.get("data", []))
                except:
                    model_count = 0

                return {
                    "success": True,
                    "status": "connected",
                    "models_available": model_count
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Invalid API key (401)"}
            elif response.status_code == 403:
                return {"success": False, "error": "Insufficient permissions (403)"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

    except httpx.TimeoutException:
        return {"success": False, "error": "Connection timeout"}
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to provider"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/routing/auto")
async def get_auto_routing_config(provider: str):
    """
    Get automatic routing configuration for a provider.

    When a user selects a provider, this returns the recommended:
    - Base URL
    - Model tier recommendations
    - Any special settings

    This eliminates manual "select API backend" dialogs.
    """
    routing_configs = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "recommended_big": "anthropic/claude-3.5-sonnet",
            "recommended_middle": "openai/gpt-4o",
            "recommended_small": "google/gemini-2.0-flash-exp",
            "special_notes": "Uses OPENROUTER_API_KEY - routes to 350+ models",
            "auto_config": True
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "recommended_big": "gpt-4o",
            "recommended_middle": "gpt-4o-mini",
            "recommended_small": "gpt-4o-mini",
            "special_notes": "Uses OPENAI_API_KEY - direct OpenAI access",
            "auto_config": True
        },
        "anthropic": {
            "base_url": "https://api.anthropic.com/v1",
            "recommended_big": "claude-3-5-sonnet-20241022",
            "recommended_middle": "claude-3-5-sonnet-20241022",
            "recommended_small": "claude-3-haiku-20240307",
            "special_notes": "Uses ANTHROPIC_API_KEY - direct Anthropic access",
            "auto_config": True
        },
        "google": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "recommended_big": "gemini-1.5-pro",
            "recommended_middle": "gemini-1.5-flash",
            "recommended_small": "gemini-1.5-flash",
            "special_notes": "Uses GOOGLE_API_KEY - Google AI Studio",
            "auto_config": True
        },
        "vibeproxy": {
            "base_url": "http://127.0.0.1:8317/v1",
            "recommended_big": "gemini-claude-opus-4-5-thinking",
            "recommended_middle": "gemini-3-pro-preview",
            "recommended_small": "mimo-v2-flash:free",
            "special_notes": "Local OAuth proxy - no API key needed for some models",
            "auto_config": True
        }
    }

    config = routing_configs.get(provider.lower())
    if not config:
        return {"error": "Unknown provider", "auto_config": False}

    # Get current config to show what will be overwritten
    current_config = {
        "openai_api_key": "***" if config.openai_api_key else "",
        "openai_base_url": config.openai_base_url,
        "big_model": config.big_model,
        "middle_model": config.middle_model,
        "small_model": config.small_model
    } if hasattr(config, 'openai_api_key') else {}

    return {
        "provider": provider,
        "routing": config,
        "current": current_config,
        "status": "ready"
    }


@router.post("/api/routing/apply")
async def apply_auto_routing(provider: str):
    """
    Apply automatic routing configuration for a provider.

    This eliminates the need for manual backend selection dialogs
    and automatically configures the system for the selected provider.
    """
    try:
        from src.core.config import config

        # Get the routing configuration
        routing_response = await get_auto_routing_config(provider)
        if "error" in routing_response:
            raise HTTPException(status_code=400, detail=routing_response["error"])

        routing = routing_response["routing"]

        # Apply the configuration
        config.openai_base_url = routing["base_url"]
        config.big_model = routing["recommended_big"]
        config.middle_model = routing["recommended_middle"]
        config.small_model = routing["recommended_small"]

        # Clear tier-specific endpoints (use default)
        config.enable_big_endpoint = False
        config.enable_middle_endpoint = False
        config.enable_small_endpoint = False
        config.big_endpoint = ""
        config.middle_endpoint = ""
        config.small_endpoint = ""

        # Set default provider for tracking
        config.default_provider = provider.lower()

        logger.info(f"Auto-routed to {provider}: {routing['base_url']}")

        return {
            "success": True,
            "message": f"Automatically configured for {provider}",
            "applied": {
                "base_url": routing["base_url"],
                "big_model": routing["recommended_big"],
                "middle_model": routing["recommended_middle"],
                "small_model": routing["recommended_small"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to apply auto routing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/config/api-key")
async def save_api_key(provider: str, api_key: str):
    """
    Save API key for a specific provider.

    Args:
        provider: Provider name (openrouter, openai, anthropic, google)
        api_key: API key to save
    """
    try:
        import os
        import dotenv

        # Map provider to environment variable
        env_vars = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY"
        }

        env_var = env_vars.get(provider.lower())
        if not env_var:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        # Update environment variable
        os.environ[env_var] = api_key

        # Update config object
        from src.core.config import config
        if provider.lower() == "openrouter" or provider.lower() == "openai":
            config.openai_api_key = api_key
        elif provider.lower() == "anthropic":
            config.anthropic_api_key = api_key

        # Update .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            content = env_file.read_text()
            # Update or add the key
            lines = content.split('\n')
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={api_key}"
                    updated = True
                    break
            if not updated:
                lines.append(f"{env_var}={api_key}")
            env_file.write_text('\n'.join(lines))

        logger.info(f"Updated API key for {provider}")
        return {
            "success": True,
            "message": f"API key saved for {getProviderDisplayName(provider)}",
            "env_var": env_var
        }

    except Exception as e:
        logger.error(f"Failed to save API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function for display names
def getProviderDisplayName(provider: str):
    names = {
        "openrouter": "OpenRouter",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
        "vibeproxy": "VibeProxy"
    }
    return names.get(provider.lower(), provider)


@router.get("/api/stats")
async def get_stats():
    """Get proxy statistics"""
    try:
        # Try to get stats from src.services.models.model_filter import get_available_models
        from src.services.usage.usage_tracker import usage_tracker

        if usage_tracker.enabled:
            # Get today's stats
            summary = usage_tracker.get_cost_summary(days=1)

            # Get recent requests
            recent = []
            with usage_tracker.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT original_model, input_tokens + output_tokens as total_tokens,
                           duration_ms, estimated_cost, timestamp, status
                    FROM api_requests
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)

                for row in cursor:
                    recent.append({
                        "model": row[0],
                        "tokens": row[1],
                        "duration": int(row[2]),
                        "cost": f"{row[3]:.4f}",
                        "timestamp": row[4],
                        "status": row[5]
                    })

            return {
                "requests_today": summary.get("total_requests", 0),
                "total_tokens": summary.get("total_tokens", 0),
                "est_cost": summary.get("total_cost", 0),
                "avg_latency": int(summary.get("avg_duration_ms", 0)),
                "recent_requests": recent
            }
        else:
            # Return empty stats if tracking is disabled
            return {
                "requests_today": 0,
                "total_tokens": 0,
                "est_cost": 0,
                "avg_latency": 0,
                "recent_requests": []
            }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "requests_today": 0,
            "total_tokens": 0,
            "est_cost": 0,
            "avg_latency": 0,
            "recent_requests": []
        }



@router.get("/api/stats/requests")
async def get_recent_requests():
    """Get recent requests list for dashboard"""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        
        if not usage_tracker.enabled:
            return []
            
        recent = []
        with usage_tracker.get_connection() as conn:
            cursor = conn.execute("""
                SELECT original_model, input_tokens + output_tokens as total_tokens,
                       duration_ms, estimated_cost, timestamp, status, endpoint, request_id
                FROM api_requests
                ORDER BY timestamp DESC
                LIMIT 50
            """)
            
            for row in cursor:
                recent.append({
                    "model": row[0],
                    "tokens": row[1],
                    "duration": int(row[2]),
                    "cost": f"{row[3]:.4f}",
                    "timestamp": row[4],
                    "status": row[5],
                    "endpoint": row[6],
                    "id": row[7]
                })
        return recent

    except Exception as e:
        logger.error(f"Failed to get recent requests: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED ANALYTICS & VISUALIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/analytics/dashboard")
async def get_dashboard_analytics(days: int = 7):
    """
    Get comprehensive analytics data for dashboard visualization.

    Returns:
        - Summary metrics
        - Time series data (tokens, cost, requests over time)
        - Model comparison stats
        - Savings achieved through routing
        - Token breakdown (prompt/ completion/ reasoning)
        - Provider statistics
    """
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return {
                "enabled": False,
                "message": "Usage tracking is disabled. Set TRACK_USAGE=true to enable.",
                "data": {}
            }

        data = usage_tracker.get_dashboard_summary(days)

        # Add model metadata from enriched data if available
        try:
            from src.services.models.openrouter_enricher import enrich_model
            import json
            from pathlib import Path

            enriched_path = Path(__file__).parent.parent.parent / "data" / "openrouter_models_enriched.json"
            if enriched_path.exists():
                with open(enriched_path, 'r') as f:
                    enriched_data = json.load(f)
                    model_metadata = {}
                    for model in enriched_data.get('models', []):
                        model_metadata[model['id']] = {
                            "name": model.get('name'),
                            "provider": model.get('provider'),
                            "pricing": model.get('pricing'),
                            "capabilities": {
                                "tools": model.get('supports_tools', False),
                                "vision": model.get('supports_vision', False),
                                "reasoning": model.get('supports_reasoning', False),
                                "audio": model.get('supports_audio', False)
                            },
                            "context_length": model.get('context_length', 0)
                        }
                    data["model_metadata"] = model_metadata
        except Exception:
            pass  # Metadata is optional

        return {
            "enabled": True,
            "days": days,
            "data": data
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        return {
            "enabled": False,
            "error": str(e),
            "data": {}
        }


@router.get("/api/analytics/time-series")
async def get_time_series_analytics(days: int = 14):
    """Get time-series data for line charts."""
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return {"dates": [], "tokens": [], "cost": [], "requests": []}

        return usage_tracker.get_time_series_data(days)

    except Exception as e:
        logger.error(f"Failed to get time series: {e}")
        return {"dates": [], "tokens": [], "cost": [], "requests": []}


@router.get("/api/analytics/model-comparison")
async def get_model_comparison_analytics(days: int = 14):
    """Get comparative data for different models."""
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return []

        return usage_tracker.get_model_comparison(days)

    except Exception as e:
        logger.error(f"Failed to get model comparison: {e}")
        return []


@router.get("/api/analytics/savings")
async def get_savings_analytics(days: int = 14):
    """Get savings achieved through smart routing."""
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return []

        return usage_tracker.get_savings_data(days)

    except Exception as e:
        logger.error(f"Failed to get savings data: {e}")
        return []


@router.get("/api/analytics/token-breakdown")
async def get_token_breakdown_analytics(days: int = 14):
    """Get detailed token breakdown statistics."""
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return {}

        return usage_tracker.get_token_breakdown_stats(days)

    except Exception as e:
        logger.error(f"Failed to get token breakdown: {e}")
        return {}


@router.get("/api/analytics/providers")
async def get_provider_analytics(days: int = 14):
    """Get provider-level statistics."""
    try:
        from src.services.usage.usage_tracker import usage_tracker

        if not usage_tracker.enabled:
            return []

        return usage_tracker.get_provider_stats(days)

    except Exception as e:
        logger.error(f"Failed to get provider stats: {e}")
        return []


@router.get("/api/analytics/export")
async def export_analytics(format: str = "json", days: int = 30):
    """Export usage data to JSON or CSV format."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        import tempfile
        import os

        if not usage_tracker.enabled:
            return {"success": False, "error": "Usage tracking disabled"}

        # Create temp file
        suffix = ".json" if format == "json" else ".csv"
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)

        try:
            if format == "json":
                success = usage_tracker.export_to_json(path, days)
            else:
                success = usage_tracker.export_to_csv(path, days)

            if success:
                # Read and return content
                with open(path, 'r') as f:
                    content = f.read()

                # Clean up
                os.unlink(path)

                return {
                    "success": True,
                    "format": format,
                    "content": content,
                    "message": f"Exported {days} days of data in {format.upper()} format"
                }
            else:
                os.unlink(path)
                return {"success": False, "error": "Export failed"}

        except Exception as e:
            if os.path.exists(path):
                os.unlink(path)
            raise e

    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")
        return {"success": False, "error": str(e)}


@router.post("/api/analytics/refresh-models")
async def refresh_model_metadata():
    """Manually refresh the OpenRouter model metadata cache."""
    try:
        from src.services.models.openrouter_fetcher import fetch_and_cache_models
        import asyncio

        result = await fetch_and_cache_models()
        return {
            "success": True,
            "models_fetched": len(result.get('models', [])),
            "message": "Model metadata refreshed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to refresh models: {e}")
        return {"success": False, "error": str(e)}


@router.get("/api/analytics/health")
async def get_analytics_health():
    """Check if analytics data is being collected properly."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        import sqlite3

        if not usage_tracker.enabled:
            return {
                "enabled": False,
                "message": "Usage tracking disabled",
                "data_available": False
            }

        # Check what tables have data
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM api_requests")
        api_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM daily_model_stats")
        daily_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM savings_tracking")
        savings_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM token_breakdown")
        breakdown_count = cursor.fetchone()[0]

        conn.close()

        return {
            "enabled": True,
            "data_available": api_count > 0,
            "tables": {
                "api_requests": api_count,
                "daily_model_stats": daily_count,
                "savings_tracking": savings_count,
                "token_breakdown": breakdown_count
            },
            "health": "healthy" if api_count > 0 else "no_data"
        }

    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "enabled": False,
            "error": str(e),
            "health": "error"
        }


@router.post("/api/test-connection")
async def test_provider_connection():
    """Test connection to the configured provider"""
    try:
        provider_url = os.getenv("PROVIDER_BASE_URL") or config.openai_base_url
        provider_key = os.getenv("PROVIDER_API_KEY") or config.openai_api_key

        if not provider_url or not provider_key:
            return {
                "success": False,
                "error": "Provider URL or API key not configured"
            }

        # Test by calling the /models endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{provider_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {provider_key}"}
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "provider": provider_url
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid API key (401 Unauthorized)"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "API key valid but insufficient permissions (403 Forbidden)"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unexpected response: {response.status_code}"
                }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Connection timeout - provider may be slow or unreachable"
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Cannot connect to provider - check URL"
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CROSSTALK API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

CROSSTALK_PRESETS_DIR = Path("configs/crosstalk/presets")
CROSSTALK_SESSIONS_DIR = Path("configs/crosstalk/sessions")


@router.get("/api/crosstalk/presets")
async def list_crosstalk_presets():
    """List available Crosstalk presets"""
    try:
        presets = []
        if CROSSTALK_PRESETS_DIR.exists():
            for preset_file in CROSSTALK_PRESETS_DIR.glob("*.json"):
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                    presets.append({
                        "filename": preset_file.stem,
                        "name": preset_data.get("name", preset_file.stem),
                        "description": preset_data.get("description", ""),
                        "models": len(preset_data.get("models", [])),
                        "topology": preset_data.get("topology", {}).get("type", "ring")
                    })
        return presets
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        return []


@router.get("/api/crosstalk/presets/{preset_name}")
async def get_crosstalk_preset(preset_name: str):
    """Get a specific Crosstalk preset"""
    try:
        preset_file = CROSSTALK_PRESETS_DIR / f"{preset_name}.json"
        if not preset_file.exists():
            raise HTTPException(status_code=404, detail="Preset not found")
        
        with open(preset_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Preset not found")
    except Exception as e:
        logger.error(f"Failed to load preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CrosstalkSessionCreate(BaseModel):
    """Crosstalk session configuration"""
    name: Optional[str] = None
    models: List[Dict[str, Any]]
    topology: Dict[str, Any] = {"type": "ring"}
    paradigm: str = "relay"
    rounds: int = 5
    infinite: bool = False
    stop_conditions: Dict[str, Any] = {}
    summarize_every: int = 0
    initial_prompt: str = ""


@router.post("/api/crosstalk/presets")
async def save_crosstalk_preset(preset: CrosstalkSessionCreate):
    """Save a Crosstalk preset"""
    try:
        CROSSTALK_PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        
        name = preset.name or f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        preset_file = CROSSTALK_PRESETS_DIR / f"{name}.json"
        
        preset_data = {
            "name": name,
            "models": preset.models,
            "topology": preset.topology,
            "paradigm": preset.paradigm,
            "rounds": preset.rounds,
            "infinite": preset.infinite,
            "stop_conditions": preset.stop_conditions,
            "summarize_every": preset.summarize_every,
            "initial_prompt": preset.initial_prompt
        }
        
        with open(preset_file, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {"status": "success", "filename": name}
    except Exception as e:
        logger.error(f"Failed to save preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/crosstalk/sessions")
async def list_crosstalk_sessions():
    """List recent Crosstalk sessions"""
    try:
        sessions = []
        if CROSSTALK_SESSIONS_DIR.exists():
            for session_file in sorted(CROSSTALK_SESSIONS_DIR.glob("*.json"), reverse=True)[:20]:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    sessions.append({
                        "filename": session_file.stem,
                        "started_at": session_data.get("started_at", ""),
                        "ended_at": session_data.get("ended_at", ""),
                        "messages": len(session_data.get("messages", [])),
                        "paradigm": session_data.get("config", {}).get("paradigm", "relay")
                    })
        return sessions
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return []


@router.get("/api/crosstalk/sessions/{session_name}")
async def get_crosstalk_session(session_name: str):
    """Get a specific Crosstalk session transcript"""
    try:
        session_file = CROSSTALK_SESSIONS_DIR / f"{session_name}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        with open(session_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CrosstalkRunRequest(BaseModel):
    """Request to run a crosstalk session"""
    models: list = []
    topology: dict = {}
    paradigm: str = "relay"
    rounds: int = 5
    infinite: bool = False
    stop_conditions: dict = {}
    initial_prompt: str = ""
    summarize_every: int = 0
    checkpoint_every: int = 0
    final_round_vote: dict = {}


@router.post("/api/crosstalk/run")
async def run_crosstalk_session(request: CrosstalkRunRequest):
    """Run a Crosstalk session from the web UI"""
    import asyncio
    from datetime import datetime
    
    try:
        # Validate minimum requirements
        if not request.initial_prompt:
            raise HTTPException(status_code=400, detail="Initial prompt is required")
        if len(request.models) < 2:
            raise HTTPException(status_code=400, detail="At least 2 models required")
        
        # Generate session ID
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build session config for the engine
        session_config = {
            "session_id": session_id,
            "models": request.models,
            "topology": request.topology,
            "paradigm": request.paradigm,
            "rounds": request.rounds,
            "infinite": request.infinite,
            "stop_conditions": request.stop_conditions,
            "initial_prompt": request.initial_prompt,
            "messages": []
        }
        
        # For now, return the session config (real engine integration would be async)
        # Save session file
        CROSSTALK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = CROSSTALK_SESSIONS_DIR / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_config, f, indent=2)
        
        return {
            "status": "created",
            "session_id": session_id,
            "message": "Session created. Use CLI for full execution: python start_proxy.py --crosstalk-studio",
            "config": session_config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run crosstalk session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/health")
async def health_check():
    """Health check endpoint for auto-wizard"""
    provider_url = os.getenv("PROVIDER_BASE_URL") or config.openai_base_url
    provider_key = os.getenv("PROVIDER_API_KEY") or config.openai_api_key
    
    return {
        "status": "ok",
        "provider_configured": bool(provider_key),
        "provider_url": provider_url,
        "cascade_enabled": getattr(config, 'model_cascade', False),
        "big_model": config.big_model,
        "middle_model": config.middle_model,
        "small_model": config.small_model
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL PLAYGROUND
# ═══════════════════════════════════════════════════════════════════════════════

class PlaygroundRequest(BaseModel):
    """Model playground request"""
    model_tier: str = "big"  # "big", "middle", "small"
    system_prompt: str = ""
    user_message: str
    temperature: float = 0.7
    max_tokens: int = 1024


@router.post("/api/playground/run")
async def run_playground(request: PlaygroundRequest):
    """
    Run a test prompt through the proxy.
    
    Returns the model response with token counts and latency.
    """
    import time
    
    # Get model based on tier
    model_map = {
        "big": config.big_model,
        "middle": config.middle_model,
        "small": config.small_model
    }
    model = model_map.get(request.model_tier, config.big_model)
    
    if not model:
        raise HTTPException(status_code=400, detail=f"No model configured for tier: {request.model_tier}")
    
    # Get API key
    api_key = os.getenv("PROVIDER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="No API key configured")
    
    # Build messages
    messages = []
    if request.system_prompt:
        messages.append({"role": "system", "content": request.system_prompt})
    messages.append({"role": "user", "content": request.user_message})
    
    # Call API
    base_url = config.openai_base_url or "https://openrouter.ai/api/v1"
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "latency_ms": latency_ms
                }
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            
            return {
                "success": True,
                "content": content,
                "model": model,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "latency_ms": latency_ms
            }
            
    except Exception as e:
        logger.error(f"Playground error: {e}")
        return {
            "success": False,
            "error": str(e),
            "latency_ms": int((time.time() - start_time) * 1000)
        }

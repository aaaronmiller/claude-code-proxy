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
async def list_models():
    """List available models from models database"""
    try:
        models_file = Path("models.json")
        if not models_file.exists():
            return []

        with open(models_file, 'r') as f:
            models_data = json.load(f)
            return models_data.get("models", [])

    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return []


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

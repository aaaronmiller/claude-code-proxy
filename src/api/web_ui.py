"""Web UI and Configuration API endpoints"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.config import config
from src.core.logging import logger

router = APIRouter()

# Profile storage path
PROFILES_DIR = Path("configs/profiles")
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


class ConfigUpdate(BaseModel):
    """Configuration update model"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    big_model: Optional[str] = None
    middle_model: Optional[str] = None
    small_model: Optional[str] = None
    reasoning_effort: Optional[str] = None
    reasoning_max_tokens: Optional[str] = None
    track_usage: Optional[str] = None
    use_compact_logger: Optional[str] = None


class ProfileCreate(BaseModel):
    """Profile creation model"""
    name: str
    config: Dict[str, Any]


@router.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "openai_api_key": "***" if config.openai_api_key else "",
        "anthropic_api_key": "***" if config.anthropic_api_key else "",
        "openai_base_url": config.openai_base_url,
        "big_model": config.big_model,
        "middle_model": config.middle_model,
        "small_model": config.small_model,
        "reasoning_effort": config.reasoning_effort if hasattr(config, 'reasoning_effort') else "",
        "reasoning_max_tokens": config.reasoning_max_tokens if hasattr(config, 'reasoning_max_tokens') else "",
        "track_usage": os.getenv("TRACK_USAGE", "false"),
        "use_compact_logger": os.getenv("USE_COMPACT_LOGGER", "false"),
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
        # Try to get stats from usage tracker if enabled
        from src.utils.usage_tracker import usage_tracker

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

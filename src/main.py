from fastapi import FastAPI
from src.api.endpoints import router as api_router
import uvicorn
import sys
import os
from src.core.config import config

app = FastAPI(title="Claude-to-OpenAI API Proxy", version="1.0.0")

app.include_router(api_router)


def main(env_updates: dict = None):
    """Main entry point with optional environment updates."""
    # Apply environment updates from CLI
    if env_updates:
        for key, value in env_updates.items():
            # Remove CLAUDE_ prefix and set as environment variable
            env_key = key.replace('CLAUDE_', '')
            os.environ[env_key] = value

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claude-to-OpenAI API Proxy v1.0.0")
        print("")
        print("Usage: python src/main.py")
        print("")
        print("Required environment variables:")
        print("  OPENAI_API_KEY - Your OpenAI API key")
        print("")
        print("Optional environment variables:")
        print("  ANTHROPIC_API_KEY - Expected Anthropic API key for client validation")
        print("                      If set, clients must provide this exact API key")
        print(
            f"  OPENAI_BASE_URL - OpenAI API base URL (default: https://api.openai.com/v1)"
        )
        print(f"  BIG_MODEL - Model for opus requests (default: gpt-4o)")
        print(f"  MIDDLE_MODEL - Model for sonnet requests (default: gpt-4o)")
        print(f"  SMALL_MODEL - Model for haiku requests (default: gpt-4o-mini)")
        print(f"  HOST - Server host (default: 0.0.0.0)")
        print(f"  PORT - Server port (default: 8082)")
        print(f"  LOG_LEVEL - Logging level (default: WARNING)")
        print(f"  MAX_TOKENS_LIMIT - Token limit (default: 4096)")
        print(f"  MIN_TOKENS_LIMIT - Minimum token limit (default: 100)")
        print(f"  REQUEST_TIMEOUT - Request timeout in seconds (default: 90)")
        print("")
        print("Model mapping:")
        print(f"  Claude haiku models -> {config.small_model}")
        print(f"  Claude sonnet/opus models -> {config.big_model}")
        sys.exit(0)

    # Update model limits from OpenRouter
    print("🔄 Updating model limits from OpenRouter...")
    try:
        import asyncio
        from pathlib import Path
        import json
        
        # Import scraper function
        scraper_path = Path(__file__).parent.parent / "scripts" / "scrape_openrouter_models.py"
        sys.path.insert(0, str(scraper_path.parent))
        
        from scrape_openrouter_models import fetch_openrouter_models, parse_model_limits
        
        # Run scraper
        models = asyncio.run(fetch_openrouter_models())
        if models:
            model_limits = []
            for model in models:
                limits = parse_model_limits(model)
                if limits["model_id"] and limits["context_limit"] > 0:
                    model_limits.append(limits)
            
            # Save JSON
            models_dir = Path(__file__).parent.parent / "models"
            models_dir.mkdir(exist_ok=True)
            json_path = models_dir / "model_limits.json"
            
            json_data = {
                item["model_id"]: {
                    "context": item["context_limit"],
                    "output": item["output_limit"],
                    "name": item["name"]
                }
                for item in model_limits
            }
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
            
            print(f"✅ Updated {len(model_limits)} model limits")
        else:
            print("⚠️  Failed to fetch models, using cached limits")
    except Exception as e:
        print(f"⚠️  Model limits update failed: {e}, using cached limits")
    
    # Display comprehensive configuration
    from src.utils.startup_display import display_startup_config
    display_startup_config(config)

    # Parse log level - extract just the first word to handle comments
    log_level = config.log_level.split()[0].lower()

    # Validate and set default if invalid
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    # Start server
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()

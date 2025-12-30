from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.endpoints import router as api_router
from src.api.web_ui import router as web_ui_router
from src.api.websocket_dashboard import router as websocket_router
from src.api.websocket_logs import router as ws_logs_router
from src.api.analytics import router as analytics_router
from src.api.billing import router as billing_router
from src.api.benchmarks import router as benchmarks_router
from src.api.users import router as users_router
from src.api.openai_endpoints import router as openai_router
import uvicorn
import sys
import os
from pathlib import Path
from src.core.config import config

app = FastAPI(title="Claude-to-OpenAI API Proxy", version="1.0.0")

# Include API routers
app.include_router(api_router)
app.include_router(openai_router)  # OpenAI-compatible endpoint for cross-IDE support
app.include_router(web_ui_router)
app.include_router(websocket_router)
app.include_router(ws_logs_router)  # Live log streaming
app.include_router(analytics_router)
app.include_router(billing_router)
app.include_router(benchmarks_router)
app.include_router(users_router)

# Mount static files for web UI
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Serve index.html at root
    @app.get("/")
    async def read_root():
        return FileResponse(str(static_dir / "index.html"))

# Serve web UI at root (This block is now redundant if the above @app.get("/") is active)
# Keeping it for now as the instruction implies it should remain, but it will be shadowed.
# If the intent was to remove the old @app.get("/") and replace it, the instruction was a bit ambiguous.
# Given the instruction structure, I'm replacing the old @app.get("/") with the new one,
# and the lines after the new @app.get("/") in the instruction seem to be a remnant of the old one.
# I will interpret the instruction as replacing the entire old @app.get("/") block with the new one.
# The lines `index_file = static_dir / "index.html"` and subsequent `if` block in the instruction
# appear to be part of the old logic that the new `@app.get("/")` is replacing.
# So, the old `@app.get("/")` block will be removed.

@app.get("/config")
async def serve_config_ui():
    """Serve the web UI at /config path for convenience"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Web UI not available"}


def main(env_updates: dict = None, skip_validation: bool = False):
    """Main entry point with optional environment updates."""
    # Apply environment updates from CLI
    if env_updates:
        for key, value in env_updates.items():
            # Remove CLAUDE_ prefix and set as environment variable
            env_key = key.replace('CLAUDE_', '')
            os.environ[env_key] = value
            
        # Reload configuration from environment variables
        config.__init__()

    # Check for dashboard flag
    enable_dashboard = "--dashboard" in sys.argv or config.enable_dashboard

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claude-to-OpenAI API Proxy v1.0.0")
        print("")
        print("Usage: python src/main.py [--dashboard]")
        print("")
        print("Options:")
        print("  --dashboard  Enable terminal dashboard with live metrics")
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
        print("Dashboard environment variables:")
        print(f"  ENABLE_DASHBOARD - Enable terminal dashboard (default: false)")
        print(f"  DASHBOARD_LAYOUT - Layout: default, compact, detailed (default: default)")
        print(f"  DASHBOARD_REFRESH - Refresh rate in seconds (default: 0.5)")
        print(f"  DASHBOARD_WATERFALL_SIZE - Completed requests to show (default: 20)")
        print(f"  TRACK_USAGE - Enable usage tracking (default: true if dashboard enabled)")
        print(f"  COMPACT_LOGGER - Reduce console noise (default: true if dashboard enabled)")
        print("")
        print("Model mapping:")
        print(f"  Claude haiku models -> {config.small_model}")
        print(f"  Claude sonnet/opus models -> {config.big_model}")
        sys.exit(0)

    # Update model limits from OpenRouter
    print("🔄 Updating model limits from OpenRouter...")
    try:
        import asyncio
        import json
        
        # Import scraper function
        scraper_path = Path(__file__).parent.parent / "scripts" / "maintenance" / "scrape_openrouter_models.py"
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
    from src.services.logging.startup_display import print_startup_banner
    from src.services.logging.compact_logger import CompactLogger
    from src.services.models.provider_detector import validate_provider_configuration
    print_startup_banner(config)

    # Validate configuration
    if not skip_validation:
        from src.core.validator import validate_config_on_startup
        validation_passed = validate_config_on_startup(strict=False)

        if not validation_passed:
            # Offer to launch wizard interactively
            print("\n💡 Configuration issues detected!")

            # Check if running in interactive terminal
            if sys.stdin.isatty() and "--no-wizard" not in sys.argv:
                try:
                    response = input("Would you like to run the setup wizard now? [Y/n]: ").strip().lower()
                    if response in ["", "y", "yes"]:
                        print("\n🧙 Launching Setup Wizard...\n")
                        from src.cli.wizard import SetupWizard
                        wizard = SetupWizard()
                        wizard.run()

                        # Reload configuration after wizard
                        print("\n🔄 Reloading configuration...")
                        from dotenv import load_dotenv
                        load_dotenv(override=True)
                        config.__init__()

                        # Re-validate
                        validation_passed = validate_config_on_startup(strict=False)
                        if not validation_passed:
                            print("\n❌ Configuration still has issues. Please check .env manually.")
                            sys.exit(1)
                    else:
                        print("\n💡 Run 'python start_proxy.py --setup' to fix configuration issues")
                        print("💡 Or use --skip-validation to bypass this check")
                        sys.exit(1)
                except (EOFError, KeyboardInterrupt):
                    print("\n\n❌ Setup cancelled.")
                    sys.exit(1)
            else:
                print("\n💡 Run 'python start_proxy.py --setup' to fix configuration issues")
                print("💡 Or use --skip-validation to bypass this check")
                sys.exit(1)

    # Parse log level - extract just the first word to handle comments
    log_level = config.log_level.split()[0].lower()

    # Validate and set default if invalid
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    # Start terminal dashboard if enabled
    if enable_dashboard:
        import threading
        from src.dashboard.terminal_dashboard import terminal_dashboard
        from src.dashboard.dashboard_hooks import dashboard_hooks

        print("\n🎨 Starting Terminal Dashboard...")
        print("   Dashboard will display live metrics and request flow")
        print("   Press Ctrl+C to stop\n")

        # Enable dashboard hooks
        dashboard_hooks.enable()

        # Start dashboard in separate thread
        dashboard_thread = threading.Thread(target=terminal_dashboard.start, daemon=True)
        dashboard_thread.start()

        # Brief delay to let dashboard initialize
        import time
        time.sleep(0.5)

    # Start server
    try:
        uvicorn.run(
            "src.main:app",
            host=config.host,
            port=config.port,
            log_level=log_level,
            reload=False,
        )
    finally:
        # Cleanup dashboard if running
        if enable_dashboard:
            terminal_dashboard.stop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Start Claude Code Proxy server."""

import sys
import os
import argparse

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Parse CLI arguments and start the proxy."""
    parser = argparse.ArgumentParser(
        description='Claude Code Proxy - Use Claude API with OpenAI-compatible providers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
✨ Usage Tips:
  → All Settings:        %(prog)s --settings
  → Configure Models:    %(prog)s --select-models
  → View Analytics:      %(prog)s --analytics
  → Health Check:        %(prog)s --doctor
  → Dry Run:             %(prog)s --dry-run
  
  → Standard Start:      %(prog)s
  → Force Setup:         %(prog)s --setup

For more details, see docs/guides/configuration.md
        """
    )

    # Create argument groups
    model_group = parser.add_argument_group('🤖 Model Configuration')
    reasoning_group = parser.add_argument_group('🧠 Reasoning & Thinking')
    server_group = parser.add_argument_group('🔌 Server Settings')
    mode_group = parser.add_argument_group('💾 Profile/Mode Management')
    crosstalk_group = parser.add_argument_group('🗣️  Crosstalk Orchestration')
    tools_group = parser.add_argument_group('🛠️  Interactive Tools & Config')
    validation_group = parser.add_argument_group('✅ Validation & Diagnostics')

    # Model arguments
    model_group.add_argument('--big-model', dest='big_model', metavar='MODEL',
                       help='Model for Claude Opus requests')
    model_group.add_argument('--middle-model', dest='middle_model', metavar='MODEL',
                       help='Model for Claude Sonnet requests')
    model_group.add_argument('--small-model', dest='small_model', metavar='MODEL',
                       help='Model for Claude Haiku requests')
    model_group.add_argument('--select-models', action='store_true',
                       help='Launch interactive model selector')
    model_group.add_argument('--model-cascade', dest='model_cascade', action='store_true',
                       help='Enable model cascade fallback on provider errors')

    # Reasoning arguments
    reasoning_group.add_argument('--reasoning-effort', dest='reasoning_effort',
                       choices=['low', 'medium', 'high'],
                       help='Reasoning effort level (low, medium, high)')
    reasoning_group.add_argument('--verbosity', dest='verbosity',
                       help='Response verbosity level')
    reasoning_group.add_argument('--reasoning-exclude', dest='reasoning_exclude',
                       choices=['true', 'false'],
                       help='Whether to exclude reasoning tokens from response')

    # Server arguments
    server_group.add_argument('--host', dest='host', metavar='HOST',
                       help='Server host (default: 0.0.0.0)')
    server_group.add_argument('--port', dest='port', type=int, metavar='PORT',
                       help='Server port (default: 8082)')
    server_group.add_argument('--log-level', dest='log_level',
                       choices=['debug', 'info', 'warning', 'error', 'critical'],
                       help='Logging level')

    # Mode arguments
    mode_group.add_argument('--list-modes', action='store_true',
                       help='List all saved modes')
    mode_group.add_argument('--load-mode', dest='load_mode', metavar='ID/NAME',
                       help='Load a saved mode (ID or name)')
    mode_group.add_argument('--save-mode', dest='save_mode', metavar='NAME',
                       help='Save current configuration as a mode')
    mode_group.add_argument('--delete-mode', dest='delete_mode', metavar='ID/NAME',
                       help='Delete a saved mode')
    mode_group.add_argument('--mode', dest='mode_name', metavar='NAME',
                       help='Shorthand for --save-mode')

    # Crosstalk options
    crosstalk_group.add_argument('--crosstalk-studio', action='store_true',
                       help='Launch Crosstalk Studio TUI (visual multi-model chat)')
    crosstalk_group.add_argument('--crosstalk-init', action='store_true',
                       help='Launch interactive crosstalk setup wizard')
    crosstalk_group.add_argument('--crosstalk', dest='crosstalk_models',
                       help='Quick setup (comma-separated models)')
    crosstalk_group.add_argument('--system-prompt-big', dest='big_system_prompt',
                       help='System prompt for BIG model')
    crosstalk_group.add_argument('--system-prompt-middle', dest='middle_system_prompt',
                       help='System prompt for MIDDLE model')
    crosstalk_group.add_argument('--system-prompt-small', dest='small_system_prompt',
                       help='System prompt for SMALL model')
    crosstalk_group.add_argument('--crosstalk-iterations', dest='crosstalk_iterations', type=int,
                       help='Number of iterations (default: 20)')
    crosstalk_group.add_argument('--crosstalk-topic', dest='crosstalk_topic',
                       help='Initial topic')
    crosstalk_group.add_argument('--crosstalk-paradigm', dest='crosstalk_paradigm',
                       choices=['memory', 'report', 'relay', 'debate'],
                       help='Communication paradigm')

    # Interactive Tools
    tools_group.add_argument('--setup', action='store_true',
                       help='Launch first-time setup wizard')
    tools_group.add_argument('--configure-prompts', action='store_true',
                       help='Launch prompt injection configurator')
    tools_group.add_argument('--configure-terminal', action='store_true',
                       help='Launch terminal output configurator')
    tools_group.add_argument('--configure-dashboard', action='store_true',
                       help='Launch dashboard module configurator')
    tools_group.add_argument('--analytics', action='store_true',
                       help='View usage analytics')
    tools_group.add_argument('--settings', action='store_true',
                       help='Launch unified settings TUI (models, terminal, dashboard, prompts)')
    tools_group.add_argument('--doctor', action='store_true',
                       help='Run health check and auto-fix common issues')
    tools_group.add_argument('--configure-advanced', action='store_true',
                       help='Launch advanced configuration TUI (reasoning, prompts, hybrid mode)')
    tools_group.add_argument('--fix-keys', action='store_true',
                       help='(Deprecated, use --doctor) Launch API key repair wizard')
    
    # Quick Model Configuration
    model_config_group = parser.add_argument_group('⚡ Quick Model Setup')
    model_config_group.add_argument('--set-big', metavar='MODEL',
                       help='Quick set BIG model (e.g., vibeproxy/gemini-opus)')
    model_config_group.add_argument('--set-middle', metavar='MODEL',
                       help='Quick set MIDDLE model (e.g., vibeproxy/gemini-pro-3)')
    model_config_group.add_argument('--set-small', metavar='MODEL',
                       help='Quick set SMALL model (e.g., openrouter/gpt-4o-mini)')
    model_config_group.add_argument('--show-models', action='store_true',
                       help='Show available models from all configured endpoints')
    model_config_group.add_argument('--check-endpoints', action='store_true',
                       help='Check endpoint connectivity and API key validity')
    model_config_group.add_argument('--update-models', action='store_true',
                       help='Scrape latest model stats (pricing, limits) from providers')
    model_config_group.add_argument('--rank-models', action='store_true',
                       help='AI-rank free models for coding capability')


    # Validation & Diagnostics
    validation_group.add_argument('--config', dest='show_config', action='store_true',
                       help='Show current configuration and exit')
    validation_group.add_argument('--validate-config', action='store_true',
                       help='Validate configuration and exit')
    validation_group.add_argument('--skip-validation', action='store_true',
                       help='Skip configuration validation on startup')
    validation_group.add_argument('--dry-run', action='store_true',
                       help='Validate config and check readiness without starting server')
    validation_group.add_argument('--client', action='store_true',
                       help='Run as client wrapper (internal use)')

    args, unknown = parser.parse_known_args() # Use parse_known_args to allow passing args to client

    # Handle unified settings TUI
    if args.settings:
        from src.cli.settings import main as settings_main
        settings_main()
        return

    # Handle crosstalk-studio (visual TUI)
    if getattr(args, 'crosstalk_studio', False):
        from src.cli.crosstalk_studio import main as crosstalk_main
        crosstalk_main()
        return

    # Handle doctor (health check + auto-fix)
    if args.doctor or args.fix_keys:
        from src.cli.fix_keys import main as fix_keys_main
        if args.fix_keys:
            print("⚠️  --fix-keys is deprecated. Use --doctor instead.")
        fix_keys_main()
        return

    # Handle advanced configuration TUI
    if getattr(args, 'configure_advanced', False):
        from src.cli.advanced_config import main as advanced_main
        advanced_main()
        return

    if args.client:
        from src.cli.client_wrapper import main as client_main
        # Pass unknown args to client wrapper (the command to run)
        client_main(unknown)
        return

    # Handle quick model configuration
    if args.set_big or args.set_middle or args.set_small:
        from src.cli.quick_config import set_model
        changes = False
        if args.set_big:
            print("\n🔧 Configuring BIG model...")
            if set_model("big", args.set_big):
                changes = True
        if args.set_middle:
            print("\n🔧 Configuring MIDDLE model...")
            if set_model("middle", args.set_middle):
                changes = True
        if args.set_small:
            print("\n🔧 Configuring SMALL model...")
            if set_model("small", args.set_small):
                changes = True
        if changes:
            print("\n💡 Restart the proxy for changes to take effect.")
        return

    # Handle show-models
    if args.show_models:
        import asyncio
        from src.cli.quick_config import show_models
        asyncio.run(show_models())
        return

    # Handle check-endpoints
    if args.check_endpoints:
        import asyncio
        from src.cli.quick_config import check_endpoints
        asyncio.run(check_endpoints())
        return

    # Handle update-models (scrape latest stats)
    if args.update_models:
        import asyncio
        from src.services.models.scrape_model_stats import update_model_database, get_scraper_model
        print(f"🤖 Using model: {get_scraper_model()}")
        print("   (Set SCRAPER_MODEL env var to use a different model)")
        asyncio.run(update_model_database("openrouter"))
        return

    # Handle rank-models (AI-powered coding model ranking)
    if args.rank_models:
        import asyncio
        from src.services.models.model_ranker import update_rankings, get_ranker_model
        print(f"🤖 Using model: {get_ranker_model()}")
        print("   (Set RANKER_MODEL env var to use a different model)")
        asyncio.run(update_rankings())
        return

    # Handle validation check
    if args.validate_config:
        from src.core.validator import validate_config_on_startup
        passed = validate_config_on_startup(strict=False)
        sys.exit(0 if passed else 1)

    # Handle --config (show config and exit)
    if args.show_config:
        from src.core.config import Config
        from src.services.logging.startup_display import display_startup_config
        config = Config()
        display_startup_config(config)
        sys.exit(0)

    # Handle dry-run (validate without starting)
    if args.dry_run:
        from src.core.config import Config
        import socket

        print("\n🔍 Dry Run - Checking configuration...\n")
        
        config = Config()
        issues = []
        
        # Check API key
        if config.openai_api_key and "dummy" not in config.openai_api_key:
            key_preview = config.openai_api_key[:8] + "..." + config.openai_api_key[-4:]
            print(f"✓ Provider API Key: {key_preview}")
        else:
            issues.append("No valid API key configured")
            print("✗ Provider API Key: Not configured")
        
        # Check base URL
        print(f"✓ Provider URL: {config.openai_base_url}")
        
        # Check models
        print(f"✓ Big Model: {config.big_model}")
        print(f"✓ Middle Model: {config.middle_model}")
        print(f"✓ Small Model: {config.small_model}")
        
        # Check port availability
        port = config.port
        host = config.host
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host if host != "0.0.0.0" else "127.0.0.1", port))
            sock.close()
            if result == 0:
                issues.append(f"Port {port} is already in use")
                print(f"✗ Port {port}: Already in use")
            else:
                print(f"✓ Port {port}: Available")
        except Exception as e:
            print(f"? Port {port}: Could not check ({e})")
        
        # Check features
        print(f"✓ Dashboard: {'enabled' if config.enable_dashboard else 'disabled'}")
        print(f"✓ Tracking: {'enabled' if config.track_usage else 'disabled'}")
        
        print()
        if issues:
            print(f"⚠️  Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"   - {issue}")
            print("\nRun with --doctor to attempt auto-fix.")
            sys.exit(1)
        else:
            print("✅ All checks passed. Ready to launch.")
            print("   Run without --dry-run to start the server.")
            sys.exit(0)


    # Handle setup wizard
    if args.setup:
        from src.cli.wizard import main as wizard_main
        wizard_main()
        return

    # Check for missing configuration (Auto-Wizard)
    # If no API key is set (and not explicitly skipping validation), redirect to wizard
    if not args.skip_validation:
        from src.core.config import Config
        # Initialize config to check env vars
        temp_config = Config()
        
        # Check if we have a valid provider key (not None, not empty, not placeholder)
        key = temp_config.openai_api_key
        has_key = key and "dummy" not in key and "your-" not in key
        
        # Check if passthrough mode is enabled (which is valid)
        # But Config enables passthrough if key is missing, so we need to be careful.
        # If the user explicitly set passthrough, that's fine.
        # But if it defaulted to passthrough because of missing config, we should prompt.
        
        # Actually, Config sets passthrough_mode=True if key is missing.
        # So we can't just check passthrough_mode.
        # We need to check if the user *intended* to run without config.
        # But the user request is: "detect if there is no key... and kick us to the wizard"
        
        if not has_key:
            print("\n⚠️  No Provider API Key detected!")
            print("   Redirecting to setup wizard...\n")
            try:
                from src.cli.wizard import main as wizard_main
                wizard_main()
                # After wizard, we should probably exit to let user restart with new config
                # or just return because wizard writes to .env which needs reloading
                return
            except ImportError:
                print("❌ Wizard not found. Please configure .env manually.")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error launching wizard: {e}")
                sys.exit(1)

    # Handle crosstalk operations
    # Import locally to avoid initializing OpenAI client before config check
    from src.cli.crosstalk_cli import handle_crosstalk_operations
    if handle_crosstalk_operations(args):
        return

    # Handle prompt configurator
    if args.configure_prompts:
        from src.cli.prompt_config import main as prompt_main
        prompt_main()
        return

    # Handle terminal configurator
    if args.configure_terminal:
        from src.cli.terminal_config import main as terminal_main
        terminal_main()
        return

    # Handle analytics
    if args.analytics:
        from src.cli.analytics import main as analytics_main
        analytics_main()
        return

    # Handle dashboard configurator
    if args.configure_dashboard:
        from src.cli.dashboard_config import main as dashboard_main
        dashboard_main()
        return

    # Handle model selector
    if args.select_models:
        from src.cli.model_selector import run_model_selector
        run_model_selector()
        return
    
    # Handle mode operations
    from src.services.logging.startup_display import print_startup_banner
    from src.services.models.provider_detector import validate_provider_config
    from src.services.models.modes import ModeManager
    if ModeManager.handle_mode_operations(args):
        return

    # Set environment variables from CLI args
    env_updates = {}
    skip_validation = args.skip_validation
    for key, value in vars(args).items():
        if value is not None and key not in ['show_config', 'select_models', 'validate_config', 'skip_validation']:
            env_key = key.upper().replace('-', '_')
            env_updates[f'CLAUDE_{env_key}'] = str(value)

    # Import main after handling modes
    from src.main import main as start_main
    start_main(env_updates, skip_validation=skip_validation)

if __name__ == "__main__":
    main()
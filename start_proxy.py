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
Examples:
  %(prog)s                                    # Start with .env config
  %(prog)s --big-model gpt-5 --reasoning high # Set models via CLI
  %(prog)s --list-modes                       # List saved modes
  %(prog)s --load-mode 1                      # Load saved mode
  %(prog)s --mode development                 # Save current config as mode
        """
    )

    # Model arguments
    parser.add_argument('--big-model', dest='big_model', metavar='MODEL',
                       help='Model for Claude Opus requests')
    parser.add_argument('--middle-model', dest='middle_model', metavar='MODEL',
                       help='Model for Claude Sonnet requests')
    parser.add_argument('--small-model', dest='small_model', metavar='MODEL',
                       help='Model for Claude Haiku requests')

    # Reasoning arguments
    parser.add_argument('--reasoning-effort', dest='reasoning_effort',
                       choices=['low', 'medium', 'high'],
                       help='Reasoning effort level (low, medium, high)')
    parser.add_argument('--verbosity', dest='verbosity',
                       help='Response verbosity level')
    parser.add_argument('--reasoning-exclude', dest='reasoning_exclude',
                       choices=['true', 'false'],
                       help='Whether to exclude reasoning tokens from response')

    # Server arguments
    parser.add_argument('--host', dest='host', metavar='HOST',
                       help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', dest='port', type=int, metavar='PORT',
                       help='Server port (default: 8082)')
    parser.add_argument('--log-level', dest='log_level',
                       choices=['debug', 'info', 'warning', 'error', 'critical'],
                       help='Logging level')

    # Mode arguments
    parser.add_argument('--list-modes', action='store_true',
                       help='List all saved modes')
    parser.add_argument('--load-mode', dest='load_mode', metavar='ID_OR_NAME',
                       help='Load a saved mode (ID or name)')
    parser.add_argument('--save-mode', dest='save_mode', metavar='NAME',
                       help='Save current configuration as a mode')
    parser.add_argument('--delete-mode', dest='delete_mode', metavar='ID_OR_NAME',
                       help='Delete a saved mode')
    parser.add_argument('--mode', dest='mode_name', metavar='NAME',
                       help='Shorthand for --save-mode when combined with other args')

    # Crosstalk options
    parser.add_argument('--crosstalk-init', action='store_true',
                       help='Launch interactive crosstalk setup wizard')
    parser.add_argument('--crosstalk', dest='crosstalk_models',
                       help='Quick crosstalk setup with comma-separated models (e.g., "big,small")')
    parser.add_argument('--system-prompt-big', dest='big_system_prompt',
                       help='System prompt for BIG model (file path with "path:" prefix or inline text)')
    parser.add_argument('--system-prompt-middle', dest='middle_system_prompt',
                       help='System prompt for MIDDLE model (file path with "path:" prefix or inline text)')
    parser.add_argument('--system-prompt-small', dest='small_system_prompt',
                       help='System prompt for SMALL model (file path with "path:" prefix or inline text)')
    parser.add_argument('--crosstalk-iterations', dest='crosstalk_iterations', type=int,
                       help='Number of crosstalk iterations (default: 20)')
    parser.add_argument('--crosstalk-topic', dest='crosstalk_topic',
                       help='Initial topic for crosstalk conversation')
    parser.add_argument('--crosstalk-paradigm', dest='crosstalk_paradigm',
                       choices=['memory', 'report', 'relay', 'debate'],
                       help='Crosstalk communication paradigm')

    # Other options
    parser.add_argument('--config', dest='show_config', action='store_true',
                       help='Show current configuration and exit')
    parser.add_argument('--select-models', action='store_true',
                       help='Launch interactive model selector')
    parser.add_argument('--validate-config', action='store_true',
                       help='Validate configuration and exit')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip configuration validation on startup')

    args = parser.parse_args()

    # Handle validation check
    if args.validate_config:
        from src.core.validator import validate_config_on_startup
        passed = validate_config_on_startup(strict=False)
        sys.exit(0 if passed else 1)

    # Handle crosstalk operations
    from src.cli.crosstalk_cli import handle_crosstalk_operations
    if handle_crosstalk_operations(args):
        return

    # Handle model selector
    if args.select_models:
        from src.cli.model_selector import run_model_selector
        run_model_selector()
        return
    
    # Handle mode operations
    from src.utils.modes import handle_mode_operations
    if handle_mode_operations(args):
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
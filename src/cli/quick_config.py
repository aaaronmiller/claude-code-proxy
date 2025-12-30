"""
Quick Model Configuration CLI

Provides easy commands to set models for BIG/MIDDLE/SMALL endpoints.

Usage:
    python -m src.cli.quick_config --set-big vibeproxy/gemini-opus
    python -m src.cli.quick_config --set-middle vibeproxy/gemini-pro-3
    python -m src.cli.quick_config --set-small openrouter/gpt-4o-mini
    python -m src.cli.quick_config --show-models  # Show available models from all endpoints
    python -m src.cli.quick_config --check-endpoints  # Verify API keys and connectivity
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def update_env_file(key: str, value: str) -> bool:
    """Update a key in the .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f"{key}={value}\n")
        return True
    
    # Read existing content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add the key
    key_found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        new_lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    return True


async def check_endpoints():
    """Check all configured endpoints and show their status."""
    from src.services.models.provider_models import (
        ProviderModelFetcher,
        get_top_models_per_provider,
        format_model_display
    )
    from src.core.config import config
    
    print("\n" + "=" * 70)
    print(" ENDPOINT STATUS CHECK")
    print("=" * 70)
    
    fetcher = ProviderModelFetcher()
    
    endpoints = []
    
    # Collect all endpoints
    if config.enable_big_endpoint:
        endpoints.append(("BIG", config.big_endpoint, config.big_api_key, config.big_model))
    else:
        endpoints.append(("BIG (default)", config.openai_base_url, config.openai_api_key, config.big_model))
    
    if config.enable_middle_endpoint:
        endpoints.append(("MIDDLE", config.middle_endpoint, config.middle_api_key, config.middle_model))
    else:
        endpoints.append(("MIDDLE (default)", config.openai_base_url, config.openai_api_key, config.middle_model))
    
    if config.enable_small_endpoint:
        endpoints.append(("SMALL", config.small_endpoint, config.small_api_key, config.small_model))
    else:
        endpoints.append(("SMALL (default)", config.openai_base_url, config.openai_api_key, config.small_model))
    
    for name, endpoint, api_key, model in endpoints:
        print(f"\n{name}:")
        print(f"  Endpoint: {endpoint}")
        print(f"  Model:    {model}")
        
        status = await fetcher.fetch_models(endpoint, api_key)
        
        if status.is_connected:
            if status.api_key_valid:
                print(f"  Status:   ✅ Connected ({len(status.models)} models)")
                
                # Show top 3 models
                top_models = get_top_models_per_provider(status, 3)
                if top_models:
                    print(f"  Top models:")
                    for m in top_models:
                        tag = " 🆓✨NEW" if m.is_free else ""
                        print(f"    • {m.id}{tag}")
            else:
                print(f"  Status:   ❌ Invalid API Key")
        else:
            print(f"  Status:   ❌ Connection Failed ({status.error})")
    
    await fetcher.close()
    print()


async def show_models():
    """Show available models from all configured endpoints."""
    from src.services.models.provider_models import (
        ProviderModelFetcher,
        get_top_models_per_provider,
        format_model_display
    )
    from src.core.config import config
    
    print("\n" + "=" * 70)
    print(" AVAILABLE MODELS BY ENDPOINT")
    print("=" * 70)
    
    fetcher = ProviderModelFetcher()
    
    # Unique endpoints only
    endpoints = {}
    
    if config.enable_big_endpoint and config.big_endpoint:
        endpoints[config.big_endpoint] = ("BIG", config.big_api_key)
    
    if config.enable_middle_endpoint and config.middle_endpoint:
        if config.middle_endpoint not in endpoints:
            endpoints[config.middle_endpoint] = ("MIDDLE", config.middle_api_key)
    
    if config.enable_small_endpoint and config.small_endpoint:
        if config.small_endpoint not in endpoints:
            endpoints[config.small_endpoint] = ("SMALL", config.small_api_key)
    
    if config.openai_base_url and config.openai_base_url not in endpoints:
        endpoints[config.openai_base_url] = ("DEFAULT", config.openai_api_key)
    
    for endpoint, (name, api_key) in endpoints.items():
        status = await fetcher.fetch_models(endpoint, api_key)
        
        print(f"\n─── {status.provider.upper()} ({endpoint}) ───")
        
        if not status.is_connected:
            print(f"  ❌ Not connected: {status.error}")
            continue
        
        if not status.api_key_valid:
            print(f"  ❌ Invalid API key")
            continue
        
        # Show top 10 models, prioritizing new free ones
        top_models = get_top_models_per_provider(status, 10)
        
        if not top_models:
            print("  No models available")
            continue
        
        print(f"  {'Model ID':<45} {'CTX':>6} {'OUT':>6}  {'Price'}")
        print(f"  {'-'*45} {'-'*6} {'-'*6}  {'-'*10}")
        
        for model in top_models:
            print(f"  {format_model_display(model)}")
    
    await fetcher.close()
    print()


def set_model(slot: str, model: str):
    """Set a model for a specific slot."""
    slot_upper = slot.upper()
    
    if slot_upper not in ["BIG", "MIDDLE", "SMALL"]:
        print(f"❌ Invalid slot: {slot}. Must be BIG, MIDDLE, or SMALL.")
        return False
    
    key = f"{slot_upper}_MODEL"
    
    # Check if model contains endpoint hint
    if "/" in model:
        parts = model.split("/", 1)
        endpoint_hint = parts[0].lower()
        actual_model = parts[1] if len(parts) > 1 else model
        
        # Auto-configure endpoint based on hint
        if endpoint_hint == "vibeproxy":
            update_env_file(f"ENABLE_{slot_upper}_ENDPOINT", "true")
            update_env_file(f"{slot_upper}_ENDPOINT", "http://127.0.0.1:8317/v1")
            model = actual_model
            print(f"  📡 Auto-configured {slot_upper}_ENDPOINT=http://127.0.0.1:8317/v1")
        elif endpoint_hint == "openrouter":
            update_env_file(f"ENABLE_{slot_upper}_ENDPOINT", "true")
            update_env_file(f"{slot_upper}_ENDPOINT", "https://openrouter.ai/api/v1")
            # Keep full model ID for OpenRouter
            print(f"  📡 Auto-configured {slot_upper}_ENDPOINT=https://openrouter.ai/api/v1")
        elif endpoint_hint == "openai":
            update_env_file(f"ENABLE_{slot_upper}_ENDPOINT", "true")
            update_env_file(f"{slot_upper}_ENDPOINT", "https://api.openai.com/v1")
            model = actual_model
            print(f"  📡 Auto-configured {slot_upper}_ENDPOINT=https://api.openai.com/v1")
    
    update_env_file(key, model)
    print(f"✅ Set {key}={model}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Quick Model Configuration")
    parser.add_argument("--set-big", metavar="MODEL", help="Set BIG model (e.g., vibeproxy/gemini-opus)")
    parser.add_argument("--set-middle", metavar="MODEL", help="Set MIDDLE model")
    parser.add_argument("--set-small", metavar="MODEL", help="Set SMALL model")
    parser.add_argument("--show-models", action="store_true", help="Show available models from all endpoints")
    parser.add_argument("--check-endpoints", action="store_true", help="Check endpoint connectivity and API keys")
    
    args = parser.parse_args()
    
    # Handle set commands
    changes_made = False
    
    if args.set_big:
        print(f"\n🔧 Configuring BIG model...")
        if set_model("big", args.set_big):
            changes_made = True
    
    if args.set_middle:
        print(f"\n🔧 Configuring MIDDLE model...")
        if set_model("middle", args.set_middle):
            changes_made = True
    
    if args.set_small:
        print(f"\n🔧 Configuring SMALL model...")
        if set_model("small", args.set_small):
            changes_made = True
    
    if changes_made:
        print("\n💡 Restart the proxy for changes to take effect.")
    
    # Handle show/check commands
    if args.show_models:
        asyncio.run(show_models())
    
    if args.check_endpoints:
        asyncio.run(check_endpoints())
    
    # If no args, show help
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()

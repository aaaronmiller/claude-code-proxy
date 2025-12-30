#!/usr/bin/env python3
"""
Crosstalk Runner - Programmatic API for Model-to-Model Conversations

Enables running crosstalk sessions from:
- JSON config files
- Inline configuration dictionaries
- Saved preset names

Designed for MCP integration and CLI scripting.
Returns transcript and saves to output file.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Union, Dict, Any, Optional, List
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent.parent
PRESETS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "presets"
SESSIONS_DIR = PROJECT_ROOT / "configs" / "crosstalk" / "sessions"

# Ensure directories exist
for d in [PRESETS_DIR, SESSIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_config(config_source: Union[str, Dict, Path]) -> Dict[str, Any]:
    """
    Load crosstalk configuration from various sources.
    
    Args:
        config_source: One of:
            - Path to JSON file (str or Path)
            - Preset name (str without .json)
            - Inline config dict
            
    Returns:
        Parsed configuration dictionary
    """
    if isinstance(config_source, dict):
        return config_source
    
    path = Path(config_source)
    
    # Check if it's a direct file path
    if path.exists() and path.suffix == ".json":
        with open(path) as f:
            return json.load(f)
    
    # Check presets directory
    preset_path = PRESETS_DIR / f"{config_source}.json"
    if preset_path.exists():
        with open(preset_path) as f:
            return json.load(f)
    
    # Try adding .json
    if not path.suffix:
        path = Path(f"{config_source}.json")
        if path.exists():
            with open(path) as f:
                return json.load(f)
    
    raise FileNotFoundError(f"Could not find config: {config_source}")


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate a crosstalk configuration."""
    required = ["models"]
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required key: {key}")
    
    if not config["models"]:
        raise ValueError("At least one model is required")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

async def run_from_config(
    config_source: Union[str, Dict, Path],
    output_file: Optional[str] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """
    Run a crosstalk session from configuration.
    
    Args:
        config_source: Config file path, preset name, or inline dict
        output_file: Optional path for transcript output
        stream: If True, print responses in real-time
        
    Returns:
        Dict with:
            - transcript: List of messages
            - output_file: Path to saved transcript
            - config: Configuration used
            - status: "completed" or "error"
    """
    # Load and validate config
    config = load_config(config_source)
    validate_config(config)
    
    # Import session classes
    from src.cli.crosstalk_studio import CrosstalkSession, ModelSlot, TopologyConfig, StopConditions
    
    # Build session
    models = []
    for i, m in enumerate(config.get("models", [])):
        if isinstance(m, dict):
            slot = ModelSlot(
                slot_id=m.get("slot_id", i + 1),
                model_id=m.get("model_id", "anthropic/claude-3-opus"),
                system_prompt_file=m.get("system_prompt_file", ""),
                system_prompt_inline=m.get("system_prompt_inline", ""),
                jinja_template=m.get("jinja_template", "basic"),
                temperature=m.get("temperature", 0.9),
                max_tokens=m.get("max_tokens", 4096)
            )
        else:
            # String model ID
            slot = ModelSlot(slot_id=i + 1, model_id=m)
        models.append(slot)
    
    # Build topology config
    topo_data = config.get("topology", {})
    topology = TopologyConfig(
        type=topo_data.get("type", "ring"),
        order=topo_data.get("order", []),
        center=topo_data.get("center", 1),
        spokes=topo_data.get("spokes", [])
    )
    
    # Build stop conditions
    stop_data = config.get("stop_conditions", {})
    stop_conditions = StopConditions(
        max_time_seconds=stop_data.get("max_time_seconds", 0),
        max_cost_dollars=stop_data.get("max_cost_dollars", 0.0),
        max_turns=stop_data.get("max_turns", 0),
        stop_keywords=stop_data.get("stop_keywords", [])
    )
    
    session = CrosstalkSession(
        models=models,
        rounds=config.get("rounds", 5),
        paradigm=config.get("paradigm", "relay"),
        topology=topology,
        initial_prompt=config.get("initial_prompt", "Begin the conversation."),
        memory_file=config.get("memory_file"),
        infinite=config.get("infinite", False),
        stop_conditions=stop_conditions,
        summarize_every=config.get("summarize_every", 0)
    )
    
    # Run the session
    from src.cli.crosstalk_engine import run_crosstalk
    
    try:
        transcript = await run_crosstalk(session)
        
        # Determine output path
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = SESSIONS_DIR / f"session_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        # Save transcript
        output_data = {
            "config": config,
            "messages": [asdict(m) for m in transcript.messages] if transcript else [],
            "started_at": transcript.started_at if transcript else "",
            "ended_at": transcript.ended_at if transcript else "",
            "status": "completed" if transcript else "error"
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        return {
            "transcript": output_data["messages"],
            "output_file": str(output_file),
            "config": config,
            "status": "completed"
        }
        
    except Exception as e:
        return {
            "transcript": [],
            "output_file": None,
            "config": config,
            "status": "error",
            "error": str(e)
        }


async def run_quick(
    models: List[str],
    prompt: str,
    rounds: int = 5,
    paradigm: str = "relay"
) -> Dict[str, Any]:
    """
    Quick crosstalk session with minimal configuration.
    
    Args:
        models: List of model IDs
        prompt: Initial prompt
        rounds: Number of rounds
        paradigm: Communication paradigm
        
    Returns:
        Same as run_from_config
    """
    config = {
        "models": [{"model_id": m} for m in models],
        "initial_prompt": prompt,
        "rounds": rounds,
        "paradigm": paradigm
    }
    return await run_from_config(config)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """CLI entry point for crosstalk runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run crosstalk sessions from configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run from preset
  python -m src.cli.crosstalk_runner --config backrooms
  
  # Run from file
  python -m src.cli.crosstalk_runner --config configs/crosstalk/presets/my_config.json
  
  # Quick run
  python -m src.cli.crosstalk_runner --quick "claude-3-opus,gemini-pro" --prompt "Explore consciousness"
  
  # With output file
  python -m src.cli.crosstalk_runner --config backrooms --output my_session.json
        """
    )
    
    parser.add_argument("--config", "-c", type=str,
                       help="Config file path or preset name")
    parser.add_argument("--output", "-o", type=str,
                       help="Output file path for transcript")
    parser.add_argument("--quick", "-q", type=str,
                       help="Quick run: comma-separated model IDs")
    parser.add_argument("--prompt", "-p", type=str, default="Begin.",
                       help="Initial prompt for quick run")
    parser.add_argument("--rounds", "-r", type=int, default=5,
                       help="Number of rounds")
    parser.add_argument("--paradigm", type=str, default="relay",
                       choices=["relay", "memory", "debate", "report"],
                       help="Communication paradigm")
    parser.add_argument("--list-presets", "-l", action="store_true",
                       help="List available presets")
    parser.add_argument("--json", "-j", action="store_true",
                       help="Output result as JSON (for MCP)")
    
    args = parser.parse_args()
    
    # List presets
    if args.list_presets:
        presets = list(PRESETS_DIR.glob("*.json"))
        if presets:
            print("Available presets:")
            for p in presets:
                print(f"  - {p.stem}")
        else:
            print("No presets found. Create one with Crosstalk Studio.")
        return
    
    # Quick run
    if args.quick:
        models = [m.strip() for m in args.quick.split(",")]
        result = asyncio.run(run_quick(
            models=models,
            prompt=args.prompt,
            rounds=args.rounds,
            paradigm=args.paradigm
        ))
    
    # Config run
    elif args.config:
        result = asyncio.run(run_from_config(
            config_source=args.config,
            output_file=args.output
        ))
    
    else:
        parser.print_help()
        return
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("status") == "completed":
            print(f"\n✅ Session completed")
            print(f"   Messages: {len(result.get('transcript', []))}")
            print(f"   Output: {result.get('output_file')}")
        else:
            print(f"\n❌ Session failed: {result.get('error')}")


if __name__ == "__main__":
    main()

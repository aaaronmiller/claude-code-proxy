"""Mode management for saving and loading configuration presets."""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime


MODES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "modes.json")


class ModeManager:
    """Manage saved configuration modes."""

    def __init__(self):
        self.modes_file = MODES_FILE
        self.modes = self._load_modes()

    def _load_modes(self) -> Dict[str, Any]:
        """Load modes from file."""
        if os.path.exists(self.modes_file):
            try:
                with open(self.modes_file, 'r') as f:
                    data = json.load(f)
                    return data.get('modes', {})
            except Exception as e:
                print(f"Warning: Could not load modes file: {e}")
        return {}

    def _save_modes(self):
        """Save modes to file."""
        try:
            with open(self.modes_file, 'w') as f:
                json.dump({
                    'modes': self.modes,
                    'version': '1.0'
                }, f, indent=2)
        except Exception as e:
            print(f"Error: Could not save modes file: {e}")
            sys.exit(1)

    def _get_available_id(self) -> str:
        """Get the next available mode ID (1-99)."""
        used_ids = set()
        for mode in self.modes.values():
            if mode.get('id'):
                used_ids.add(int(mode['id']))

        for i in range(1, 100):
            if i not in used_ids:
                return str(i)

        raise ValueError("Maximum number of modes (99) reached")

    def save_mode(self, name: str, config: Dict[str, str], mode_id: Optional[str] = None) -> bool:
        """Save a configuration as a mode."""
        if not name:
            print("Error: Mode name cannot be empty")
            return False

        # Check if name already exists
        for mode in self.modes.values():
            if mode.get('name', '').lower() == name.lower():
                print(f"Error: Mode '{name}' already exists")
                return False

        if not mode_id:
            try:
                mode_id = self._get_available_id()
            except ValueError as e:
                print(f"Error: {e}")
                return False

        # Check if ID already exists
        for existing_id, mode in self.modes.items():
            if mode.get('id') == mode_id:
                print(f"Error: Mode ID {mode_id} already exists")
                return False

        self.modes[mode_id] = {
            'id': mode_id,
            'name': name,
            'config': config,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }

        self._save_modes()
        print(f"✓ Saved mode '{name}' (ID: {mode_id})")
        return True

    def load_mode(self, identifier: str) -> Optional[Dict[str, str]]:
        """Load a mode by ID or name."""
        # Try as ID first
        if identifier in self.modes:
            mode = self.modes[identifier]
            config = mode['config']
            print(f"✓ Loaded mode '{mode['name']}' (ID: {mode['id']})")
            return config

        # Try as name (case-insensitive)
        for mode in self.modes.values():
            if mode.get('name', '').lower() == identifier.lower():
                config = mode['config']
                print(f"✓ Loaded mode '{mode['name']}' (ID: {mode['id']})")
                return config

        print(f"Error: Mode '{identifier}' not found")
        return None

    def delete_mode(self, identifier: str) -> bool:
        """Delete a mode by ID or name."""
        mode_id = None
        mode_name = None

        # Try as ID first
        if identifier in self.modes:
            mode_id = identifier
            mode_name = self.modes[identifier]['name']
        else:
            # Try as name
            for mid, mode in self.modes.items():
                if mode.get('name', '').lower() == identifier.lower():
                    mode_id = mid
                    mode_name = mode['name']
                    break

        if mode_id:
            del self.modes[mode_id]
            self._save_modes()
            print(f"✓ Deleted mode '{mode_name}' (ID: {mode_id})")
            return True

        print(f"Error: Mode '{identifier}' not found")
        return False

    def list_modes(self) -> bool:
        """List all saved modes."""
        if not self.modes:
            print("No saved modes. Create one with --save-mode NAME")
            return True

        print("\nSaved Modes:")
        print("=" * 70)

        # Sort by ID
        sorted_modes = sorted(self.modes.values(), key=lambda x: int(x['id']))

        for mode in sorted_modes:
            config = mode['config']
            # Format creation date
            created = mode.get('created', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    created = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass

            print(f"\n[{mode['id']}] {mode['name']}")
            print(f"    Created: {created}")

            # Show key config values
            big_model = config.get('BIG_MODEL', 'Not set')
            reasoning = config.get('REASONING_EFFORT', 'Not set')
            if len(big_model) > 40:
                big_model = big_model[:37] + "..."
            print(f"    Big Model: {big_model}")
            if reasoning != 'Not set':
                print(f"    Reasoning: {reasoning}")

        print("=" * 70)
        print(f"\nTotal: {len(self.modes)} mode(s)")
        return True

    def get_mode_config(self, identifier: str) -> Optional[Dict[str, str]]:
        """Get mode configuration without printing messages."""
        # Try as ID first
        if identifier in self.modes:
            return self.modes[identifier]['config']

        # Try as name
        for mode in self.modes.values():
            if mode.get('name', '').lower() == identifier.lower():
                return mode['config']

        return None


def handle_mode_operations(args) -> bool:
    """Handle mode-related operations from CLI arguments."""
    manager = ModeManager()

    # List modes
    if args.list_modes:
        manager.list_modes()
        return True

    # Load mode
    if args.load_mode:
        config = manager.load_mode(args.load_mode)
        if config:
            # Apply config to environment
            for key, value in config.items():
                os.environ[key] = value
        return True

    # Delete mode
    if args.delete_mode:
        manager.delete_mode(args.delete_mode)
        return True

    # Save mode
    if args.save_mode:
        # Get current config
        from src.core.config import config as current_config

        config = {
            'BIG_MODEL': current_config.big_model,
            'MIDDLE_MODEL': current_config.middle_model,
            'SMALL_MODEL': current_config.small_model,
            'REASONING_EFFORT': current_config.reasoning_effort or '',
            'VERBOSITY': current_config.verbosity or '',
            'REASONING_EXCLUDE': 'true' if current_config.reasoning_exclude else 'false',
            'HOST': str(current_config.host),
            'PORT': str(current_config.port),
            'LOG_LEVEL': current_config.log_level,
        }

        manager.save_mode(args.save_mode, config)
        return True

    # Shorthand --mode NAME (save after other args are set)
    if args.mode_name:
        # Get config from environment variables (including CLI args)
        config = {
            'BIG_MODEL': os.environ.get('BIG_MODEL', os.environ.get('CLAUDE_BIG_MODEL', '')),
            'MIDDLE_MODEL': os.environ.get('MIDDLE_MODEL', os.environ.get('CLAUDE_MIDDLE_MODEL', '')),
            'SMALL_MODEL': os.environ.get('SMALL_MODEL', os.environ.get('CLAUDE_SMALL_MODEL', '')),
            'REASONING_EFFORT': os.environ.get('REASONING_EFFORT', os.environ.get('CLAUDE_REASONING_EFFORT', '')),
            'VERBOSITY': os.environ.get('VERBOSITY', os.environ.get('CLAUDE_VERBOSITY', '')),
            'REASONING_EXCLUDE': os.environ.get('REASONING_EXCLUDE', os.environ.get('CLAUDE_REASONING_EXCLUDE', 'false')),
            'HOST': os.environ.get('HOST', os.environ.get('CLAUDE_HOST', '0.0.0.0')),
            'PORT': os.environ.get('PORT', os.environ.get('CLAUDE_PORT', '8082')),
            'LOG_LEVEL': os.environ.get('LOG_LEVEL', os.environ.get('CLAUDE_LOG_LEVEL', 'INFO')),
        }

        manager.save_mode(args.mode_name, config)
        return True

    return False
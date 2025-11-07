#!/usr/bin/env python3
"""
Interactive model selector for Claude Code Proxy.
Allows selection of BIG, MIDDLE, and SMALL models with reasoning support.
"""

import json
import os
import sys
import re
from typing import Dict, List, Any, Optional


# ANSI Color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Background colors
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


class ModelSelector:
    """Interactive model selector with colors and modes."""

    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        self.models_data = None
        self.selections = {
            "big_model": None,
            "middle_model": None,
            "small_model": None,
            "reasoning_effort": None,
            "verbosity": None,
            "reasoning_exclude": "false"
        }

    def color(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{Colors.RESET}"

    def load_models(self) -> bool:
        """Load models from JSON file."""
        models_file = os.path.join(self.models_dir, "openrouter_models.json")

        if not os.path.exists(models_file):
            print(self.color("✗ Models file not found: " + models_file, Colors.RED))
            print("  " + self.color("Run fetch_openrouter_models.py first to download model data.", Colors.YELLOW))
            return False

        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                self.models_data = json.load(f)
            return True
        except Exception as e:
            print(self.color(f"✗ Error loading models: {e}", Colors.RED))
            return False

    def display_header(self):
        """Display ASCII art header."""
        print("\n" + "="*70)
        print(self.color("╔" + "═"*68 + "╗", Colors.CYAN))
        print(self.color("║" + " "*68 + "║", Colors.CYAN))
        print(self.color("║" + " "*15 + "CLAUDE CODE PROXY" + " "*25 + "║", Colors.CYAN))
        print(self.color("║" + " "*20 + "Model Selector" + " "*23 + "║", Colors.BRIGHT_CYAN))
        print(self.color("║" + " "*68 + "║", Colors.CYAN))
        print(self.color("╚" + "═"*68 + "╝", Colors.CYAN))
        print("="*70)
        print("")

    def load_modes(self) -> Dict[str, Any]:
        """Load saved modes."""
        from src.utils.modes import ModeManager
        manager = ModeManager()
        return manager.modes

    def display_templates_menu(self):
        """Display and apply pre-built templates."""
        from src.utils.templates import ModeTemplates

        print(f"\n{self.color('='*70, Colors.BRIGHT_MAGENTA)}")
        print(self.color("║" + " "*20 + "Pre-Built Templates" + " "*23 + "║", Colors.BRIGHT_MAGENTA))
        print(self.color("="*70, Colors.BRIGHT_MAGENTA))

        templates = ModeTemplates.list_templates()

        print(self.color("\nAvailable Templates:", Colors.BOLD + Colors.WHITE))
        print(self.color("-" * 70, Colors.DIM))

        for i, template in enumerate(templates, 1):
            name = template['name']
            display_name = template['display_name']
            description = template['description']
            tags = ", ".join(template['tags'])

            print(f"{self.color(str(i) + '.', Colors.CYAN)} {self.color(display_name, Colors.BOLD + Colors.WHITE)}")
            print(f"     {self.color('ID:', Colors.YELLOW)} {name}")
            print(f"     {self.color('Description:', Colors.YELLOW)} {description}")
            print(f"     {self.color('Tags:', Colors.YELLOW)} {self.color(tags, Colors.DIM)}")
            print()

        print(self.color("-" * 70, Colors.DIM))
        print(self.color("\nSelect a template to apply (1-{})".format(len(templates)), Colors.BRIGHT_GREEN))
        print(self.color("or 'b' to go back", Colors.DIM))

        while True:
            choice = input(self.color("\n> ", Colors.BRIGHT_GREEN)).strip().lower()

            if choice == 'b':
                return

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(templates):
                    template_name = templates[idx]['name']
                    config = ModeTemplates.get_config(template_name)

                    if config:
                        # Apply the template
                        self.selections['big_model'] = config.get('BIG_MODEL')
                        self.selections['middle_model'] = config.get('MIDDLE_MODEL')
                        self.selections['small_model'] = config.get('SMALL_MODEL')
                        self.selections['reasoning_effort'] = config.get('REASONING_EFFORT') or None
                        self.selections['verbosity'] = config.get('VERBOSITY') or None
                        self.selections['reasoning_exclude'] = config.get('REASONING_EXCLUDE', 'false')

                        print(self.color(f"\n✓ Applied template: {templates[idx]['display_name']}", Colors.BRIGHT_GREEN))

                        # Show requirements
                        requirements = ModeTemplates.get_requirements(template_name)
                        if requirements:
                            print(self.color("\nRequirements:", Colors.BOLD + Colors.WHITE))
                            for key, value in requirements.items():
                                if isinstance(value, bool):
                                    status = self.color("✓", Colors.BRIGHT_GREEN) if value else self.color("✗", Colors.BRIGHT_RED)
                                    print(f"  {status} {key}")
                                else:
                                    print(f"  • {key}: {value}")

                        input("\nPress Enter to continue...")
                        return

            print(self.color("Invalid selection. Please try again.", Colors.BRIGHT_RED))

    def display_recommendations_menu(self):
        """Display model recommendations based on usage and alternatives."""
        from src.utils.recommender import ModelRecommender

        print(f"\n{self.color('='*70, Colors.BRIGHT_YELLOW)}")
        print(self.color("║" + " "*17 + "Model Recommendations" + " "*22 + "║", Colors.BRIGHT_YELLOW))
        print(self.color("="*70, Colors.BRIGHT_YELLOW))

        recommender = ModelRecommender()

        # Show usage patterns
        print(self.color("\nUsage Analysis:", Colors.BOLD + Colors.WHITE))
        print(self.color("-" * 70, Colors.DIM))

        patterns = recommender.analyze_usage_patterns()

        if patterns['big_models']:
            print(self.color("\nMost Used BIG Models:", Colors.CYAN))
            for model, count in patterns['big_models'].most_common(3):
                print(f"  {self.color('•', Colors.CYAN)} {model} ({count} modes)")

        if patterns['reasoning_usage']:
            print(self.color("\nPreferred Reasoning Effort:", Colors.CYAN))
            for effort, count in patterns['reasoning_usage'].most_common(3):
                print(f"  {self.color('•', Colors.CYAN)} {effort} ({count} modes)")

        # Show free alternatives
        print(self.color("\n" + "=" * 70, Colors.DIM))
        print(self.color("\nFind Free Alternatives", Colors.BOLD + Colors.WHITE))
        print(self.color("-" * 70, Colors.DIM))
        print(self.color("Enter a paid model ID to find free alternatives:", Colors.DIM))
        print(self.color("Example: openai/gpt-5", Colors.DIM))

        model_input = input(self.color("\nModel ID: ", Colors.BRIGHT_GREEN)).strip()

        if model_input:
            print(self.color(f"\nSearching for alternatives to {model_input}...", Colors.BRIGHT_CYAN))

            # Find free alternatives
            free_alternatives = recommender.find_model_alternatives(model_input, "free")
            local_alternatives = recommender.find_model_alternatives(model_input, "local")

            if free_alternatives:
                print(self.color(f"\nTop FREE alternatives ({len(free_alternatives)} found):", Colors.BRIGHT_GREEN))
                print(self.color("-" * 70, Colors.DIM))

                for alt in free_alternatives[:5]:
                    model = alt['model']
                    print(f"\n{self.color('•', Colors.BRIGHT_GREEN)} {model['id']}")
                    print(f"  Score: {alt['score']}")
                    for reason in alt['reasons'][:3]:
                        print(f"  {self.color('  -', Colors.DIM)} {reason}")

                    # Show model details
                    if model.get('context_length'):
                        print(f"  {self.color('Context:', Colors.YELLOW)} {model['context_length']:,} tokens")
                    if model.get('source'):
                        print(f"  {self.color('Source:', Colors.YELLOW)} {model['source']}")

            else:
                print(self.color("\nNo free alternatives found for this model.", Colors.BRIGHT_YELLOW))

            if local_alternatives and local_alternatives != free_alternatives:
                print(self.color(f"\nTop LOCAL alternatives ({len(local_alternatives)} found):", Colors.BRIGHT_BLUE))
                print(self.color("-" * 70, Colors.DIM))

                for alt in local_alternatives[:3]:
                    model = alt['model']
                    print(f"\n{self.color('•', Colors.BRIGHT_BLUE)} {model['id']}")
                    print(f"  Score: {alt['score']}")

        input("\nPress Enter to continue...")

    def display_modes_menu(self):
        """Display modes submenu."""
        modes = self.load_modes()
        mode_list = list(modes.values()) if modes else []

        print(f"\n{self.color('='*70, Colors.MAGENTA)}")
        print(self.color("║" + " "*20 + "Configuration Modes" + " "*21 + "║", Colors.MAGENTA))
        print(self.color("="*70, Colors.MAGENTA))

        if not mode_list:
            print(self.color("\nNo saved modes found.", Colors.YELLOW))
            print("Save your current configuration as a mode from the main menu.")
            input("\nPress Enter to continue...")
            return

        # Sort by ID
        mode_list.sort(key=lambda x: int(x['id']))

        print(self.color("\nSaved Modes:", Colors.BOLD + Colors.WHITE))
        print("-" * 70)

        for mode in mode_list:
            config = mode['config']
            big_model = config.get('BIG_MODEL', 'Not set')
            if len(big_model) > 40:
                big_model = big_model[:37] + "..."

            reasoning = config.get('REASONING_EFFORT', 'Not set')
            created = mode.get('created', '')
            if created:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created)
                    created = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass

            print(f"{self.color('[' + mode['id'] + ']', Colors.CYAN)} {self.color(mode['name'], Colors.BOLD + Colors.WHITE)}")
            print(f"     {self.color('Big Model:', Colors.YELLOW)} {big_model}")
            if reasoning != 'Not set':
                print(f"     {self.color('Reasoning:', Colors.YELLOW)} {reasoning}")
            print(f"     {self.color('Created:', Colors.YELLOW)} {created}")
            print()

        print("-" * 70)
        print(self.color("\nSelect a mode to load, or 'b' to go back", Colors.BRIGHT_GREEN))
        print(self.color("Options: 1-99 (mode ID) or 'b' to back", Colors.DIM))

        while True:
            choice = input("\n> ").strip().lower()

            if choice == 'b':
                return

            if choice.isdigit() and 1 <= int(choice) <= 99:
                mode_id = choice
                if mode_id in modes:
                    # Load this mode
                    config = modes[mode_id]['config']
                    self.selections['big_model'] = config.get('BIG_MODEL')
                    self.selections['middle_model'] = config.get('MIDDLE_MODEL')
                    self.selections['small_model'] = config.get('SMALL_MODEL')
                    self.selections['reasoning_effort'] = config.get('REASONING_EFFORT') or None
                    self.selections['verbosity'] = config.get('VERBOSITY') or None
                    self.selections['reasoning_exclude'] = config.get('REASONING_EXCLUDE', 'false')

                    print(self.color(f"\n✓ Loaded mode '{modes[mode_id]['name']}'", Colors.BRIGHT_GREEN))
                    input("\nPress Enter to continue...")
                    return
                else:
                    print(self.color(f"Mode {mode_id} not found", Colors.RED))
            else:
                print(self.color("Invalid selection", Colors.RED))

    def display_menu(self, title: str, items: List[Dict[str, Any]], multi_select: bool = False) -> List[int]:
        """Display a numbered menu of items with enhanced metadata."""
        print(f"\n{title}")
        print(self.color("-" * 70, Colors.DIM))

        for i, item in enumerate(items, 1):
            # Truncate long model names
            model_id = item['id'] if 'id' in item else str(item)
            if len(model_id) > 45:
                model_id = model_id[:42] + "..."

            # Add capability indicators
            indicators = []
            if 'supports_reasoning' in item and item['supports_reasoning']:
                indicators.append(self.color("REASONING", Colors.BRIGHT_GREEN))
            if 'supports_vision' in item and item['supports_vision']:
                indicators.append(self.color("VISION", Colors.BRIGHT_BLUE))
            if 'is_free' in item and item['is_free']:
                indicators.append(self.color("FREE", Colors.BRIGHT_YELLOW))

            indicator_str = " [" + ", ".join(indicators) + "]" if indicators else ""

            print(f"{self.color(str(i) + '.', Colors.CYAN)} {model_id}{indicator_str}")

            # Show source and endpoint
            if 'source' in item:
                source_info = self.get_source_and_endpoint(item)
                print(f"     {self.color(source_info, Colors.DIM)}")

            # Show name if different from id
            if 'name' in item and item['name'] and item['name'] != item.get('id'):
                print(f"     {self.color(item['name'], Colors.WHITE)}")

            # Show context length
            if item.get('context_length'):
                print(f"     {self.color('Context:', Colors.YELLOW)} {item['context_length']:,} tokens")

            # Show pricing
            if item.get('pricing'):
                pricing = item['pricing']
                if pricing.get('prompt_numeric', 0) > 0:
                    print(f"     {self.color('Price:', Colors.YELLOW)} ${pricing['prompt']}/1M prompt, ${pricing['completion']}/1M completion")
                else:
                    print(f"     {self.color('Price:', Colors.YELLOW)} Free")

        print(self.color("-" * 70, Colors.DIM))

        if multi_select:
            print(self.color("Enter numbers separated by commas (e.g., 1,3,5) or 'a' for all", Colors.DIM))
        else:
            print(self.color("Enter number (or 'b' to go back)", Colors.DIM))

        while True:
            try:
                choice = input(self.color("\n> ", Colors.BRIGHT_GREEN)).strip()
                if choice.lower() == 'b' and not multi_select:
                    return []

                if multi_select and choice.lower() == 'a':
                    return list(range(len(items)))

                numbers = [int(x.strip()) for x in choice.split(',') if x.strip().isdigit()]
                valid_numbers = [n for n in numbers if 1 <= n <= len(items)]

                if valid_numbers:
                    # Convert to 0-based index
                    return [n - 1 for n in valid_numbers]
                else:
                    print("Invalid selection. Please try again.")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)

    def get_reasoning_models(self) -> List[Dict[str, Any]]:
        """Get models that support reasoning (including local models)."""
        all_models = (
            self.models_data.get("local_models", []) +
            self.models_data.get("reasoning_models", []) +
            self.models_data.get("verbosity_models", [])
        )
        # Remove duplicates by id
        seen = set()
        unique_models = []
        for model in all_models:
            if model['id'] not in seen:
                seen.add(model['id'])
                unique_models.append(model)
        return unique_models

    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all available models."""
        all_models = (
            self.models_data.get("local_models", []) +
            self.models_data.get("reasoning_models", []) +
            self.models_data.get("verbosity_models", []) +
            self.models_data.get("standard_models", [])
        )
        # Remove duplicates
        seen = set()
        unique_models = []
        for model in all_models:
            if model['id'] not in seen:
                seen.add(model['id'])
                unique_models.append(model)
        return unique_models

    def get_local_models(self) -> List[Dict[str, Any]]:
        """Get local provider models."""
        return self.models_data.get("local_models", [])

    def get_source_and_endpoint(self, model: Dict[str, Any]) -> str:
        """Get source and endpoint info for display."""
        source = model.get('source', 'unknown')
        endpoint = model.get('endpoint', 'N/A')

        if source == 'lmstudio':
            return f"[LMStudio] {endpoint}"
        elif source == 'ollama':
            return f"[Ollama] {endpoint}"
        elif source == 'openrouter':
            return f"[OpenRouter]"
        else:
            return f"[{source}]"

    def select_model(self, model_type: str, category: str) -> Optional[str]:
        """Select a model with reasoning support preference."""
        print(f"\n{self.color('='*70, Colors.BRIGHT_CYAN)}")
        print(self.color(f"║" + f" Select {model_type} Model ".center(68) + "║", Colors.BRIGHT_CYAN))
        print(self.color("="*70, Colors.BRIGHT_CYAN))

        # Get appropriate models based on category
        if category == "reasoning":
            available_models = self.get_reasoning_models()
            if not available_models:
                print(self.color("No models with reasoning support found!", Colors.BRIGHT_RED))
                return None
            print(self.color(f"\nShowing models with REASONING support ({len(available_models)} models)", Colors.BRIGHT_GREEN))
        elif category == "all":
            available_models = self.get_all_models()
            available_models = sorted(available_models, key=lambda x: x['id'].lower())
            print(self.color(f"\nShowing all models ({len(available_models)} models)", Colors.BRIGHT_GREEN))
        elif category == "local":
            available_models = self.get_local_models()
            print(self.color(f"\nShowing local models ({len(available_models)} models)", Colors.BRIGHT_GREEN))
        else:
            available_models = sorted(
                self.models_data.get("standard_models", []),
                key=lambda x: x['id'].lower()
            )
            print(f"\nShowing standard models ({len(available_models)} models)")

        # Show a subset (top 20) for easier selection
        display_models = available_models[:20]
        print(f"Showing first {len(display_models)} (of {len(available_models)}) for performance")
        print("Use search option to find specific models.")

        # Add search option
        display_models = [{"id": "SEARCH", "name": "Search for a model..."}] + display_models

        indices = self.display_menu(
            f"Choose your {model_type} model (category: {category})",
            display_models
        )

        if not indices:
            return None

        if indices[0] == 0:  # Search selected
            return self.search_and_select_model(model_type, available_models)

        selected_model = display_models[indices[0]]
        return selected_model['id']

    def search_and_select_model(self, model_type: str, available_models: List[Dict[str, Any]]) -> Optional[str]:
        """Search and select a model."""
        print("\n" + "="*70)
        print("Search Models")
        print("="*70)
        print("Enter search term (provider, model name, or keyword)")
        print("Examples: 'gpt-5', 'claude', 'openai', 'qwen', 'free'")
        print("(Press Enter with no input to cancel)")

        search_term = input("\nSearch term: ").strip().lower()

        if not search_term:
            return None

        # Filter models
        matches = []
        for model in available_models:
            if (search_term in model['id'].lower() or
                search_term in model.get('name', '').lower() or
                search_term in model.get('description', '').lower()):
                matches.append(model)

        if not matches:
            print(f"\nNo models found matching '{search_term}'")
            return self.search_and_select_model(model_type, available_models)

        print(f"\nFound {len(matches)} matching model(s)")
        indices = self.display_menu(
            f"Select from {len(matches)} matches",
            matches
        )

        if not indices:
            return self.search_and_select_model(model_type, available_models)

        return matches[indices[0]]['id']

    def select_reasoning_config(self) -> Dict[str, str]:
        """Select reasoning configuration."""
        print(f"\n{'='*70}")
        print("Reasoning Configuration")
        print(f"{'='*70}")

        print("\nGPT-5 and other reasoning models support configuring:")
        print("  - Reasoning effort: How much compute to use for reasoning")
        print("  - Verbosity: Detail level of responses")
        print("  - Reasoning exclude: Whether to show reasoning tokens")

        print("\n--- Reasoning Effort ---")
        print("1. low    - Faster, less reasoning")
        print("2. medium - Balanced (default)")
        print("3. high   - Best quality, more compute")
        print("4. None   - Disable reasoning")

        effort_choice = input("\nSelect effort (1-4): ").strip()

        effort_map = {
            "1": "low",
            "2": "medium",
            "3": "high",
            "4": ""
        }

        reasoning_effort = effort_map.get(effort_choice, "")

        print("\n--- Verbosity Level ---")
        print("1. default - Standard verbosity")
        print("2. high    - More detailed responses")

        verbosity_choice = input("\nSelect verbosity (1-2): ").strip()
        verbosity_map = {
            "1": "",
            "2": "high"
        }
        verbosity = verbosity_map.get(verbosity_choice, "")

        print("\n--- Reasoning Tokens ---")
        print("1. Show (exclude=false) - Include reasoning in response")
        print("2. Hide (exclude=true)  - Exclude reasoning from response")

        exclude_choice = input("\nSelect (1-2): ").strip()
        exclude_map = {
            "1": "false",
            "2": "true"
        }
        reasoning_exclude = exclude_map.get(exclude_choice, "false")

        return {
            "reasoning_effort": reasoning_effort,
            "verbosity": verbosity,
            "reasoning_exclude": reasoning_exclude
        }

    def display_selections(self):
        """Display current selections with colors."""
        print(f"\n{self.color('='*70, Colors.BRIGHT_MAGENTA)}")
        print(self.color("║" + " "*21 + "CURRENT CONFIGURATION" + " "*21 + "║", Colors.BRIGHT_MAGENTA))
        print(self.color("="*70, Colors.BRIGHT_MAGENTA))

        big_model = self.selections['big_model'] or self.color('Not selected', Colors.DIM)
        middle_model = self.selections['middle_model'] or self.color('Not selected', Colors.DIM)
        small_model = self.selections['small_model'] or self.color('Not selected', Colors.DIM)
        reasoning_effort = self.selections['reasoning_effort'] or self.color('Not set', Colors.DIM)
        verbosity = self.selections['verbosity'] or self.color('Not set', Colors.DIM)

        print(f"{self.color('BIG_MODEL:', Colors.YELLOW)}       {big_model}")
        print(f"{self.color('MIDDLE_MODEL:', Colors.YELLOW)}    {middle_model}")
        print(f"{self.color('SMALL_MODEL:', Colors.YELLOW)}     {small_model}")
        print(f"{self.color('REASONING_EFFORT:', Colors.YELLOW)} {reasoning_effort}")
        print(f"{self.color('VERBOSITY:', Colors.YELLOW)}        {verbosity}")
        print(f"{self.color('REASONING_EXCLUDE:', Colors.YELLOW)} {self.selections['reasoning_exclude']}")
        print(self.color("="*70, Colors.BRIGHT_MAGENTA))

    def update_env_file(self) -> bool:
        """Update .env file with selections."""
        if not os.path.exists(self.env_file):
            print(f"✗ .env file not found: {self.env_file}")
            return False

        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Create a dictionary of current values
            env_dict = {}
            for line in lines:
                line = line.rstrip('\r\n')
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()

            # Update with selections
            if self.selections['big_model']:
                env_dict['BIG_MODEL'] = self.selections['big_model']
            if self.selections['middle_model']:
                env_dict['MIDDLE_MODEL'] = self.selections['middle_model']
            if self.selections['small_model']:
                env_dict['SMALL_MODEL'] = self.selections['small_model']
            if self.selections['reasoning_effort'] is not None:
                env_dict['REASONING_EFFORT'] = self.selections['reasoning_effort']
            if self.selections['verbosity'] is not None:
                env_dict['VERBOSITY'] = self.selections['verbosity']
            if self.selections['reasoning_exclude']:
                env_dict['REASONING_EXCLUDE'] = self.selections['reasoning_exclude']

            # Write back to file
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    line = line.rstrip('\r\n')
                    if '=' in line and not line.startswith('#'):
                        key = line.split('=', 1)[0].strip()
                        if key in env_dict:
                            f.write(f"{key}={env_dict[key]}\n")
                            del env_dict[key]
                        else:
                            f.write(line + '\n')
                    else:
                        f.write(line + '\n')

                # Add any new keys
                for key, value in env_dict.items():
                    f.write(f"{key}={value}\n")

            print(f"\n✓ Updated {self.env_file}")
            return True

        except Exception as e:
            print(f"\n✗ Error updating .env file: {e}")
            return False

    def run(self):
        """Run the interactive selector."""
        self.display_header()

        # Load models
        if not self.load_models():
            print("\nRun fetch_openrouter_models.py first to download model data.")
            sys.exit(1)

        print(self.color(f"Loaded {self.models_data['summary']['total']} models", Colors.BRIGHT_GREEN))
        print(self.color(f"  - {self.models_data['summary']['local_count']} local (LMStudio, Ollama)", Colors.BRIGHT_YELLOW))
        print(self.color(f"  - {self.models_data['summary']['reasoning_count']} with reasoning", Colors.BRIGHT_GREEN))
        print(self.color(f"  - {self.models_data['summary']['verbosity_count']} with verbosity", Colors.BRIGHT_GREEN))
        print(self.color(f"  - {self.models_data['summary']['standard_count']} standard", Colors.BRIGHT_GREEN))
        print(self.color(f"  - {self.models_data['summary']['free_count']} free models", Colors.BRIGHT_YELLOW))

        # Selection loop
        while True:
            print(f"\n{self.color('='*70, Colors.BRIGHT_BLUE)}")
            print(self.color("║" + " "*25 + "MAIN MENU" + " "*29 + "║", Colors.BRIGHT_BLUE))
            print(self.color("="*70, Colors.BRIGHT_BLUE))

            print(f"{self.color('1.', Colors.CYAN)} {self.color('Select BIG model', Colors.WHITE)} (for Claude Opus)")
            print(f"{self.color('2.', Colors.CYAN)} {self.color('Select MIDDLE model', Colors.WHITE)} (for Claude Sonnet)")
            print(f"{self.color('3.', Colors.CYAN)} {self.color('Select SMALL model', Colors.WHITE)} (for Claude Haiku)")
            print(f"{self.color('4.', Colors.CYAN)} {self.color('Configure reasoning settings', Colors.WHITE)}")
            print(f"{self.color('5.', Colors.CYAN)} {self.color('View current selections', Colors.WHITE)}")
            print()
            print(f"{self.color('6.', Colors.BRIGHT_YELLOW)} {self.color('Browse LOCAL models', Colors.BRIGHT_YELLOW)} (LMStudio, Ollama)")
            print(f"{self.color('7.', Colors.BRIGHT_MAGENTA)} {self.color('Use Template', Colors.BRIGHT_MAGENTA)} (Free-tier, Production, etc.)")
            print(f"{self.color('8.', Colors.BRIGHT_BLUE)} {self.color('Get Recommendations', Colors.BRIGHT_BLUE)} (Find free alternatives)")
            print(f"{self.color('9.', Colors.MAGENTA)} {self.color('Save and apply configuration', Colors.MAGENTA)}")
            print()
            print(f"{self.color('10.', Colors.YELLOW)} {self.color('Load saved mode', Colors.YELLOW)}")
            print(f"{self.color('11.', Colors.YELLOW)} {self.color('Save current config as mode', Colors.YELLOW)}")
            print(f"{self.color('12.', Colors.YELLOW)} {self.color('List all modes', Colors.YELLOW)}")
            print()
            print(f"{self.color('0.', Colors.BRIGHT_RED)} {self.color('Exit', Colors.BRIGHT_RED)}")

            choice = input(self.color("\n> Select option: ", Colors.BRIGHT_GREEN)).strip()

            if choice == '1':
                model = self.select_model("BIG", "all")
                if model:
                    self.selections['big_model'] = model
                    print(self.color(f"\n✓ Selected: {model}", Colors.BRIGHT_GREEN))
                    input("\nPress Enter to continue...")

            elif choice == '2':
                model = self.select_model("MIDDLE", "all")
                if model:
                    self.selections['middle_model'] = model
                    print(self.color(f"\n✓ Selected: {model}", Colors.BRIGHT_GREEN))
                    input("\nPress Enter to continue...")

            elif choice == '3':
                model = self.select_model("SMALL", "all")
                if model:
                    self.selections['small_model'] = model
                    print(self.color(f"\n✓ Selected: {model}", Colors.BRIGHT_GREEN))
                    input("\nPress Enter to continue...")

            elif choice == '4':
                reasoning_config = self.select_reasoning_config()
                self.selections.update(reasoning_config)
                print(self.color("\n✓ Reasoning configuration updated", Colors.BRIGHT_GREEN))
                input("\nPress Enter to continue...")

            elif choice == '5':
                self.display_selections()
                input("\nPress Enter to continue...")

            elif choice == '6':
                # Browse local models
                model = self.select_model("LOCAL", "local")
                if model:
                    # Ask which slot to use
                    print(self.color("\nSelect which model slot to use:", Colors.BRIGHT_CYAN))
                    print(self.color("1. BIG model (Claude Opus)", Colors.WHITE))
                    print(self.color("2. MIDDLE model (Claude Sonnet)", Colors.WHITE))
                    print(self.color("3. SMALL model (Claude Haiku)", Colors.WHITE))

                    slot_choice = input(self.color("\nSelect slot (1-3): ", Colors.BRIGHT_GREEN)).strip()

                    if slot_choice == '1':
                        self.selections['big_model'] = model
                        print(self.color(f"\n✓ Set BIG model: {model}", Colors.BRIGHT_GREEN))
                    elif slot_choice == '2':
                        self.selections['middle_model'] = model
                        print(self.color(f"\n✓ Set MIDDLE model: {model}", Colors.BRIGHT_GREEN))
                    elif slot_choice == '3':
                        self.selections['small_model'] = model
                        print(self.color(f"\n✓ Set SMALL model: {model}", Colors.BRIGHT_GREEN))
                    else:
                        print(self.color("Invalid selection", Colors.BRIGHT_RED))

                    input("\nPress Enter to continue...")

            elif choice == '7':
                self.display_templates_menu()

            elif choice == '8':
                self.display_recommendations_menu()

            elif choice == '9':
                if not any([self.selections['big_model'],
                            self.selections['middle_model'],
                            self.selections['small_model']]):
                    print(self.color("\n⚠ Warning: No models selected!", Colors.BRIGHT_YELLOW))
                    confirm = input(self.color("Continue anyway? (y/N): ", Colors.BRIGHT_YELLOW)).strip().lower()
                    if confirm != 'y':
                        continue

                if self.update_env_file():
                    print("\n" + self.color("="*70, Colors.BRIGHT_GREEN))
                    print(self.color("✓ Configuration saved successfully!", Colors.BRIGHT_GREEN))
                    print(self.color("="*70, Colors.BRIGHT_GREEN))
                    print(self.color("\nYour .env file has been updated with the selected models.", Colors.WHITE))
                    print(self.color("Restart the proxy server to use the new configuration.", Colors.WHITE))
                else:
                    print(self.color("\n✗ Failed to save configuration", Colors.BRIGHT_RED))

                input("\nPress Enter to continue...")

            elif choice == '10':
                self.display_modes_menu()

            elif choice == '11':
                # Save current config as mode
                print(self.color("\n" + "="*70, Colors.MAGENTA))
                print(self.color("Save Configuration as Mode", Colors.MAGENTA))
                print(self.color("="*70, Colors.MAGENTA))

                mode_name = input(self.color("\nEnter mode name: ", Colors.BRIGHT_GREEN)).strip()

                if not mode_name:
                    print(self.color("Mode name cannot be empty", Colors.BRIGHT_RED))
                    input("\nPress Enter to continue...")
                    continue

                # Create config from current selections
                config = {
                    'BIG_MODEL': self.selections['big_model'] or '',
                    'MIDDLE_MODEL': self.selections['middle_model'] or '',
                    'SMALL_MODEL': self.selections['small_model'] or '',
                    'REASONING_EFFORT': self.selections['reasoning_effort'] or '',
                    'VERBOSITY': self.selections['verbosity'] or '',
                    'REASONING_EXCLUDE': self.selections['reasoning_exclude'],
                }

                from src.utils.modes import ModeManager
                manager = ModeManager()
                if manager.save_mode(mode_name, config):
                    print(self.color(f"✓ Saved configuration as mode: {mode_name}", Colors.BRIGHT_GREEN))

                input("\nPress Enter to continue...")

            elif choice == '12':
                from src.utils.modes import ModeManager
                manager = ModeManager()
                manager.list_modes()
                input("\nPress Enter to continue...")

            elif choice == '0':
                print(self.color("\nGoodbye!", Colors.BRIGHT_CYAN))
                break

            else:
                print(self.color("\nInvalid option. Please try again.", Colors.BRIGHT_RED))


def main():
    try:
        selector = ModelSelector()
        selector.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()

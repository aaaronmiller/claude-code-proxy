"""Interactive model selector with static TUI (no scrolling spam)."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from src.services.models.model_filter import get_available_models, filter_models, model_filter
from src.services.models.modes import ModeManager
from src.services.models.recommender import ModelRecommender
from src.services.usage.model_limits import get_model_limits

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE TERMINAL SIZE: 140 columns × 40 rows
# Source: Ice-ninja's Ghostty config (~/.config/ghostty/config)
# 
# All TUI elements should fit within this minimum size:
# - Max content width: 138 chars (140 - 2 for borders)
# - Usable rows: ~25 for model list (40 - 15 header/footer chrome)
# 
# The TUI auto-adapts to terminal size via get_terminal_size()
# ═══════════════════════════════════════════════════════════════════════════════

# Try to import readchar for arrow key support
try:
    import readchar
    ARROW_SUPPORT = True
except ImportError:
    ARROW_SUPPORT = False


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size (rows, cols)."""
    try:
        size = os.get_terminal_size()
        return size.lines, size.columns
    except (OSError, ValueError, AttributeError):
        return 24, 80

DEFAULT_MODELS = [
    # ═══════════════════════════════════════════════════════════════════════════════
    # VIBEPROXY / ANTIGRAVITY (FREE via local OAuth - port 8317)
    # These route through VibeProxy's local proxy with OAuth authentication
    # ═══════════════════════════════════════════════════════════════════════════════
    "vibeproxy/gemini-2.5-pro",
    "vibeproxy/gemini-2.5-flash",
    "vibeproxy/gemini-2.0-flash-thinking",
    "vibeproxy/claude-sonnet-4",
    "vibeproxy/claude-opus-4",
    "vibeproxy/gpt-4o",
    "vibeproxy/qwen-2.5-max",
    
    # Legacy antigravity/ prefix (alias for vibeproxy/)
    "antigravity/gemini-3-pro",
    "antigravity/gemini-3-flash",
    "antigravity/claude-sonnet-4.5",
    "antigravity/claude-sonnet-4.5-thinking",
    "antigravity/claude-opus-4.5",
    "antigravity/gpt-oss-120b",
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DIRECT API ROUTES (requires API keys configured in .env)
    # These connect directly to provider APIs without VibeProxy
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # OpenAI Direct (requires OPENAI_API_KEY)
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "openai/o1",
    "openai/o1-mini",
    
    # Anthropic Direct (requires ANTHROPIC_API_KEY)
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-5-haiku",
    "anthropic/claude-3-opus",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4",
    
    # Google Direct (requires GOOGLE_API_KEY)
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "google/gemini-2.0-flash-thinking",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # OPENROUTER (aggregated access via OpenRouter API key)
    # ═══════════════════════════════════════════════════════════════════════════════
    "openrouter/anthropic/claude-3.5-sonnet",
    "openrouter/openai/gpt-4o",
    "openrouter/google/gemini-pro-1.5",
    "openrouter/meta-llama/llama-3.1-405b-instruct",
    "openrouter/meta-llama/llama-3.1-70b-instruct",
    "openrouter/qwen/qwen-2.5-72b-instruct",
    "openrouter/mistral/mistral-large-2407",
    "openrouter/cohere/command-r-plus-08-2024",
    
    # Meta (via OpenRouter)
    "meta-llama/llama-3.1-405b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    
    # Others (via OpenRouter)
    "mistral/mistral-large-2407",
    "cohere/command-r-plus-08-2024",
    "qwen/qwen-2.5-72b-instruct"
]

def load_all_models() -> List[str]:
    """Load all available models from the scraped database or use defaults."""
    models_dir = Path(__file__).parent.parent.parent / "models"
    json_path = models_dir / "model_limits.json"
    
    # Try to load from file
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                return sorted(data.keys())
        except Exception:
            pass # Fallback to defaults
            
    return sorted(DEFAULT_MODELS)


def format_model_line(idx: int, model_id: str, selected_for: Optional[str] = None, max_width: int = 80) -> str:
    """Format a single model line for display."""
    context, output = get_model_limits(model_id)
    
    def fmt(tokens):
        if tokens >= 1000000:
            return f"{tokens/1000000:.1f}M"
        elif tokens >= 1000:
            return f"{tokens/1000:.0f}k"
        return str(tokens)
    
    # Badges
    badges = []
    if model_filter.is_new_model(model_id):
        badges.append("✨") # New
    if model_filter.is_free_model(model_id):
        badges.append("🆓") # Free
    if model_filter.is_top_model(model_id):
        badges.append("🏆") # Top/Popular
    if model_filter.get_recently_used_models(20) and model_id in model_filter.get_recently_used_models(20):
        badges.append("⭐") # Used
    if selected_for:
        badges.append(f"[{selected_for}]")
    
    badge_str = " ".join(badges) if badges else ""
    badge_len = len(badge_str) + 1 if badge_str else 0
    
    # Dynamic name width
    # Line format: "{idx:3}. {name} {ctx} {out}  {badges}"
    # Fixed chars: 3(idx) + 2(. ) + 1(space) + 6(ctx) + 1(sp) + 6(out) + 2(sp) + 2(border) = ~23 chars roughly
    # We reserved 4 chars for border/padding in main loop, so passed-in max_width is real available
    suffix_len = 16 + badge_len # ctx(6)+sp+out(6)+sp(2)+badges
    prefix_len = 6 # idx(3)+dot+sp
    name_width = max(10, max_width - prefix_len - suffix_len)
    
    display_name = model_id
    if len(display_name) > name_width:
        display_name = display_name[:name_width-3] + "..."
    
    return f"{idx:3}. {display_name:<{name_width}} {fmt(context):>6} {fmt(output):>6}  {badge_str}"


def draw_ui(
    models: List[str],
    page: int,
    per_page: int,
    search_query: str,
    big_model: Optional[str],
    middle_model: Optional[str],
    small_model: Optional[str],
    show_all: bool
):
    """Draw the static UI (no scrolling)."""
    clear_screen()
    rows, cols = get_terminal_size()
    
    # Header
    print("╔" + "═" * (cols - 2) + "╗")
    print("║" + " MODEL SELECTOR ".center(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    
    # Current selections
    print(f"║ BIG:    {(big_model or 'not set'):<{cols-12}}║")
    print(f"║ MIDDLE: {(middle_model or 'not set'):<{cols-12}}║")
    print(f"║ SMALL:  {(small_model or 'not set'):<{cols-12}}║")
    print("╠" + "═" * (cols - 2) + "╣")
    
    # Model list header
    mode = "ALL MODELS" if show_all else "RECOMMENDED"
    total_models = len(models)
    total_pages = (total_models + per_page - 1) // per_page
    current_page = page + 1
    
    header = f" {mode} ({total_models} models) - Page {current_page}/{total_pages} "
    if search_query:
        header += f"- Search: '{search_query}' "
    print("║" + header.ljust(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print(f"║ {'#':<3}  {'Model':<45} {'CTX':>6} {'OUT':>6}  {'Tags':<15}║")
    print("╠" + "─" * (cols - 2) + "╣")
    
    # Model list (paginated)
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_models)
    
    # Determine which models are selected
    selected_map = {}
    if big_model in models:
        selected_map[big_model] = "B"
    if middle_model in models:
        selected_map[middle_model] = "M"
    if small_model in models:
        selected_map[small_model] = "S"
    
    for i in range(start_idx, end_idx):
        model_id = models[i]
        selected_for = selected_map.get(model_id)
        line = format_model_line(i + 1, model_id, selected_for)
        # Truncate to fit terminal width
        if len(line) > cols - 4:
            line = line[:cols - 7] + "..."
        print(f"║ {line:<{cols-4}} ║")
    
    # Fill remaining space
    displayed = end_idx - start_idx
    max_display = rows - 15  # Reserve space for header/footer
    for _ in range(max_display - displayed):
        print("║" + " " * (cols - 2) + "║")
    
    # Footer with commands
    print("╠" + "═" * (cols - 2) + "╣")
    print("║ COMMANDS:".ljust(cols - 1) + "║")
    print("║   [number] b/m/s  - Assign model to Big/Middle/Small".ljust(cols - 1) + "║")
    print("║   n/p             - Next/Previous page".ljust(cols - 1) + "║")
    print("║   /[text]         - Search models".ljust(cols - 1) + "║")
    print("║   a               - Toggle All/Recommended".ljust(cols - 1) + "║")
    print("║   paste [model]   - Paste custom model ID".ljust(cols - 1) + "║")
    print("║   q               - Save and quit".ljust(cols - 1) + "║")
    print("╚" + "═" * (cols - 2) + "╝")
    print()


def draw_menu(cursor: int, big_model: str, middle_model: str, small_model: str):
    """Draw the main menu for selecting which slot to configure."""
    clear_screen()
    rows, cols = get_terminal_size()
    
    print("╔" + "═" * (cols - 2) + "╗")
    print("║" + " MODEL SELECTOR - CHOOSE SLOT ".center(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║" + " " * (cols - 2) + "║")
    
    options = [
        ("BIG MODEL", big_model or "not set"),
        ("MIDDLE MODEL", middle_model or "not set"),
        ("SMALL MODEL", small_model or "not set"),
        ("SAVE & QUIT", ""),
        ("BACK TO SETTINGS", ""),
    ]

    for i, (label, value) in enumerate(options):
        if i == cursor:
            if value:
                line = f"  → {label}: {value}"
            else:
                line = f"  → {label}"
            print("║ " + line.ljust(cols - 3) + "║")
        else:
            if value:
                line = f"    {label}: {value}"
            else:
                line = f"    {label}"
            print("║ " + line.ljust(cols - 3) + "║")
    
    print("║" + " " * (cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║ CONTROLS:".ljust(cols - 1) + "║")
    print("║   ↑/↓ or j/k  - Navigate".ljust(cols - 1) + "║")
    print("║   Enter       - Select".ljust(cols - 1) + "║")
    print("║   q           - Quit without saving".ljust(cols - 1) + "║")
    print("╚" + "═" * (cols - 2) + "╝")


def get_key():
    """Get a single keypress (works with or without readchar)."""
    if ARROW_SUPPORT:
        key = readchar.readkey()
        if key == readchar.key.UP:
            return 'UP'
        elif key == readchar.key.DOWN:
            return 'DOWN'
        elif key == readchar.key.ENTER or key == '\r' or key == '\n':
            return 'ENTER'
        else:
            return key
    else:
        # Fallback to regular input
        return input("→ ").strip()


def run_model_selector():
    """Run the interactive model selector with static UI."""
    from src.core.config import config
    
    # Load models
    all_models = load_all_models()
    if not all_models:
        print("❌ No models found. Run the scraper first.")
        return
    
    # State
    big_model = config.big_model
    middle_model = config.middle_model
    small_model = config.small_model
    
    # Main menu loop
    menu_cursor = 0
    
    while True:
        draw_menu(menu_cursor, big_model, middle_model, small_model)
        
        if ARROW_SUPPORT:
            key = get_key()
            
            if key == 'UP' or key == 'k':
                menu_cursor = (menu_cursor - 1) % 4
                continue
            elif key == 'DOWN' or key == 'j':
                menu_cursor = (menu_cursor + 1) % 4
                continue
            elif key == 'ENTER':
                if menu_cursor == 3:  # Save & Quit
                    print(f"\n✅ Models selected:")
                    print(f"   BIG_MODEL={big_model}")
                    print(f"   MIDDLE_MODEL={middle_model}")
                    print(f"   SMALL_MODEL={small_model}")
                    print("\nUpdate your .env file with these values.")
                    return
                elif menu_cursor == 4:  # Back
                    print("\n🔙 Returning to settings...")
                    return
                else:
                    # Enter model picker for selected slot
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[menu_cursor]
                    selected = pick_model(all_models, slot)
                    if selected:
                        if slot == 'big':
                            big_model = selected
                        elif slot == 'middle':
                            middle_model = selected
                        elif slot == 'small':
                            small_model = selected
            elif key == 'q':
                print("\n❌ Cancelled")
                return
        else:
            # Fallback to text input
            cmd = input("→ ").strip()
            if cmd == 'q':
                print("\n❌ Cancelled")
                return
            elif cmd.isdigit():
                choice = int(cmd) - 1
                if choice == 3:
                    print(f"\n✅ Models selected:")
                    print(f"   BIG_MODEL={big_model}")
                    print(f"   MIDDLE_MODEL={middle_model}")
                    print(f"   SMALL_MODEL={small_model}")
                    print("\nUpdate your .env file with these values.")
                    return
                elif 0 <= choice < 3:
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[choice]
                    selected = pick_model(all_models, slot)
                    if selected:
                        if slot == 'big':
                            big_model = selected
                        elif slot == 'middle':
                            middle_model = selected
                        elif slot == 'small':
                            small_model = selected


def pick_model(all_models: List[str], slot: str) -> Optional[str]:
    """Pick a model with arrow keys or typing."""
    # State
    show_all = False
    search_query = ""
    page = 0
    cursor = 0
    
    # Get filtered models
    def get_current_models():
        if search_query:
            return [m for m in all_models if search_query.lower() in m.lower()]
        elif show_all:
            return all_models
        else:
            return model_filter.get_filtered_models(
                all_models,
                include_free=True,
                include_top=True,
                include_recent=True,
                max_total=60
            )
    
    models = get_current_models()
    rows, cols = get_terminal_size()
    per_page = rows - 15  # Reserve space for UI chrome
    
    while True:
        # Draw UI with cursor
        draw_model_picker(models, page, per_page, cursor, search_query, slot, show_all)
        
        # Get command
        try:
            if ARROW_SUPPORT:
                key = get_key()
                
                if key == 'UP' or key == 'k':
                    if cursor > 0:
                        cursor -= 1
                        if cursor < page * per_page:
                            page -= 1
                elif key == 'DOWN' or key == 'j':
                    if cursor < len(models) - 1:
                        cursor += 1
                        if cursor >= (page + 1) * per_page:
                            page += 1
                elif key == 'ENTER':
                    return models[cursor]
                elif key == 'q' or key == '\x1b':  # ESC
                    return None
                elif key == 'a':
                    show_all = not show_all
                    search_query = ""
                    models = get_current_models()
                    page = 0
                    cursor = 0
                elif key == '/':
                    search_query = input("Search: ").strip()
                    models = get_current_models()
                    page = 0
                    cursor = 0
            else:
                cmd = input("→ ").strip()
                if not cmd:
                    continue
                
                if cmd.lower() == 'q':
                    return None
                elif cmd.lower() == 'n':
                    total_pages = (len(models) + per_page - 1) // per_page
                    if page < total_pages - 1:
                        page += 1
                elif cmd.lower() == 'p':
                    if page > 0:
                        page -= 1
                elif cmd.lower() == 'a':
                    show_all = not show_all
                    search_query = ""
                    models = get_current_models()
                    page = 0
                elif cmd.startswith('/'):
                    search_query = cmd[1:].strip()
                    models = get_current_models()
                    page = 0
                elif cmd.isdigit():
                    idx = int(cmd) - 1
                    if 0 <= idx < len(models):
                        return models[idx]
                elif cmd.lower().startswith('paste '):
                    return cmd[6:].strip()
        except (EOFError, KeyboardInterrupt):
            return None


def draw_model_picker(
    models: List[str],
    page: int,
    per_page: int,
    cursor: int,
    search_query: str,
    slot: str,
    show_all: bool
):
    """Draw the model picker UI with cursor."""
    clear_screen()
    rows, cols = get_terminal_size()
    
    # Header
    print("╔" + "═" * (cols - 2) + "╗")
    print("║" + f" SELECT MODEL FOR {slot.upper()} ".center(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    
    # Model list header
    mode = "ALL MODELS" if show_all else "RECOMMENDED"
    total_models = len(models)
    total_pages = (total_models + per_page - 1) // per_page
    current_page = page + 1
    
    header = f" {mode} ({total_models} models) - Page {current_page}/{total_pages} "
    if search_query:
        header += f"- Search: '{search_query}' "
    print("║" + header.ljust(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print(f"║ {'#':<3}  {'Model':<45} {'CTX':>6} {'OUT':>6}  {'Tags':<15}║")
    print("╠" + "─" * (cols - 2) + "╣")
    
    # Model list (paginated)
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_models)
    
    for i in range(start_idx, end_idx):
        model_id = models[i]
        
        # Determine if selected
        selected_for = None
        # Only passed if we knew the slot, but here we just show the picker
        # The picker doesn't know about big/middle/small choices unless we pass them?
        # Actually pick_model doesn't use selected_map logic from draw_ui.
        # It's fine.
        
        cursor_marker = "→" if i == cursor else " "
        # Pass max_width = cols - 4 (borders/padding)
        line_content = format_model_line(i + 1, model_id, None, max_width=cols-6)
        
        print(f"║ {cursor_marker} {line_content} ║")
    
    # Fill remaining space
    displayed = end_idx - start_idx
    max_display = rows - 15
    for _ in range(max_display - displayed):
        print("║" + " " * (cols - 2) + "║")
    
    # Footer
    print("╠" + "═" * (cols - 2) + "╣")
    if ARROW_SUPPORT:
        print("║ CONTROLS:".ljust(cols - 1) + "║")
        print("║   ↑/↓ or j/k  - Navigate | Enter - Select | / - Search".ljust(cols - 1) + "║")
        print("║   a - Toggle All/Recommended | q/ESC - Cancel".ljust(cols - 1) + "║")
    else:
        print("║ COMMANDS:".ljust(cols - 1) + "║")
        print("║   [number] - Select | n/p - Next/Prev | / - Search".ljust(cols - 1) + "║")
        print("║   a - Toggle All/Recommended | q - Cancel".ljust(cols - 1) + "║")
    print("╚" + "═" * (cols - 2) + "╝")
    print()


def run_model_selector_old():
    """Run the interactive model selector with static UI (old text-based version)."""
    from src.core.config import config
    
    # Load models
    all_models = load_all_models()
    if not all_models:
        print("❌ No models found. Run the scraper first.")
        return
    
    # State
    show_all = False
    search_query = ""
    page = 0
    big_model = config.big_model
    middle_model = config.middle_model
    small_model = config.small_model
    
    # Get filtered models
    def get_current_models():
        if search_query:
            return [m for m in all_models if search_query.lower() in m.lower()]
        elif show_all:
            return all_models
        else:
            return model_filter.get_filtered_models(
                all_models,
                include_free=True,
                include_top=True,
                include_recent=True,
                max_total=60
            )
    
    models = get_current_models()
    rows, cols = get_terminal_size()
    per_page = rows - 15  # Reserve space for UI chrome
    
    while True:
        # Draw UI
        draw_ui(models, page, per_page, search_query, big_model, middle_model, small_model, show_all)
        
        # Get command
        try:
            cmd = input("→ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Cancelled")
            return
        
        if not cmd:
            continue
        
        # Handle commands
        if cmd.lower() == 'q':
            # Save to .env
            print(f"\n✅ Models selected:")
            print(f"   BIG_MODEL={big_model}")
            print(f"   MIDDLE_MODEL={middle_model}")
            print(f"   SMALL_MODEL={small_model}")
            print("\nUpdate your .env file with these values.")
            return
        
        elif cmd.lower() == 'n':
            # Next page
            total_pages = (len(models) + per_page - 1) // per_page
            if page < total_pages - 1:
                page += 1
        
        elif cmd.lower() == 'p':
            # Previous page
            if page > 0:
                page -= 1
        
        elif cmd.lower() == 'a':
            # Toggle all/recommended
            show_all = not show_all
            search_query = ""
            models = get_current_models()
            page = 0
        
        elif cmd.startswith('/'):
            # Search
            search_query = cmd[1:].strip()
            models = get_current_models()
            page = 0
        
        elif cmd.lower().startswith('paste '):
            # Paste custom model
            custom_model = cmd[6:].strip()
            if custom_model:
                slot = input(f"Assign '{custom_model}' to [b/m/s]: ").strip().lower()
                if slot == 'b':
                    big_model = custom_model
                elif slot == 'm':
                    middle_model = custom_model
                elif slot == 's':
                    small_model = custom_model
        
        else:
            # Try to parse as number + slot
            parts = cmd.split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].lower() in ['b', 'm', 's']:
                idx = int(parts[0]) - 1
                slot = parts[1].lower()
                
                if 0 <= idx < len(models):
                    selected_model = models[idx]
                    if slot == 'b':
                        big_model = selected_model
                    elif slot == 'm':
                        middle_model = selected_model
                    elif slot == 's':
                        small_model = selected_model
                else:
                    print(f"❌ Invalid model number: {parts[0]}")
                    input("Press Enter to continue...")
            else:
                print(f"❌ Unknown command: {cmd}")
                input("Press Enter to continue...")

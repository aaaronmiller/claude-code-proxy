"""Interactive model selector with static TUI (no scrolling spam)."""

import json
import os
import sys
import socket
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from src.services.models.model_filter import get_available_models, filter_models, model_filter
from src.services.models.modes import ModeManager
from src.services.models.recommender import ModelRecommender
from src.services.usage.model_limits import get_model_limits
from src.cli.env_utils import update_env_values

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

# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

PROVIDERS = {
    "vibeproxy": {
        "name": "🌌 VibeProxy/Antigravity",
        "endpoint": "http://127.0.0.1:8317/v1",
        "api_key_env": None,  # Uses OAuth
        "detect_port": 8317,
        "description": "Local OAuth (Claude/Gemini via Google)",
        "model_prefix": "",
    },
    "openrouter": {
        "name": "🚀 OpenRouter",
        "endpoint": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "description": "352+ models, free tier available",
        "model_prefix": "",
    },
    "gemini": {
        "name": "🌟 Google Gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GOOGLE_API_KEY",
        "description": "Direct Gemini API",
        "model_prefix": "",
    },
    "openai": {
        "name": "🤖 OpenAI",
        "endpoint": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "description": "GPT-4, o1, DALL-E",
        "model_prefix": "",
    },
    "ollama": {
        "name": "🏠 Ollama",
        "endpoint": "http://localhost:11434/v1",
        "api_key_env": None,
        "detect_port": 11434,
        "description": "Local models (free)",
        "model_prefix": "",
    },
    "custom": {
        "name": "⚙️  Custom Endpoint",
        "endpoint": "",
        "api_key_env": None,
        "description": "Configure manually",
        "model_prefix": "",
    },
}


def detect_provider_status(provider_id: str) -> Tuple[bool, str]:
    """
    Detect if a provider is available.
    Returns (is_available, status_message).
    """
    provider = PROVIDERS.get(provider_id, {})
    
    # Check port-based detection (VibeProxy, Ollama)
    if "detect_port" in provider:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', provider["detect_port"]))
            sock.close()
            if result == 0:
                return True, "✓ RUNNING"
            else:
                return False, "○ Not running"
        except Exception:
            return False, "○ Error"
    
    # Check API key based detection
    if provider.get("api_key_env"):
        key = os.environ.get(provider["api_key_env"], "")
        if key and key not in ["dummy", "your-key-here", ""]:
            return True, f"✓ Key set"
        else:
            return False, f"○ No API key"
    
    # Custom always "available"
    if provider_id == "custom":
        return True, "Manual config"
    
    return False, "Unknown"


def get_available_providers() -> List[Tuple[str, str, str, bool]]:
    """
    Get list of available providers with status.
    Returns list of (provider_id, display_name, status, is_available).
    """
    result = []
    for pid, pinfo in PROVIDERS.items():
        is_available, status = detect_provider_status(pid)
        result.append((pid, pinfo["name"], status, is_available))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def visual_len(s: str) -> int:
    """Calculate visual length of string, accounting for double-width emojis."""
    # Heuristic: these known emojis/symbols are usually double-width in terminals
    # or cause misalignment.
    double_width_chars = "🌌🚀🌟🤖🏠⚙️▶★🆓🧠👁️🔧✨🏆⭐⚠️✅❌⏳💡"
    count = sum(1 for c in s if c in double_width_chars)
    return len(s) + count

def pad_visual(s: str, width: int, align: str = '<') -> str:
    """Pad string to visual width."""
    vlen = visual_len(s)
    padding = max(0, width - vlen)
    if align == '<':
        return s + " " * padding
    elif align == '>':
        return " " * padding + s
    elif align == '^':
        left = padding // 2
        right = padding - left
        return " " * left + s + " " * right
    return s

def draw_provider_menu(cursor: int, slot: str, current_provider: Optional[str] = None):
    """Draw the provider selection menu."""
    clear_screen()
    rows, cols = get_terminal_size()
    
    # Get ONLY available providers for selection (unless Current is unavailable, show it)
    all_providers = get_available_providers()
    
    # Filter: Show available OR custom OR currently selected
    # User requested "only endpoints which have valid api keys"
    providers = []
    for p in all_providers:
        pid, _, _, is_avail = p
        # Always show custom, vibeproxy (local), ollama (local)
        # Show others only if available (API key set)
        if is_avail or pid in ["custom", "vibeproxy", "ollama"] or pid == current_provider:
             providers.append(p)
    
    # If filtered list is empty (shouldn't happen due to custom), fall back
    if not providers:
        providers = all_providers

    print("╔" + "═" * (cols - 2) + "╗")
    title = f" SELECT PROVIDER FOR {slot.upper()} MODEL "
    print("║" + title.center(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║" + " " * (cols - 2) + "║")
    
    for i, (pid, name, status, is_available) in enumerate(providers):
        if i == cursor:
            marker = "▶"
            style_start = "★ " if is_available else "  "
        else:
            marker = " "
            style_start = "  " if is_available else "  "
        
        # Show current selection
        current_mark = " [CURRENT]" if pid == current_provider else ""
        
        line = f"  {marker} {name}  {status}{current_mark}"
        desc = f"      {PROVIDERS[pid]['description']}"
        
        # Pad and print using visual length
        print("║" + pad_visual(line, cols - 2) + "║")
        print("║" + pad_visual(desc, cols - 2) + "║")
    
    print("║" + " " * (cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║ CONTROLS:".ljust(cols - 1) + "║")
    print("║   ↑/↓  Navigate   Enter  Select   q  Back".ljust(cols - 1) + "║")
    print("╚" + "═" * (cols - 2) + "╝")
    
    return providers # Return the list we displayed so caller can map cursor correctly

def pick_provider(slot: str, current_provider: Optional[str] = None) -> Optional[str]:
    """Let user pick a provider for the given slot."""
    # Initial fetch to get cursor
    temp_providers = get_available_providers() 
    # We need the filtered list to handle cursor correctly.
    # Logic moved inside loop or we refactor draw_provider_menu to return displayed list.
    # Refactored draw_provider_menu to return the displayed list.
    
    cursor = 0
    # Try to find current in the *filtered* list? 
    # We don't have the filtered list yet.
    # Let's run drawing once to get logic or duplicate filtering logic.
    
    # Filter logic duplicate:
    all_p = get_available_providers()
    providers = []
    for p in all_p:
        pid, _, _, is_avail = p
        if is_avail or pid in ["custom", "vibeproxy", "ollama"] or pid == current_provider:
             providers.append(p)
    
    # Find cursor
    if current_provider:
        for i, (pid, _, _, _) in enumerate(providers):
            if pid == current_provider:
                cursor = i
                break
    
    while True:
        displayed_providers = draw_provider_menu(cursor, slot, current_provider)
        # displayed_providers should match 'providers' calculated above if logic is consistent
        # Update 'providers' just in case capability changed? Unlikely in sub-second.
        providers = displayed_providers 
        
        try:
            if ARROW_SUPPORT:
                key = get_key()
                if key == 'UP' or key == 'k':
                    cursor = (cursor - 1) % len(providers)
                elif key == 'DOWN' or key == 'j':
                    cursor = (cursor + 1) % len(providers)
                elif key == 'ENTER':
                    pid, _, _, is_available = providers[cursor]
                    if not is_available and pid not in ["custom"]:
                         # Inform user
                         pass 
                    return pid
                elif key == 'q':
                    return None
            else:
                cmd = input("→ ").strip()
                if cmd == 'q':
                    return None
                elif cmd.isdigit():
                    idx = int(cmd) - 1
                    if 0 <= idx < len(providers):
                        return providers[idx][0]
        except (EOFError, KeyboardInterrupt):
            return None

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

def load_all_models(refresh: bool = False) -> List[str]:
    """Load all available models from the enriched database or use defaults.

    Args:
        refresh: If True, forces a refresh from OpenRouter API

    Priority order:
    1. Live fetch from OpenRouter (if refresh=True)
    2. data/openrouter_models.json (new fetcher format)
    3. data/openrouter_models_enriched.json (enriched data)
    4. models/model_limits.json (legacy)
    5. DEFAULT_MODELS (hardcoded fallback)
    """
    project_root = Path(__file__).parent.parent.parent

    # If refresh requested, use the new fetcher
    if refresh:
        try:
            from src.services.models.openrouter_fetcher import refresh_openrouter_models_sync
            print("🔄 Refreshing models from OpenRouter...")
            data, was_refreshed, error = refresh_openrouter_models_sync(force=True)
            if was_refreshed and data.get('models'):
                print(f"✅ Fetched {len(data['models'])} models")
                return sorted([m['id'] for m in data['models']])
            elif error:
                print(f"⚠️  Refresh failed: {error}")
        except Exception as e:
            print(f"⚠️  Refresh error: {e}")

    # Priority 1: New fetcher cache (openrouter_models.json)
    new_cache_path = project_root / "data" / "openrouter_models.json"
    if new_cache_path.exists():
        try:
            with open(new_cache_path, 'r') as f:
                data = json.load(f)
                if 'models' in data:
                    return sorted([m['id'] for m in data['models']])
        except Exception:
            pass

    # Priority 2: Enriched OpenRouter data
    enriched_path = project_root / "data" / "openrouter_models_enriched.json"
    if enriched_path.exists():
        try:
            with open(enriched_path, 'r') as f:
                data = json.load(f)
                if 'models' in data:
                    return sorted([m['id'] for m in data['models']])
        except Exception:
            pass

    # Priority 3: Legacy model limits
    legacy_path = project_root / "models" / "model_limits.json"
    if legacy_path.exists():
        try:
            with open(legacy_path, 'r') as f:
                data = json.load(f)
                return sorted(data.keys())
        except Exception:
            pass

    return sorted(DEFAULT_MODELS)


def refresh_models_cache() -> Tuple[bool, str]:
    """
    Force refresh the models cache from OpenRouter.

    Returns:
        Tuple of (success, message)
    """
    try:
        from src.services.models.openrouter_fetcher import refresh_openrouter_models_sync
        data, was_refreshed, error = refresh_openrouter_models_sync(force=True)

        if error:
            return False, f"Refresh failed: {error}"
        if was_refreshed:
            return True, f"Refreshed {len(data.get('models', []))} models"
        return True, f"Using cached data ({len(data.get('models', []))} models)"
    except Exception as e:
        return False, f"Error: {str(e)}"


# Cache for enriched model data
_enriched_models_cache: Optional[dict] = None

def get_enriched_model_info(model_id: str) -> Optional[dict]:
    """Get enriched metadata for a specific model.
    
    Returns dict with: context_length, max_completion_tokens, supports_reasoning,
    supports_tools, supports_vision, pricing, description, etc.
    """
    global _enriched_models_cache
    
    if _enriched_models_cache is None:
        project_root = Path(__file__).parent.parent.parent
        enriched_path = project_root / "data" / "openrouter_models_enriched.json"
        
        if enriched_path.exists():
            try:
                with open(enriched_path, 'r') as f:
                    data = json.load(f)
                    # Build lookup dict by model ID
                    _enriched_models_cache = {m['id']: m for m in data.get('models', [])}
            except Exception:
                _enriched_models_cache = {}
        else:
            _enriched_models_cache = {}
    
    return _enriched_models_cache.get(model_id)


def format_model_line(idx: int, model_id: str, selected_for: Optional[str] = None, max_width: int = 80) -> str:
    """Format a single model line for display with enriched capabilities."""
    # Try to get enriched data first
    enriched = get_enriched_model_info(model_id)
    
    if enriched:
        context = enriched.get('context_length', 0)
        output = enriched.get('max_completion_tokens', 0)
    else:
        context, output = get_model_limits(model_id)
    
    def fmt(tokens):
        if tokens >= 1000000:
            return f"{tokens/1000000:.1f}M"
        elif tokens >= 1000:
            return f"{tokens/1000:.0f}k"
        return str(tokens) if tokens else "?"
    
    # Badges - use enriched data if available
    badges = []
    
    if enriched:
        # Enriched capability badges
        if enriched.get('pricing', {}).get('is_free', False):
            badges.append("🆓")  # Free
        if enriched.get('supports_reasoning', False):
            badges.append("🧠")  # Reasoning
        if enriched.get('supports_vision', False):
            badges.append("👁️")  # Vision
        if enriched.get('supports_tools', False):
            badges.append("🔧")  # Tools
    else:
        # Fallback to old badges
        if model_filter.is_new_model(model_id):
            badges.append("✨")  # New
        if model_filter.is_free_model(model_id):
            badges.append("🆓")  # Free
        if model_filter.is_top_model(model_id):
            badges.append("🏆")  # Top/Popular
    
    if model_filter.get_recently_used_models(20) and model_id in model_filter.get_recently_used_models(20):
        badges.append("⭐")  # Used
    if selected_for:
        badges.append(f"[{selected_for}]")
    
    badge_str = " ".join(badges) if badges else ""
    badge_len = visual_len(badge_str) + 1 if badge_str else 0
    
    # Dynamic name width
    suffix_len = 16 + badge_len
    prefix_len = 6
    name_width = max(10, max_width - prefix_len - suffix_len)
    
    display_name = model_id
    if len(display_name) > name_width:
        display_name = display_name[:name_width-3] + "..."
    
    # Manually align using visual width
    # f"{idx:3}. {display_name:<{name_width}} {fmt(context):>6} {fmt(output):>6}  {badge_str}"
    
    part1 = f"{idx:3}. "
    part2 = pad_visual(display_name, name_width)
    part3 = f" {fmt(context):>6} {fmt(output):>6}  "
    part4 = badge_str
    
    return part1 + part2 + part3 + part4


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
    print(f"║ BIG:    {pad_visual(big_model or 'not set', cols-12)}║")
    print(f"║ MIDDLE: {pad_visual(middle_model or 'not set', cols-12)}║")
    print(f"║ SMALL:  {pad_visual(small_model or 'not set', cols-12)}║")
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
        line = format_model_line(i + 1, model_id, selected_for, cols - 6)
        # Truncate to fit terminal width
        if visual_len(line) > cols - 4:
            # Need visual truncate
            line = line[:cols - 7] + "..." # Rough safety
        print(f"║ {pad_visual(line, cols-4)} ║")
    
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


def draw_menu(cursor: int, big_model: str, middle_model: str, small_model: str,
               big_provider: str = None, middle_provider: str = None, small_provider: str = None):
    """Draw the main menu for selecting which slot to configure."""
    clear_screen()
    rows, cols = get_terminal_size()
    
    # Helper to format provider display
    def fmt_provider(pid: str) -> str:
        if not pid:
            return "default"
        return PROVIDERS.get(pid, {}).get("name", pid).replace("🌌 ", "").replace("🚀 ", "").replace("🌟 ", "").replace("🤖 ", "").replace("🏠 ", "").replace("⚙️  ", "")
    
    print("╔" + "═" * (cols - 2) + "╗")
    print("║" + " MODEL & PROVIDER SELECTOR ".center(cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║" + " " * (cols - 2) + "║")
    
    # Slot options with provider info
    options = [
        ("BIG", big_model or "not set", fmt_provider(big_provider)),
        ("MIDDLE", middle_model or "not set", fmt_provider(middle_provider)),
        ("SMALL", small_model or "not set", fmt_provider(small_provider)),
    ]

    for i, (slot, model, provider) in enumerate(options):
        marker = "▶" if i == cursor else " "
        if model and model != "not set":
            line = f"  {marker} {slot}: {model} @ {provider}"
        else:
            line = f"  {marker} {slot}: (not configured)"
        print("║ " + pad_visual(line, cols - 3) + "║")
    
    print("║" + " " * (cols - 2) + "║")
    
    # Action options
    actions = [
        ("SAVE & QUIT", ""),
        ("BACK TO SETTINGS", ""),
    ]
    for i, (label, _) in enumerate(actions):
        marker = "▶" if i + 3 == cursor else " "
        line = f"  {marker} {label}"
        print("║ " + pad_visual(line, cols - 3) + "║")
    
    print("║" + " " * (cols - 2) + "║")
    print("╠" + "═" * (cols - 2) + "╣")
    print("║ CONTROLS:".ljust(cols - 1) + "║")
    print("║   ↑/↓ or j/k  Navigate    Enter  Configure    q  Quit".ljust(cols - 1) + "║")
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
    
    # State - models
    big_model = config.big_model
    middle_model = config.middle_model
    small_model = config.small_model
    
    # State - providers (detect from current endpoints)
    def detect_current_provider(endpoint: str) -> Optional[str]:
        if not endpoint:
            return None
        for pid, pinfo in PROVIDERS.items():
            if pinfo.get("endpoint") and pinfo["endpoint"] in endpoint:
                return pid
        if "127.0.0.1:8317" in endpoint or "localhost:8317" in endpoint:
            return "vibeproxy"
        if "openrouter.ai" in endpoint:
            return "openrouter"
        if "googleapis" in endpoint:
            return "gemini"
        if "openai.com" in endpoint:
            return "openai"
        if ":11434" in endpoint:
            return "ollama"
        return None
    
    # Detect initial providers from config
    big_provider = detect_current_provider(getattr(config, 'big_endpoint', '') or config.openai_base_url)
    middle_provider = detect_current_provider(getattr(config, 'middle_endpoint', '') or config.openai_base_url)
    small_provider = detect_current_provider(getattr(config, 'small_endpoint', '') or config.openai_base_url)
    
    # Main menu loop
    menu_cursor = 0
    
    while True:
        draw_menu(menu_cursor, big_model, middle_model, small_model,
                  big_provider, middle_provider, small_provider)
        
        if ARROW_SUPPORT:
            key = get_key()
            
            if key == 'UP' or key == 'k':
                menu_cursor = (menu_cursor - 1) % 5
                continue
            elif key == 'DOWN' or key == 'j':
                menu_cursor = (menu_cursor + 1) % 5
                continue
            elif key == 'ENTER':
                if menu_cursor == 3:  # Save & Quit
                    # Save to .env using shared utility
                    updates = {
                        "BIG_MODEL": big_model,
                        "MIDDLE_MODEL": middle_model, 
                        "SMALL_MODEL": small_model,
                    }
                    # Add provider/endpoint settings if custom (Seamless Hybrid)
                    # BIG
                    if big_provider and big_provider not in ["vibeproxy", "ollama", "custom"]:
                        updates["ENABLE_BIG_ENDPOINT"] = "true"
                        updates["BIG_ENDPOINT"] = PROVIDERS.get(big_provider, {}).get("endpoint", "")
                        # Seamless API Key
                        key_env = PROVIDERS.get(big_provider, {}).get("api_key_env")
                        if key_env:
                            val = os.environ.get(key_env)
                            if not val and key_env == "OPENROUTER_API_KEY":
                                val = os.environ.get("PROVIDER_API_KEY")
                            if val:
                                updates["BIG_API_KEY"] = val
                    elif big_provider == "vibeproxy":
                        updates["ENABLE_BIG_ENDPOINT"] = "false"
                        updates["BIG_API_KEY"] = ""
                        
                    # MIDDLE
                    if middle_provider and middle_provider not in ["vibeproxy", "ollama", "custom"]:
                        updates["ENABLE_MIDDLE_ENDPOINT"] = "true"
                        updates["MIDDLE_ENDPOINT"] = PROVIDERS.get(middle_provider, {}).get("endpoint", "")
                        # Seamless API Key
                        key_env = PROVIDERS.get(middle_provider, {}).get("api_key_env")
                        if key_env:
                            val = os.environ.get(key_env)
                            if not val and key_env == "OPENROUTER_API_KEY":
                                val = os.environ.get("PROVIDER_API_KEY")
                            if val:
                                updates["MIDDLE_API_KEY"] = val
                    elif middle_provider == "vibeproxy":
                        updates["ENABLE_MIDDLE_ENDPOINT"] = "false"
                        updates["MIDDLE_API_KEY"] = ""

                    # SMALL
                    if small_provider and small_provider not in ["vibeproxy", "ollama", "custom"]:
                        updates["ENABLE_SMALL_ENDPOINT"] = "true"
                        updates["SMALL_ENDPOINT"] = PROVIDERS.get(small_provider, {}).get("endpoint", "")
                        # Seamless API Key
                        key_env = PROVIDERS.get(small_provider, {}).get("api_key_env")
                        if key_env:
                            val = os.environ.get(key_env)
                            if not val and key_env == "OPENROUTER_API_KEY":
                                val = os.environ.get("PROVIDER_API_KEY")
                            if val:
                                updates["SMALL_API_KEY"] = val
                    elif small_provider == "vibeproxy":
                        updates["ENABLE_SMALL_ENDPOINT"] = "false" 
                        updates["SMALL_API_KEY"] = ""
                    
                    print("\n⏳ Saving configuration...")
                    update_env_values(updates)
                    print(f"\n✅ Configuration saved!")
                    print(f"   BIG:    {big_model} @ {big_provider or 'default'}")
                    print(f"   MIDDLE: {middle_model} @ {middle_provider or 'default'}")
                    print(f"   SMALL:  {small_model} @ {small_provider or 'default'}")
                    print("\n💡 Restart proxy for changes to take effect.")
                    input("\nPress Enter to continue...")
                    return
                elif menu_cursor == 4:  # Back
                    print("\n🔙 Returning to settings...")
                    return
                else:
                    # Configure slot: first pick provider, then model
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[menu_cursor]
                    current_provider = [big_provider, middle_provider, small_provider][menu_cursor]
                    
                    # Step 1: Pick provider
                    new_provider = pick_provider(slot, current_provider)
                    if new_provider:
                        # Step 2: Pick model (filtered by provider if applicable)
                        selected = pick_model(all_models, slot, new_provider)
                        if selected:
                            if slot == 'big':
                                big_model = selected
                                big_provider = new_provider
                            elif slot == 'middle':
                                middle_model = selected
                                middle_provider = new_provider
                            elif slot == 'small':
                                small_model = selected
                                small_provider = new_provider
            elif key == 'q':
                print("\n❌ Cancelled (no changes saved)")
                return
        else:
            # Fallback to text input
            cmd = input("→ ").strip()
            if cmd == 'q':
                print("\n❌ Cancelled")
                return
            elif cmd.isdigit():
                choice = int(cmd) - 1
                if choice == 3:  # Save
                    updates = {
                        "BIG_MODEL": big_model,
                        "MIDDLE_MODEL": middle_model,
                        "SMALL_MODEL": small_model,
                    }
                    update_env_values(updates)
                    print(f"\n✅ Saved!")
                    return
                elif 0 <= choice < 3:
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[choice]
                    new_provider = pick_provider(slot)
                    if new_provider:
                        selected = pick_model(all_models, slot, new_provider)
                        if selected:
                            if slot == 'big':
                                big_model = selected
                                big_provider = new_provider
                            elif slot == 'middle':
                                middle_model = selected
                                middle_provider = new_provider
                            elif slot == 'small':
                                small_model = selected
                                small_provider = new_provider


def pick_model(all_models: List[str], slot: str, provider: Optional[str] = None) -> Optional[str]:
    """Pick a model with arrow keys or typing.
    
    Args:
        all_models: List of all available models
        slot: Slot name (big, middle, small)
        provider: Optional provider to filter/recommend models for
    """
    # State
    show_all = False
    search_query = ""
    page = 0
    cursor = 0
    
    # Filter models based on provider first
    filtered_base_models = []
    if provider == "vibeproxy":
        # VibeProxy specific models
        filtered_base_models = [m for m in all_models if m.startswith("vibeproxy/") or m.startswith("antigravity/")]
        # Also allow openrouter models if user really wants? No, user requested filtering.
    elif provider == "openai":
        filtered_base_models = [m for m in all_models if m.startswith("openai/") or m.startswith("gpt-")]
    elif provider == "gemini":
        filtered_base_models = [m for m in all_models if m.startswith("google/") or m.startswith("gemini")]
    elif provider == "ollama":
        # Ollama models usually don't have prefix in some lists, but here they might not be in all_models?
        # If ollama models are not in all_models, we might need to fetch them?
        # For now assume all_models contains them or we fallback.
        filtered_base_models = [m for m in all_models if m.startswith("ollama") or not "/" in m] # Wild guess
    elif provider == "openrouter":
        # Show everything for OpenRouter as it aggregates
        filtered_base_models = all_models
    else:
        filtered_base_models = all_models
        
    if not filtered_base_models and provider:
        # Fallback if strict filter returned nothing (e.g. data mismatch)
        filtered_base_models = all_models

    # Get filtered models (search + tags)
    def get_current_models():
        candidates = filtered_base_models
        
        if search_query:
            return [m for m in candidates if search_query.lower() in m.lower()]
        elif show_all:
            return candidates
        else:
            return model_filter.get_filtered_models(
                candidates,
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
                current_input = input("→ ").strip()
                cmd = current_input
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
        # Pass max_width = cols - 6 (borders/padding/marker)
        line_content = format_model_line(i + 1, model_id, None, max_width=cols-6)
        
        full_line = f" {cursor_marker} {line_content}"
        print(f"║{pad_visual(full_line, cols-2)}║")
    
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
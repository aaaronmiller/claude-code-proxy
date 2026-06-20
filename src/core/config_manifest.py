"""
Config Manifest — single source of truth for all configurable settings.

Every setting is defined once here with:
  - env_var:     the environment variable name
  - type:        Python type for validation/casting
  - default:     default value (None = no default)
  - description: human-readable description
  - group:       logical grouping for UI sections
  - cli_flag:    argparse flag name (None = not CLI-exposed)
  - secret:      True if value should be masked in output

Consumers:
  - CLI (start_proxy.py): generate argparse from manifest
  - Web UI (/api/config): expose all settings via GET, PATCH via POST /api/settings
  - TUI (advanced_config.py): render form sections from manifest groups
  - .env.example: generated documentation

Usage:
    from src.core.config_manifest import SETTINGS, get_group, get_env_dict

    # All settings
    for s in SETTINGS:
        print(s.env_var, s.default)

    # By group
    for s in get_group("models"):
        print(s.cli_flag, s.description)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type
import os


@dataclass
class Setting:
    env_var: str
    type: Type
    default: Any
    description: str
    group: str                      # UI section grouping
    cli_flag: Optional[str] = None  # e.g. "--big-model"
    choices: Optional[List[str]] = None
    secret: bool = False            # mask in output
    tui_widget: str = "input"       # input | toggle | select | number | textarea
    web_component: str = "input"    # input | switch | select | number | textarea | slider
    units: Optional[str] = None     # display units, e.g. "tokens", "seconds", "USD"
    min_val: Optional[float] = None
    max_val: Optional[float] = None


# ── All configurable settings ─────────────────────────────────────────────────
SETTINGS: List[Setting] = [

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: server
    # ════════════════════════════════════════════════════════════════════════
    Setting("HOST", str, "0.0.0.0", "Server bind address", "server",
            cli_flag="--host", tui_widget="input", web_component="input"),
    Setting("PORT", int, 8082, "Server port", "server",
            cli_flag="--port", tui_widget="number", web_component="number",
            min_val=1024, max_val=65535),
    Setting("LOG_LEVEL", str, "info", "Logging verbosity", "server",
            cli_flag="--log-level", choices=["debug", "info", "warning", "error"],
            tui_widget="select", web_component="select"),
    Setting("REQUEST_TIMEOUT", int, 120, "Upstream request timeout", "server",
            cli_flag="--request-timeout", tui_widget="number", web_component="number",
            units="seconds", min_val=10, max_val=600),
    Setting("MAX_RETRIES", int, 2, "Max upstream retries before cascade", "server",
            cli_flag="--max-retries", tui_widget="number", web_component="number",
            min_val=0, max_val=10),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: models
    # ════════════════════════════════════════════════════════════════════════
    Setting("BIG_MODEL", str, "", "BIG tier model (opus-level)", "models",
            cli_flag="--big-model", tui_widget="input", web_component="input"),
    Setting("MIDDLE_MODEL", str, "", "MIDDLE tier model (sonnet-level)", "models",
            cli_flag="--middle-model", tui_widget="input", web_component="input"),
    Setting("SMALL_MODEL", str, "", "SMALL tier model (haiku-level)", "models",
            cli_flag="--small-model", tui_widget="input", web_component="input"),
    Setting("BIG_CASCADE", str, "", "BIG tier fallback models (comma-separated)", "models",
            cli_flag="--big-cascade", tui_widget="textarea", web_component="textarea"),
    Setting("MIDDLE_CASCADE", str, "", "MIDDLE tier fallback models (comma-separated)", "models",
            cli_flag="--middle-cascade", tui_widget="textarea", web_component="textarea"),
    Setting("SMALL_CASCADE", str, "", "SMALL tier fallback models (comma-separated)", "models",
            cli_flag="--small-cascade", tui_widget="textarea", web_component="textarea"),
    Setting("MODEL_CASCADE", bool, True, "Enable cascade fallback on model failures", "models",
            cli_flag="--model-cascade", tui_widget="toggle", web_component="switch"),
    Setting("MODEL_CASCADE_DAILY_LIMIT", int, 0,
            "Max cascade requests per model per day (0=unlimited)", "models",
            cli_flag="--cascade-daily-limit", tui_widget="number", web_component="number",
            units="requests"),
    Setting("OPENROUTER_FALLBACK_MODELS", str, "",
            "Dynamic OpenRouter fallback pool (comma-separated)", "models",
            cli_flag="--or-fallbacks", tui_widget="textarea", web_component="textarea"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: fusion
    # ════════════════════════════════════════════════════════════════════════
    Setting("FUSION_PROFILE", str, "free",
            "Default OpenRouter Fusion profile name", "fusion",
            cli_flag="--fusion-profile", tui_widget="input", web_component="input"),
    Setting("FUSION_ALIASES", str, "fusion,ccp/fusion,openrouter/fusion",
            "Model aliases that trigger OpenRouter Fusion", "fusion",
            cli_flag="--fusion-aliases", tui_widget="textarea", web_component="textarea"),
    Setting("FUSION_FREE_ANALYSIS_MODELS", str,
            "openrouter/free,openrouter/free,openrouter/free",
            "Free Fusion profile panel models", "fusion",
            cli_flag="--fusion-free-analysis-models", tui_widget="textarea",
            web_component="textarea"),
    Setting("FUSION_FREE_MODEL", str, "openrouter/free",
            "Free Fusion profile judge/final model", "fusion",
            cli_flag="--fusion-free-model", tui_widget="input", web_component="input"),
    Setting("FUSION_FREE_PRESET", str, "",
            "Optional OpenRouter Fusion preset for the free profile", "fusion",
            cli_flag="--fusion-free-preset", tui_widget="input", web_component="input"),
    Setting("FUSION_FREE_FORCE", bool, True,
            "Force Fusion invocation for one-shot requests when no other tools compete", "fusion",
            cli_flag="--fusion-free-force", tui_widget="toggle", web_component="switch"),
    Setting("FUSION_PROFILES", str, "",
            "JSON map of named Fusion profiles", "fusion",
            cli_flag="--fusion-profiles", tui_widget="textarea", web_component="textarea"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: router_slots
    # ════════════════════════════════════════════════════════════════════════
    Setting("ROUTER_BACKGROUND", str, "", "Model for background/async tasks", "router_slots",
            cli_flag="--router-background", tui_widget="input", web_component="input"),
    Setting("ROUTER_THINK", str, "", "Model for reasoning/thinking requests", "router_slots",
            cli_flag="--router-think", tui_widget="input", web_component="input"),
    Setting("ROUTER_LONG_CONTEXT", str, "", "Model for long-context requests", "router_slots",
            cli_flag="--router-long-context", tui_widget="input", web_component="input"),
    Setting("ROUTER_LONG_CONTEXT_THRESHOLD", int, 60000,
            "Token threshold for long-context routing", "router_slots",
            cli_flag="--router-long-context-threshold", tui_widget="number",
            web_component="slider", units="tokens", min_val=10000, max_val=500000),
    Setting("ROUTER_WEB_SEARCH", str, "", "Model for web search tool requests", "router_slots",
            cli_flag="--router-web-search", tui_widget="input", web_component="input"),
    Setting("ROUTER_IMAGE", str, "", "Model for image/vision requests", "router_slots",
            cli_flag="--router-image", tui_widget="input", web_component="input"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: reasoning
    # ════════════════════════════════════════════════════════════════════════
    Setting("REASONING_EFFORT", str, "low", "Default reasoning effort level", "reasoning",
            cli_flag="--reasoning-effort", choices=["low", "medium", "high"],
            tui_widget="select", web_component="select"),
    Setting("REASONING_MAX_TOKENS", int, 32000, "Max thinking tokens for extended reasoning",
            "reasoning", cli_flag="--reasoning-max-tokens", tui_widget="number",
            web_component="slider", units="tokens", min_val=1000, max_val=100000),
    Setting("REASONING_EXCLUDE", bool, False,
            "Strip thinking tokens from response (reduce output size)", "reasoning",
            cli_flag="--reasoning-exclude", tui_widget="toggle", web_component="switch"),
    Setting("BIG_MODEL_REASONING", str, "",
            "Per-tier reasoning override for BIG model", "reasoning",
            cli_flag="--big-reasoning", tui_widget="input", web_component="input"),
    Setting("MIDDLE_MODEL_REASONING", str, "",
            "Per-tier reasoning override for MIDDLE model", "reasoning",
            cli_flag="--middle-reasoning", tui_widget="input", web_component="input"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: budget
    # ════════════════════════════════════════════════════════════════════════
    Setting("DAILY_TOKEN_BUDGET", int, 0,
            "Max tokens per UTC day across all requests (0=disabled)", "budget",
            cli_flag="--daily-token-budget", tui_widget="number", web_component="number",
            units="tokens"),
    Setting("PER_REQUEST_TOKEN_BUDGET", int, 0,
            "Max input tokens per single request (0=disabled)", "budget",
            cli_flag="--per-request-token-budget", tui_widget="number", web_component="number",
            units="tokens"),
    Setting("DAILY_COST_BUDGET", float, 0.0,
            "Max USD spend per UTC day (0=disabled)", "budget",
            cli_flag="--daily-cost-budget", tui_widget="number", web_component="number",
            units="USD"),
    Setting("MID_STREAM_OUTPUT_BUDGET", int, 0,
            "Stop expensive model after N output tokens, route next turn cheaper (0=disabled)",
            "budget", cli_flag="--mid-stream-budget", tui_widget="number",
            web_component="slider", units="tokens"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: circuit_breaker
    # ════════════════════════════════════════════════════════════════════════
    Setting("CB_FAILURE_THRESHOLD", int, 3,
            "Failures before circuit opens (trips model as 'dead')", "circuit_breaker",
            cli_flag="--cb-failure-threshold", tui_widget="number", web_component="number",
            min_val=1, max_val=20),
    Setting("CB_SUCCESS_THRESHOLD", int, 1,
            "Successes in half-open state before circuit closes", "circuit_breaker",
            cli_flag="--cb-success-threshold", tui_widget="number", web_component="number",
            min_val=1, max_val=10),
    Setting("CB_TIMEOUT_SECONDS", float, 300.0,
            "Cooldown seconds before half-open probe (default: 5 min)", "circuit_breaker",
            cli_flag="--cb-timeout", tui_widget="number", web_component="slider",
            units="seconds", min_val=10, max_val=3600),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: compression
    # ════════════════════════════════════════════════════════════════════════
    Setting("HEADROOM_BYPASS_THRESHOLD", int, 0,
            "Skip headroom compression for requests below this token count (0=disabled)",
            "compression", cli_flag="--headroom-bypass", tui_widget="number",
            web_component="slider", units="tokens"),
    Setting("TOOL_SCHEMA_STRIP", bool, True,
            "Strip redundant fields from tool schemas to reduce token burn", "compression",
            cli_flag="--tool-schema-strip", tui_widget="toggle", web_component="switch"),
    Setting("TOOL_DESC_MAX", int, 200,
            "Max characters for tool-level description", "compression",
            cli_flag="--tool-desc-max", tui_widget="number", web_component="number",
            units="chars"),
    Setting("TOOL_PARAM_DESC_MAX", int, 120,
            "Max characters for per-property description", "compression",
            cli_flag="--tool-param-desc-max", tui_widget="number", web_component="number",
            units="chars"),
    Setting("SEMANTIC_CACHE_ENABLED", bool, True,
            "Enable semantic dedup cache (skips provider call for near-duplicate prompts)",
            "compression", cli_flag="--semantic-cache", tui_widget="toggle",
            web_component="switch"),
    Setting("SEMANTIC_CACHE_THRESHOLD", float, 0.97,
            "Similarity threshold for semantic cache hits (0.0-1.0)", "compression",
            cli_flag="--semantic-cache-threshold", tui_widget="number", web_component="slider",
            min_val=0.5, max_val=1.0),
    Setting("SEMANTIC_CACHE_SIZE", int, 256,
            "Max entries in semantic cache (LRU)", "compression",
            cli_flag="--semantic-cache-size", tui_widget="number", web_component="number"),
    Setting("SEMANTIC_CACHE_TTL", int, 3600,
            "Seconds before semantic cache entry expires", "compression",
            cli_flag="--semantic-cache-ttl", tui_widget="number", web_component="number",
            units="seconds"),
    Setting("TOKEN_COUNT_CACHE_SIZE", int, 512,
            "LRU cache slots for tiktoken encoding results", "compression",
            cli_flag="--token-cache-size", tui_widget="number", web_component="number"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: local_gpu
    # ════════════════════════════════════════════════════════════════════════
    Setting("LOCAL_ENABLED", bool, False,
            "Enable local GPU inference (ollama/llamafile) as 4th cascade tier",
            "local_gpu", cli_flag="--local-enabled", tui_widget="toggle",
            web_component="switch"),
    Setting("LOCAL_MODEL", str, "",
            "Local model name (e.g. llama3.2, mistral, phi3)", "local_gpu",
            cli_flag="--local-model", tui_widget="input", web_component="input"),
    Setting("LOCAL_ENDPOINT", str, "http://localhost:11434/v1",
            "Local inference endpoint (ollama default: :11434/v1)", "local_gpu",
            cli_flag="--local-endpoint", tui_widget="input", web_component="input"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: toolcalls
    # ════════════════════════════════════════════════════════════════════════
    Setting("TOOLCALL_MODELS", str, "",
            "Tool-call capable models prepended to cascade (comma-separated)", "toolcalls",
            cli_flag="--toolcall-models", tui_widget="textarea", web_component="textarea"),
    Setting("TOOLCALL_AUTO_ROUTE", bool, True,
            "Auto-detect tool-call requests and use TOOLCALL_MODELS", "toolcalls",
            cli_flag="--toolcall-auto-route", tui_widget="toggle", web_component="switch"),
    Setting("TOOLCALL_MAX_RETRIES", int, 2,
            "Max retries per model in tool-call cascade", "toolcalls",
            cli_flag="--toolcall-max-retries", tui_widget="number", web_component="number",
            min_val=1, max_val=10),
    Setting("TOOL_OUTPUT_MAX_CHARS", int, 50000,
            "Max characters per tool output (truncation)", "toolcalls",
            cli_flag="--tool-output-max", tui_widget="number", web_component="number",
            units="chars"),
    Setting("TOOL_OUTPUT_TRUNCATION", bool, False,
            "Enable tool output truncation (for small-context models)", "toolcalls",
            cli_flag="--tool-truncation", tui_widget="toggle", web_component="switch"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: auth
    # ════════════════════════════════════════════════════════════════════════
    Setting("PROXY_AUTH_KEY", str, "",
            "Client access key (clients must present this to use the proxy; empty=no auth)",
            "auth", cli_flag="--proxy-auth-key", secret=True,
            tui_widget="input", web_component="input"),
    Setting("OPENROUTER_API_KEY", str, "",
            "OpenRouter API key", "auth", cli_flag="--openrouter-key",
            secret=True, tui_widget="input", web_component="input"),
    Setting("AA_API_KEY", str, "",
            "Artificial Analysis API key (for intelligence benchmark scores)", "auth",
            cli_flag="--aa-key", secret=True, tui_widget="input", web_component="input"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: logging
    # ════════════════════════════════════════════════════════════════════════
    Setting("LOG_FILE", str, "logs/proxy.log", "Proxy log file path", "logging",
            cli_flag="--log-file", tui_widget="input", web_component="input"),
    Setting("LOG_MAX_SIZE_MB", int, 50, "Max log file size before rotation", "logging",
            cli_flag="--log-max-mb", tui_widget="number", web_component="number", units="MB"),
    Setting("LOG_RETENTION_DAYS", int, 7, "Days to keep rotated logs", "logging",
            cli_flag="--log-retention", tui_widget="number", web_component="number",
            units="days"),
    Setting("DEBUG_TRAFFIC_LOG", bool, False,
            "Force full traffic logging (logs/debug_traffic.log). Automatic when LOG_LEVEL=debug — use DEBUG_TRAFFIC_QUIET=true to suppress at debug level.",
            "logging",
            cli_flag="--debug-traffic", tui_widget="toggle", web_component="switch"),
    Setting("DEBUG_TRAFFIC_QUIET", bool, False,
            "Suppress full traffic logging even at LOG_LEVEL=debug. For debug Python logs WITHOUT the heavy traffic dump.",
            "logging",
            cli_flag="--debug-traffic-quiet", tui_widget="toggle", web_component="switch"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: watchdog
    # ════════════════════════════════════════════════════════════════════════
    Setting("PROXY_WATCHDOG", bool, False,
            "Start auto-recovery watchdog pane (checks health, restarts dead services)",
            "watchdog", cli_flag="--proxy-watchdog",
            tui_widget="toggle", web_component="switch"),
    Setting("WATCHDOG_INTERVAL", int, 30,
            "Watchdog health check frequency", "watchdog",
            cli_flag="--watchdog-interval",
            tui_widget="number", web_component="number", units="seconds",
            min_val=5, max_val=300),
    Setting("WATCHDOG_GRACE", int, 5,
            "Seconds to wait before restarting after first failure", "watchdog",
            cli_flag="--watchdog-grace",
            tui_widget="number", web_component="number", units="seconds",
            min_val=1, max_val=60),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: usage_tracking
    # ════════════════════════════════════════════════════════════════════════
    Setting("TRACK_USAGE", bool, True,
            "Record request statistics to SQLite database", "usage_tracking",
            cli_flag="--track-usage", tui_widget="toggle", web_component="switch"),
    Setting("USAGE_TRACKING_DB_PATH", str, "usage_tracking.db",
            "SQLite database file path for usage tracking", "usage_tracking",
            cli_flag="--usage-db", tui_widget="input", web_component="input"),
    Setting("SILENCE_DEPRECATION_WARNINGS", bool, False,
            "Suppress deprecated env-var warnings on startup", "usage_tracking",
            cli_flag="--silence-deprecation-warnings",
            tui_widget="toggle", web_component="switch"),

    # ════════════════════════════════════════════════════════════════════════
    # GROUP: allocator (F18 global quota-aware allocator)
    # ════════════════════════════════════════════════════════════════════════
    Setting("ALLOCATOR_ENABLED", bool, False,
            "Enable the F18 global quota-aware allocator (OFF by default). When off, routing "
            "is unchanged. When on, re-ranks routing per session/role under quota meters.",
            "allocator",
            cli_flag="--allocator-enabled", tui_widget="toggle", web_component="switch"),
]


# ── Helper functions ──────────────────────────────────────────────────────────

def get_group(group: str) -> List[Setting]:
    """Return all settings belonging to a group."""
    return [s for s in SETTINGS if s.group == group]


def get_all_groups() -> List[str]:
    """Return unique group names in definition order."""
    seen = set()
    groups = []
    for s in SETTINGS:
        if s.group not in seen:
            seen.add(s.group)
            groups.append(s.group)
    return groups


def get_by_env_var(env_var: str) -> Optional[Setting]:
    for s in SETTINGS:
        if s.env_var == env_var:
            return s
    return None


def get_by_cli_flag(flag: str) -> Optional[Setting]:
    """Lookup setting by CLI flag (e.g. '--big-model')."""
    for s in SETTINGS:
        if s.cli_flag == flag:
            return s
    return None


def current_env_dict() -> dict:
    """Return {env_var: current_value} for all settings."""
    result = {}
    for s in SETTINGS:
        val = os.environ.get(s.env_var)
        if val is None and s.default is not None:
            val = str(s.default)
        result[s.env_var] = val
    return result


def as_config_response() -> dict:
    """
    Build the /api/config response dict from current environment.
    Masks secret fields. Converts types appropriately.
    """
    resp = {}
    for s in SETTINGS:
        raw = os.environ.get(s.env_var)
        if raw is None:
            val = s.default
        else:
            try:
                if s.type is bool:
                    val = raw.lower() in ("true", "1", "yes")
                elif s.type is int:
                    val = int(raw)
                elif s.type is float:
                    val = float(raw)
                else:
                    val = raw
            except (ValueError, AttributeError):
                val = raw

        if s.secret and val:
            val = "***"

        key = s.env_var.lower()
        resp[key] = val

    return resp


# Group display names for UI
GROUP_LABELS = {
    "server": "Server",
    "models": "Model Tiers",
    "fusion": "OpenRouter Fusion",
    "router_slots": "Router Slots",
    "reasoning": "Reasoning & Thinking",
    "budget": "Budget & Cost Controls",
    "circuit_breaker": "Circuit Breaker",
    "compression": "Compression & Cache",
    "local_gpu": "Local GPU Inference",
    "toolcalls": "Tool Calls",
    "auth": "Authentication & API Keys",
    "logging": "Logging",
    "watchdog": "Watchdog",
    "usage_tracking": "Usage Tracking",
}

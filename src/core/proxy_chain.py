"""
Proxy Chain Configuration

Manages the ordered list of upstream proxies that Claude Code Proxy routes through.
Each entry in the chain is an HTTP service or CLI wrapper. The chain defines topology:

  Client → :8082 (this proxy) → chain[0] → chain[1] → ... → AI provider

Chain is stored in config/proxy_chain.json (path overridable via PROXY_CHAIN_FILE env).
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Default location — override with PROXY_CHAIN_FILE env var
DEFAULT_CHAIN_FILE = Path(__file__).parent.parent.parent / "config" / "proxy_chain.json"

# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProxyEntry:
    """A single entry in the proxy chain."""

    id: str                        # Unique slug, e.g. "headroom"
    name: str                      # Display name, e.g. "Headroom Compression"
    url: str                       # Base URL, e.g. "http://127.0.0.1:8787/v1"
    auth_key: str = ""             # API key (leave blank to inherit from env)
    enabled: bool = True           # Whether this entry is active
    order: int = 0                 # Sort index (auto-maintained by ProxyChain)

    # Service lifecycle (optional — only for services managed by this proxy)
    service_cmd: str = ""          # Shell command to start this service
    service_stop_cmd: str = ""     # Shell command to stop (if different from pkill)
    health_path: str = "/health"   # HTTP path for health check
    port: int = 0                  # Port number (for health checks / status display)

    # HTTP settings
    timeout: int = 90              # Request timeout in seconds
    extra_headers: dict = field(default_factory=dict)  # Additional headers to inject

    # Type hint for non-HTTP entries (e.g. CLI wrappers that don't have a URL)
    type: str = "http"             # "http" | "cli_wrapper"

    # Downstream routing: which AI providers this entry supports
    # Empty = forward all requests; populated = only models matching these prefixes
    model_prefixes: list = field(default_factory=list)

    def effective_auth_key(self) -> str:
        """Resolve auth key — expand ${ENV_VAR} references."""
        if not self.auth_key:
            return ""
        if self.auth_key.startswith("${") and self.auth_key.endswith("}"):
            env_name = self.auth_key[2:-1]
            return os.environ.get(env_name, "")
        return self.auth_key

    @property
    def is_http(self) -> bool:
        return self.type == "http" and bool(self.url)

    @property
    def display_url(self) -> str:
        if self.type == "cli_wrapper":
            return "(CLI wrapper)"
        return self.url or "(not configured)"


@dataclass
class RouteTarget:
    model: str
    base_url: str = ""
    api_key: str = ""

    def to_dict(self):
        return {"model": self.model, "base_url": self.base_url, "api_key": self.api_key}

    @classmethod
    def from_any(cls, val) -> "RouteTarget":
        if isinstance(val, str):
            return cls(model=val)
        if isinstance(val, dict):
            return cls(
                model=val.get("model", ""),
                base_url=val.get("base_url", ""),
                api_key=val.get("api_key", ""),
            )
        return cls(model="")


@dataclass
class RouterConfig:
    """Per-use-case model routing (mirrors Claude Code Router semantics)."""

    default: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    background: RouteTarget = field(default_factory=lambda: RouteTarget("nvidia/nemotron-nano-9b-v2:free"))
    think: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    long_context: RouteTarget = field(default_factory=lambda: RouteTarget("minimax/minimax-m2.5:free"))
    long_context_threshold: int = 60000
    web_search: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    image: RouteTarget = field(default_factory=lambda: RouteTarget("qwen/qwen2.5-vl-72b-instruct"))
    custom_router_path: str = ""
    disabled: bool = False        # When True, all slots return None (tier fallback only)
    passthrough: bool = False     # When True, no routing/cascade at all (Anthropic Pro mode)


@dataclass
class ProxyChain:
    """
    The full proxy chain configuration, including ordered chain entries
    and per-use-case model routing.
    """

    entries: list[ProxyEntry] = field(default_factory=list)
    router: RouterConfig = field(default_factory=RouterConfig)

    # ── Serialization ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "entries": [asdict(e) for e in self.entries],
            "router": asdict(self.router),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyChain":
        entries = [ProxyEntry(**e) for e in data.get("entries", [])]
        router_data = data.get("router", {})
        
        parsed_router_data = {}
        # Map JSON underscore-prefixed flags to dataclass fields
        if router_data.get("_disabled"):
            parsed_router_data["disabled"] = True
        if router_data.get("_passthrough"):
            parsed_router_data["passthrough"] = True
        for k, v in router_data.items():
            if k.startswith("_"):
                continue  # Already handled above
            if not hasattr(RouterConfig, k):
                continue
            if k in ["default", "background", "think", "long_context", "web_search", "image"]:
                parsed_router_data[k] = RouteTarget.from_any(v)
            else:
                parsed_router_data[k] = v
                
        router = RouterConfig(**parsed_router_data)
        # Re-sort by order field
        entries.sort(key=lambda e: e.order)
        return cls(entries=entries, router=router)

    # ── Persistence ──────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ProxyChain":
        p = Path(os.environ.get("PROXY_CHAIN_FILE", path or DEFAULT_CHAIN_FILE))
        if not p.exists():
            return cls._default_chain()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except Exception:
            return cls._default_chain()

    def save(self, path: Optional[Path] = None) -> None:
        p = Path(os.environ.get("PROXY_CHAIN_FILE", path or DEFAULT_CHAIN_FILE))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    # ── Chain manipulation ────────────────────────────────────────────────────

    def move_up(self, idx: int) -> None:
        if idx > 0:
            self.entries[idx - 1], self.entries[idx] = self.entries[idx], self.entries[idx - 1]
            self._renumber()

    def move_down(self, idx: int) -> None:
        if idx < len(self.entries) - 1:
            self.entries[idx], self.entries[idx + 1] = self.entries[idx + 1], self.entries[idx]
            self._renumber()

    def add(self, entry: ProxyEntry) -> None:
        entry.order = len(self.entries)
        self.entries.append(entry)
        self._renumber()

    def remove(self, idx: int) -> None:
        if 0 <= idx < len(self.entries):
            self.entries.pop(idx)
            self._renumber()

    def _renumber(self) -> None:
        for i, e in enumerate(self.entries):
            e.order = i

    # ── Runtime helpers ───────────────────────────────────────────────────────

    def upstream_url(self) -> str:
        """
        The URL this proxy should use as PROVIDER_BASE_URL.
        Returns the URL of the first enabled upstream HTTP entry in the chain.
        Falls back to empty string (direct OpenRouter via env) if no HTTP entries.
        """
        for e in self.entries:
            if e.enabled and e.is_http and not _is_local_proxy_entry(e):
                return e.url
        return ""

    def enabled_http_entries(self) -> list[ProxyEntry]:
        return [e for e in self.entries if e.enabled and e.is_http]

    def service_entries(self) -> list[ProxyEntry]:
        """Entries that have a service_cmd (can be started/stopped)."""
        return [e for e in self.entries if e.service_cmd]

    def start_services(self, dry_run: bool = False) -> list[tuple[str, bool, str]]:
        """
        Start all enabled services in REVERSE order (last service first,
        so each service's upstream is ready before the next starts).
        Returns list of (service_name, success, message).
        """
        results = []
        for entry in reversed(self.entries):
            if not entry.enabled or not entry.service_cmd:
                continue
            if dry_run:
                results.append((entry.name, True, f"would run: {entry.service_cmd}"))
                continue
            try:
                subprocess.Popen(
                    entry.service_cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                results.append((entry.name, True, f"started: {entry.service_cmd}"))
            except Exception as ex:
                results.append((entry.name, False, str(ex)))
        return results

    # ── Default chain ─────────────────────────────────────────────────────────

    @classmethod
    def _default_chain(cls) -> "ProxyChain":
        """
        Default topology:
          Claude Proxy → Headroom (:8787) → RTK (CLI wrapper) → [AI provider via env]
        CLIProxyAPI is included but DISABLED by default (Google banning TOS violations).
        """
        entries = [
            ProxyEntry(
                id="headroom",
                name="Headroom Compression",
                url="http://127.0.0.1:8787/v1",
                auth_key="${OPENROUTER_API_KEY}",
                enabled=True,
                order=0,
                port=8787,
                health_path="/health",
                service_cmd=(
                    "headroom proxy"
                    " --port 8787"
                    " --mode token_headroom"
                    " --openai-api-url https://openrouter.ai/api/v1"
                    " --backend openrouter"
                    " --no-telemetry"
                ),
                type="http",
            ),
            ProxyEntry(
                id="rtk",
                name="RTK Terminal Compression",
                url="",
                auth_key="",
                enabled=True,
                order=1,
                type="cli_wrapper",
                service_cmd="",  # RTK wraps CLI commands; no daemon to start
            ),
            ProxyEntry(
                id="cliproxyapi",
                name="CLIProxyAPI (Antigravity)",
                url="http://127.0.0.1:8317/v1",
                auth_key="",
                enabled=False,   # DISABLED — Google banning TOS violations
                order=2,
                port=8317,
                health_path="/v1/models",
                service_cmd=(
                    "/home/cheta/code/cliproxyapi/cli-proxy-api-plus"
                    " --config /home/cheta/code/cliproxyapi/config.yaml"
                ),
                type="http",
            ),
        ]
        router = RouterConfig(
            default=RouteTarget(""),
            background=RouteTarget("nvidia/nemotron-nano-9b-v2:free"),
            think=RouteTarget(""),
            long_context=RouteTarget("minimax/minimax-m2.5:free"),
            long_context_threshold=60000,
            web_search=RouteTarget(""),
            image=RouteTarget("qwen/qwen2.5-vl-72b-instruct"),
            custom_router_path="",
        )
        return cls(entries=entries, router=router)


# ── Module-level singleton ────────────────────────────────────────────────────

_chain: Optional[ProxyChain] = None


def get_chain() -> ProxyChain:
    """Return the loaded chain, loading from disk if needed."""
    global _chain
    if _chain is None:
        _chain = ProxyChain.load()
    return _chain


def reload_chain() -> ProxyChain:
    """Force reload from disk."""
    global _chain
    _chain = ProxyChain.load()
    return _chain


def _is_local_proxy_entry(entry: ProxyEntry) -> bool:
    """Skip self-referential chain entries when deriving the proxy upstream URL."""
    if entry.id == "claude_code_proxy":
        return True

    try:
        parsed = urlparse(entry.url)
    except Exception:
        return False

    hostname = (parsed.hostname or "").lower()
    return hostname in {"127.0.0.1", "localhost", "0.0.0.0"} and parsed.port == 8082

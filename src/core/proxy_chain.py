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
from typing import Optional, Dict, Any
from urllib.parse import urlparse

# Default location — override with PROXY_CHAIN_FILE env var
DEFAULT_CHAIN_FILE = Path(__file__).parent.parent.parent / "config" / "proxy_chain.json"

# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

# Import unified models (circular-safe as they don't import ProxyChain)
try:
    from src.core.assignments import Assignment  # type: ignore
    from src.core.identifier_mapping import IdentifierMapping  # type: ignore
except ImportError:
    # Fallback stubs for early import safety (before those modules exist)
    Assignment = None  # type: ignore
    IdentifierMapping = None  # type: ignore


@dataclass
class ProxyEntry:
    """A single entry in the proxy chain."""

    id: str  # Unique slug, e.g. "headroom"
    name: str  # Display name, e.g. "Headroom Compression"
    # Base URL is optional: service entries (claude_code_proxy, headroom) may only
    # declare a port for the health-check / startup script and rely on the runtime
    # to build the URL from host/port. Required positional `url` blew up every
    # request when entries from disk omitted it.
    url: str = ""  # Base URL, e.g. "http://127.0.0.1:8787/v1"
    auth_key: str = ""  # API key (leave blank to inherit from env)
    enabled: bool = True  # Whether this entry is active
    order: int = 0  # Sort index (auto-maintained by ProxyChain)

    # Service lifecycle (optional — only for services managed by this proxy)
    service_cmd: str = ""  # Shell command to start this service
    service_stop_cmd: str = ""  # Shell command to stop (if different from pkill)
    health_path: str = "/health"  # HTTP path for health check
    port: int = 0  # Port number (for health checks / status display)

    # HTTP settings
    timeout: int = 90  # Request timeout in seconds
    extra_headers: dict = field(default_factory=dict)  # Additional headers to inject

    # Type hint for non-HTTP entries (e.g. CLI wrappers that don't have a URL)
    type: str = "http"  # "http" | "cli_wrapper"

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

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RouteTarget:
    model: str
    base_url: str = ""
    api_key: str = ""
    assignment_id: str = ""

    def to_dict(self):
        return {
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "assignment_id": self.assignment_id,
        }

    @classmethod
    def from_any(cls, val) -> "RouteTarget":
        if isinstance(val, str):
            return cls(model=val)
        if isinstance(val, dict):
            return cls(
                model=val.get("model", ""),
                base_url=val.get("base_url", ""),
                api_key=val.get("api_key", ""),
                assignment_id=val.get("assignment_id", ""),
            )
        return cls(model="")


@dataclass
class RouterConfig:
    """Per-use-case model routing (mirrors Claude Code Router semantics)."""

    default: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    background: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    think: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    long_context: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    long_context_threshold: int = 0
    web_search: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    image: RouteTarget = field(default_factory=lambda: RouteTarget(""))
    custom_router_path: str = ""
    disabled: bool = False  # When True, all slots return None (tier fallback only)
    passthrough: bool = (
        False  # When True, no routing/cascade at all (Anthropic Pro mode)
    )


@dataclass
class ModelScanConfig:
    """Optional model-scan binding configuration, preserved across registry saves."""

    enabled: bool = False
    policy: str = "static"
    snapshot_path: str = "~/.config/model-scan/routing_snapshot.json"
    gateway_url: str = "http://127.0.0.1:7099/routing-snapshot"
    cache_ttl_s: int = 300
    staleness_limit_s: int = 86400
    lanes: dict = field(default_factory=lambda: {"interactive": {"allow_paid": True}, "standby": {"allow_paid": False}})

    # ── F18 global quota-aware allocator (OFF by default) ──────────────────────
    # When allocator_enabled and session_profiles are set, reload runs the allocator
    # over the routing snapshot and writes per-profile overlays the request path
    # already consumes via resolve_profile_binding(). Disabled or empty => no-op.
    allocator_enabled: bool = False
    # {profile_name: {"roles": {assignment_id: {floor:{...}, value_sensitivity, ...}}}}
    session_profiles: dict = field(default_factory=dict)
    # optional role_id -> snapshot slot id (defaults to the role/base-role name)
    allocator_slot_map: dict = field(default_factory=dict)
    # provider -> remaining_fraction (0..1) operator override for quota meters
    static_quota: dict = field(default_factory=dict)
    # nominal per-window call budget used to turn a remaining_fraction into a meter
    quota_nominal_calls: float = 1000.0

    @classmethod
    def from_any(cls, val: Any) -> "ModelScanConfig":
        if isinstance(val, cls):
            return val
        if not isinstance(val, dict):
            return cls()
        fields = cls.__dataclass_fields__
        return cls(**{k: v for k, v in val.items() if k in fields})


@dataclass
class ProxyChain:
    """
    The full proxy chain configuration, including ordered chain entries,
    per-use-case model routing (legacy RouterConfig), unified assignment model,
    and incoming-identifier mappings.
    """

    entries: list[ProxyEntry] = field(default_factory=list)
    router: RouterConfig = field(default_factory=RouterConfig)

    # v2 fields — unified assignment model
    schema_version: str = "2.0.0"
    assignments: list[Any] = field(
        default_factory=list
    )  # list[Assignment] but avoid circular import
    identifier_mappings: list[Any] = field(
        default_factory=list
    )  # list[IdentifierMapping]
    model_scan: ModelScanConfig = field(default_factory=ModelScanConfig)

    # ── Serialization ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        result = {
            "schema_version": self.schema_version,
            "entries": [asdict(e) for e in self.entries],
            "router": asdict(self.router),
            "assignments": [asdict(a) for a in self.assignments],
            "identifier_mappings": [asdict(m) for m in self.identifier_mappings],
            "model_scan": asdict(self.model_scan),
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyChain":
        # Parse entries
        entries = [ProxyEntry(**e) for e in data.get("entries", [])]

        # Parse router (unchanged from v1)
        router_data = data.get("router", {})
        parsed_router_data = {}
        if router_data.get("_disabled"):
            parsed_router_data["disabled"] = True
        if router_data.get("_passthrough"):
            parsed_router_data["passthrough"] = True
        for k, v in router_data.items():
            if k.startswith("_"):
                continue
            if k not in RouterConfig.__dataclass_fields__:
                continue
            if k in [
                "default",
                "background",
                "think",
                "long_context",
                "web_search",
                "image",
            ]:
                parsed_router_data[k] = RouteTarget.from_any(v)
            else:
                parsed_router_data[k] = v
        router = RouterConfig(**parsed_router_data)

        # Parse v2 additions (with safe fallback for v1 data)
        assignments_raw = data.get("assignments", [])
        assignments = []
        for a in assignments_raw:
            # Assignment class may not be available during early import; use dict if so
            if Assignment is not None:
                assignments.append(Assignment(**a))
            else:
                assignments.append(a)  # fallback: keep as dict

        mappings_raw = data.get("identifier_mappings", [])
        identifier_mappings = []
        for m in mappings_raw:
            if IdentifierMapping is not None:
                identifier_mappings.append(IdentifierMapping(**m))
            else:
                identifier_mappings.append(m)

        chain = cls(
            entries=entries,
            router=router,
            schema_version=data.get("schema_version", "1.0.0"),
            assignments=assignments,
            identifier_mappings=identifier_mappings,
            model_scan=ModelScanConfig.from_any(data.get("model_scan", {})),
        )
        # Re-sort by order field
        chain.entries.sort(key=lambda e: e.order)
        return chain

    # ── Persistence ──────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ProxyChain":
        """Load from disk, optionally migrating if schema_version < current."""
        p = Path(os.environ.get("PROXY_CHAIN_FILE", path or DEFAULT_CHAIN_FILE))
        if not p.exists():
            return cls._default_chain()

        try:
            raw = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: failed to read proxy_chain.json ({e}); using defaults")
            return cls._default_chain()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Warning: failed to parse proxy_chain.json ({e}); using defaults")
            return cls._default_chain()

        # Schema migration (T019–T021) — handled in separate module
        from src.core.schema_migrations import migrate_if_needed

        migrated_data = migrate_if_needed(
            data, p
        )  # may raise RuntimeError on unsafe migration
        return cls.from_dict(migrated_data)

    def save(self, path: Optional[Path] = None) -> None:
        """Persist to disk atomically (write-to-temp + fsync + rename).

        Safety: if this chain object has no entries but the on-disk file has
        entries, preserve the on-disk entries. This prevents API calls that
        update only assignments/router from accidentally wiping the service
        startup entries that `proxies up` depends on.
        """
        p = Path(os.environ.get("PROXY_CHAIN_FILE", path or DEFAULT_CHAIN_FILE))
        p.parent.mkdir(parents=True, exist_ok=True)

        payload = self.to_dict()

        # Guard: preserve on-disk entries if we're about to write an empty list.
        if not payload.get("entries") and p.exists():
            try:
                import json as _json
                on_disk = _json.loads(p.read_text(encoding="utf-8"))
                existing_entries = on_disk.get("entries", [])
                if existing_entries:
                    payload["entries"] = existing_entries
            except Exception:
                pass  # if we can't read on-disk, proceed with what we have

        tmp_path = p.with_suffix(".tmp")
        tmp_path.write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(p)  # atomic on POSIX

    # ── Chain manipulation ────────────────────────────────────────────────────

    def move_up(self, idx: int) -> None:
        if idx > 0:
            self.entries[idx - 1], self.entries[idx] = (
                self.entries[idx],
                self.entries[idx - 1],
            )
            self._renumber()

    def move_down(self, idx: int) -> None:
        if idx < len(self.entries) - 1:
            self.entries[idx], self.entries[idx + 1] = (
                self.entries[idx + 1],
                self.entries[idx],
            )
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

    # ── Validation ───────────────────────────────────────────────────────────

    def validate_edit(self) -> list[str]:
        """Run consistency checks on the chain.

        Returns a list of error messages. Empty list means validation passed.
        Checks:
        - Port conflicts between enabled HTTP entries (FR-013)
        - Malformed URLs (basic scheme + netloc check)
        - Unreachable service_cmd heuristic (file exists or command name recognized)
        """
        errors: list[str] = []
        used_ports: set[int] = set()

        for e in self.entries:
            if not e.enabled:
                continue

            # URL validation (if HTTP)
            if e.type == "http":
                if not e.url:
                    errors.append(f"Entry '{e.id}' is HTTP but url is blank")
                else:
                    try:
                        parsed = urlparse(e.url)
                        if not parsed.scheme or not parsed.netloc:
                            errors.append(f"Entry '{e.id}' has malformed URL: {e.url}")
                        if parsed.port:
                            if parsed.port in used_ports:
                                errors.append(
                                    f"Port conflict: {parsed.port} already used by another entry"
                                )
                            used_ports.add(parsed.port)
                    except Exception:
                        errors.append(f"Entry '{e.id}' has invalid URL: {e.url}")

            # service_cmd heuristic — only flag when the first token is itself
            # a path (contains "/"). Shell wrappers like ``cd /foo && python``
            # have ``cd`` as the first token, which is a builtin, not a path.
            if e.service_cmd:
                first_token = e.service_cmd.split()[0]
                if "/" in first_token:
                    import os as _os

                    expanded = _os.path.expanduser(first_token)
                    if not _os.path.exists(expanded):
                        errors.append(
                            f"Entry '{e.id}' service_cmd points to non-existent file: {first_token}"
                        )

        return errors

    # ── Runtime helpers ───────────────────────────────────────────────────────

    def upstream_url(self) -> str:
        """
        The URL this proxy should use as BIG_ENDPOINT.
        Returns the URL of the first enabled upstream HTTP entry in the chain.
        Falls back to empty string (direct OpenRouter via env) if no HTTP entries.
        """
        for e in self.entries:
            if e.enabled and e.is_http and not _is_local_proxy_entry(e):
                return e.url
        return ""

    def direct_provider_url(self) -> str:
        """
        The direct provider URL (bypassing local compression layers like headroom).
        Looks for a non-local entry in the chain, then falls back to env vars,
        then falls back to the OpenRouter default.
        """
        import os
        _local_ports = {"8787", "8082", "8788", "8317"}
        for e in self.entries:
            if e.enabled and e.is_http and not _is_local_proxy_entry(e):
                url = e.url or ""
                # Skip any 127.0.0.1 / localhost proxy ports
                skip = any(f":{p}" in url for p in _local_ports)
                if not skip and url:
                    return url
        # Fall back to env-configured provider URL
        return (
            os.environ.get("OPENAI_BASE_URL", "")
            or os.environ.get("OPENROUTER_API_URL", "")
            or "https://openrouter.ai/api/v1"
        )

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
                enabled=False,  # DISABLED — Google banning TOS violations
                order=2,
                port=8317,
                health_path="/v1/models",
                service_cmd=(
                    f"{Path.home()}/code/cliproxyapi/cli-proxy-api-plus"
                    f" --config {Path.home()}/code/cliproxyapi/config.yaml"
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
    """Skip local chain proxies when deriving the proxy upstream URL.

    The router (8082) sits downstream of local front-door/compression proxies — headroom
    (8787/8788) and the OAuth upstream proxy on its loopback port — in the chain topology
    ``Claude → headroom(:8787) → router(:8082) → provider``. None of these loopback proxies is a
    real upstream *provider* for the router; treating them as the router's upstream makes the
    router route back into the chain (the headroom→router→headroom loop that surfaced as the
    401 cascade). So the router's upstream must resolve to the actual provider, never a local
    compression/front-door proxy.
    """
    if entry.id == "claude_code_proxy":
        return True

    try:
        parsed = urlparse(entry.url)
    except Exception:
        return False

    hostname = (parsed.hostname or "").lower()
    # Local loopback proxy ports that are chain stages, not upstream providers.
    _LOCAL_PROXY_PORTS = {8082, 8787, 8788}
    return hostname in {"127.0.0.1", "localhost", "0.0.0.0"} and parsed.port in _LOCAL_PROXY_PORTS

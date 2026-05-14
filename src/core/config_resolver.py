"""Layered configuration resolver with provenance.

Owns the single read path for all configuration values in the proxy.
Precedence: CLI > shell env > .env > stored config > defaults.

See specs/001-unified-config-system/contracts/resolver.md for the full contract.
Implementation lands in Phase 2 (tasks T006-T014 in specs/001-unified-config-system/tasks.md).
"""

from __future__ import annotations

import contextvars
import os
import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

# ── Layer enum + precedence ────────────────────────────────────────────────────


class ConfigLayer(StrEnum):
    CLI = "cli"
    SHELL_ENV = "shell_env"
    DOTENV = "dotenv"
    STORED = "stored"
    DEFAULT = "default"


LAYERS_BY_PRECEDENCE: tuple[ConfigLayer, ...] = (
    ConfigLayer.CLI,
    ConfigLayer.SHELL_ENV,
    ConfigLayer.DOTENV,
    ConfigLayer.STORED,
    ConfigLayer.DEFAULT,
)

# ── Dataclasses ────────────────────────────────────────────────────────────────


@dataclass
class ResolvedValue:
    field_path: str
    value: Any
    source_layer: ConfigLayer
    raw_value: Any = None


@dataclass
class FieldSchema:
    type: Any = None
    default: Any = None
    validators: list[Callable[[Any], None]] = None
    is_secret: bool = False
    env_alias: str | None = None
    description: str = ""


class ConfigValidationError(ValueError):
    pass


# ── Snapshot context ───────────────────────────────────────────────────────────

_snapshot_ctx: contextvars.ContextVar[Optional[dict[str, ResolvedValue]]] = (
    contextvars.ContextVar("config_snapshot", default=None)
)


def set_snapshot(snap: dict) -> contextvars.Token:
    return _snapshot_ctx.set(snap)


def reset_snapshot(token: contextvars.Token) -> None:
    _snapshot_ctx.reset(token)


def get_snapshot() -> Optional[dict]:
    return _snapshot_ctx.get()


# ── ConfigResolver ─────────────────────────────────────────────────────────────


class ConfigResolver:
    def __init__(self) -> None:
        self._layers = {
            ConfigLayer.CLI: {},
            ConfigLayer.SHELL_ENV: {},
            ConfigLayer.DOTENV: {},
            ConfigLayer.STORED: {},
            ConfigLayer.DEFAULT: {},
        }
        self._schemas: dict[str, FieldSchema] = {}
        # Legacy env-var names actually present in the environment (not just registered).
        self._deprecated_aliases: set[str] = set()
        self._subscribers: list[Callable[[dict], None]] = []
        self._lock = threading.RLock()
        self._seq = 0
        self._initialized = False

        self._populate_shell_env()
        self._load_dotenv()

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._register_static_schemas()
        self._populate_stored_from_chain()
        self._register_legacy_aliases()
        self.emit_deprecation_summary()
        self._initialized = True

    def _register_static_schemas(self) -> None:
        # Sensible defaults for fields the proxy needs at startup; matches
        # legacy os.environ.get() defaults that existed before the resolver.
        FIELD_DEFAULTS: dict[str, Any] = {
            "host": "0.0.0.0",
            "port": 8082,
            "log_level": "WARNING",
            "request_timeout": 90,
            "max_retries": 2,
            "logs_dir": "logs",
            "log_tier": "summary",
            "log_max_size_mb": 50,
            "log_retention_days": 7,
            "usage_tracking_db_path": "usage_tracking.db",
            "tool_output_max_chars": 25000,
            "proxy_auth_key": "",
            "anthropic_api_key_legacy": "",
            "toolcall_models": "",
            "toolcall_auto_route": "true",
            "toolcall_max_retries": 2,
        }
        # Map ConfigField attr -> uppercase env var alias (case-fold to upper).
        try:
            from src.core.config import ConfigField as _CF
            from src.core.config import Config

            for attr_name, attr in Config.__dict__.items():
                if not isinstance(attr, _CF):
                    continue
                fp = attr.field_path
                typ = str
                if attr.cast is int:
                    typ = int
                elif attr.cast is bool:
                    typ = bool
                elif attr.cast is float:
                    typ = float
                is_secret = ("api_key" in fp) or (
                    fp in ("proxy_auth_key", "anthropic_api_key_legacy")
                )
                default = FIELD_DEFAULTS.get(fp)
                self.register_schema(
                    fp,
                    FieldSchema(
                        type=typ,
                        default=default,
                        is_secret=is_secret,
                    ),
                )
                # Bridge uppercase env value into the lowercase field path
                upper = fp.upper()
                for layer in (ConfigLayer.SHELL_ENV, ConfigLayer.DOTENV):
                    if upper in self._layers[layer] and fp not in self._layers[layer]:
                        self._layers[layer][fp] = self._layers[layer][upper]
        except Exception:
            pass

    def _populate_stored_from_chain(self) -> None:
        try:
            from src.core.proxy_chain import get_chain

            chain = get_chain()
            for a in chain.assignments:
                self._ensure_assignment_schemas(a)
                prefix = f"assignments.{a.id}"
                self._layers[ConfigLayer.STORED][f"{prefix}.model"] = a.model
                self._layers[ConfigLayer.STORED][f"{prefix}.provider"] = a.provider
                self._layers[ConfigLayer.STORED][f"{prefix}.base_url"] = a.base_url
                self._layers[ConfigLayer.STORED][f"{prefix}.api_key"] = a.api_key
                self._layers[ConfigLayer.STORED][f"{prefix}.enabled"] = a.enabled
                self._layers[ConfigLayer.STORED][f"{prefix}.cascade"] = a.cascade
            for m in chain.identifier_mappings:
                self._ensure_identifier_mapping_schemas(m)
                prefix = f"identifier_mappings.{m.incoming_identifier}"
                self._layers[ConfigLayer.STORED][f"{prefix}.assignment_id"] = (
                    m.assignment_id
                )
                self._layers[ConfigLayer.STORED][f"{prefix}.enabled"] = m.enabled
                self._layers[ConfigLayer.STORED][f"{prefix}.priority"] = m.priority
                self._layers[ConfigLayer.STORED][f"{prefix}.notes"] = m.notes
        except Exception:
            pass

    def _ensure_assignment_schemas(self, a: Assignment) -> None:
        prefix = f"assignments.{a.id}"
        fields = [
            ("model", str, "", False),
            ("provider", str, "", False),
            ("base_url", str, "", False),
            ("api_key", str, "", True),
            ("enabled", bool, True, False),
            ("cascade", list, [], False),
        ]
        for name, typ, default, secret in fields:
            fp = f"{prefix}.{name}"
            if fp not in self._schemas:
                self.register_schema(
                    fp, FieldSchema(type=typ, default=default, is_secret=secret)
                )

    def _ensure_identifier_mapping_schemas(self, m: IdentifierMapping) -> None:
        prefix = f"identifier_mappings.{m.incoming_identifier}"
        fields = [
            ("assignment_id", str, "", False),
            ("enabled", bool, True, False),
            ("priority", int, 0, False),
            ("notes", str, "", False),
        ]
        for name, typ, default, secret in fields:
            fp = f"{prefix}.{name}"
            if fp not in self._schemas:
                self.register_schema(
                    fp, FieldSchema(type=typ, default=default, is_secret=secret)
                )

    def _populate_shell_env(self) -> None:
        exclude = {"PATH", "PWD", "HOME", "USER", "SHELL", "LOGNAME", "LANG", "LC_*"}
        for k, v in os.environ.items():
            if k in exclude or k.startswith("_"):
                continue
            self._layers[ConfigLayer.SHELL_ENV][k] = v

    def _load_dotenv(self) -> None:
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(str(env_path), override=False)
            for k, v in os.environ.items():
                if k in self._layers[ConfigLayer.DOTENV]:
                    continue
                self._layers[ConfigLayer.DOTENV][k] = v

    LEGACY_ALIAS_MAP: dict[str, str] = {
        "BIG_MODEL": "assignments.big.model",
        "MIDDLE_MODEL": "assignments.middle.model",
        "SMALL_MODEL": "assignments.small.model",
        "BIG_ENDPOINT": "assignments.big.base_url",
        "MIDDLE_ENDPOINT": "assignments.middle.base_url",
        "SMALL_ENDPOINT": "assignments.small.base_url",
        "BIG_API_KEY": "assignments.big.api_key",
        "MIDDLE_API_KEY": "assignments.middle.api_key",
        "SMALL_API_KEY": "assignments.small.api_key",
        "ENABLE_BIG_ENDPOINT": "assignments.big.enabled",
        "ENABLE_MIDDLE_ENDPOINT": "assignments.middle.enabled",
        "ENABLE_SMALL_ENDPOINT": "assignments.small.enabled",
        "PROXY_AUTH_KEY": "proxy_auth_key",
        "OPENROUTER_API_KEY": "openai_api_key",
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key_legacy",
        "OPENAI_BASE_URL": "openai_base_url",
    }

    def _register_legacy_aliases(self) -> None:
        # Register schemas for assignments.{tier}.* even if no chain exists yet,
        # so legacy BIG_MODEL etc. can route to a known field path during tests.
        for tier in ("big", "middle", "small"):
            for fname, ftype, fdefault, fsecret in (
                ("model", str, "", False),
                ("provider", str, "", False),
                ("base_url", str, "", False),
                ("api_key", str, "", True),
                ("enabled", bool, True, False),
                ("cascade", list, [], False),
            ):
                fp = f"assignments.{tier}.{fname}"
                if fp not in self._schemas:
                    self.register_schema(
                        fp, FieldSchema(type=ftype, default=fdefault, is_secret=fsecret)
                    )
        for env_name, field_path in self.LEGACY_ALIAS_MAP.items():
            if field_path in self._schemas:
                self._schemas[field_path].env_alias = env_name
            # Bridge present env value into modern field path, in the same layer.
            for layer in (ConfigLayer.SHELL_ENV, ConfigLayer.DOTENV):
                if env_name in self._layers[layer]:
                    self._deprecated_aliases.add(env_name)
                    if field_path not in self._layers[layer]:
                        self._layers[layer][field_path] = self._layers[layer][env_name]

    def register_schema(self, field_path: str, schema: FieldSchema) -> None:
        with self._lock:
            self._schemas[field_path] = schema

    def resolve(self, field_path: str) -> ResolvedValue:
        self._ensure_initialized()
        snap = get_snapshot()
        if snap is not None and field_path in snap:
            return snap[field_path]
        with self._lock:
            schema = self._schemas.get(field_path)
            if schema is None:
                raise KeyError(f"Unknown field: {field_path}")
            for layer in LAYERS_BY_PRECEDENCE:
                if field_path in self._layers[layer]:
                    raw = self._layers[layer][field_path]
                    val = self._expand_env_vars(raw)
                    try:
                        if schema.type and val is not None:
                            if schema.type is bool:
                                val = (
                                    val.lower() in ("true", "1", "yes")
                                    if isinstance(val, str)
                                    else bool(val)
                                )
                            elif schema.type is int:
                                val = int(val)
                            elif schema.type is float:
                                val = float(val)
                            else:
                                val = schema.type(val)
                    except Exception:
                        val = raw
                    return ResolvedValue(
                        field_path=field_path,
                        value=val,
                        source_layer=layer,
                        raw_value=raw,
                    )
            if schema.default is not None:
                return ResolvedValue(
                    field_path=field_path,
                    value=schema.default,
                    source_layer=ConfigLayer.DEFAULT,
                    raw_value=None,
                )
            raise KeyError(f"Field {field_path} has no value and no default")

    def _expand_env_vars(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return pattern.sub(replace, value)

    def set(
        self,
        field_path: str,
        value: Any,
        source_layer: ConfigLayer = ConfigLayer.STORED,
        principal: str | None = None,
    ) -> None:
        self._ensure_initialized()
        with self._lock:
            schema = self._schemas.get(field_path)
            if schema is None:
                raise KeyError(f"Unknown field: {field_path}")
            if schema.validators:
                for v in schema.validators:
                    v(value)
            # Capture before value
            before_val = None
            try:
                before_rv = self.resolve(field_path)
                before_val = before_rv.value
            except KeyError:
                before_val = None
            target_layer = source_layer
            if target_layer == ConfigLayer.STORED:
                self._persist_to_structured_config(field_path, value)
            self._layers[target_layer][field_path] = value
            self._increment_seq()
            after_rv = self.resolve(field_path)
            after_val = after_rv.value
            if schema.is_secret and isinstance(after_val, str):
                from src.services.observability.audit_log import mask_secret

                after_val = mask_secret(after_val) if len(after_val) >= 12 else "***"
            self._notify_subscribers(
                {
                    "field_path": field_path,
                    "after_value": after_val,
                    "source_layer": after_rv.source_layer,
                    "seq": self._seq,
                }
            )
            if target_layer == ConfigLayer.STORED:
                self._write_audit_log(
                    field_path, schema, after_rv, principal, before_val
                )

    def _persist_to_structured_config(self, field_path: str, value: Any) -> None:
        from src.core.proxy_chain import get_chain

        chain = get_chain()
        parts = field_path.split(".")
        if len(parts) >= 2 and parts[0] == "assignments":
            assign_id = parts[1]
            field = parts[2] if len(parts) > 2 else None
            for a in chain.assignments:
                if a.id == assign_id:
                    if field:
                        setattr(a, field, value)
                    break
            else:
                return
            chain.save()
        elif len(parts) >= 2 and parts[0] == "identifier_mappings":
            inc = parts[1]
            field = parts[2] if len(parts) > 2 else None
            for m in chain.identifier_mappings:
                if m.incoming_identifier == inc:
                    if field:
                        setattr(m, field, value)
                    break
            else:
                return
            chain.save()
        else:
            pass

    def _write_audit_log(
        self,
        field_path: str,
        schema: FieldSchema,
        rv: ResolvedValue,
        principal: str | None,
        before_value: Any,
    ) -> None:
        principal_str = principal or "unknown"
        surface = (
            rv.source_layer.value
            if isinstance(rv.source_layer, ConfigLayer)
            else str(rv.source_layer)
        )
        endpoint = "resolver.set"
        from src.services.observability.audit_log import append_audit

        append_audit(
            principal=principal_str,
            surface=surface,
            endpoint=endpoint,
            field_path=field_path,
            before_value=before_value,
            after_value=rv.value,
        )

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def _notify_subscribers(self, event: dict) -> None:
        for cb in self._subscribers:
            try:
                threading.Thread(target=cb, args=(event,), daemon=True).start()
            except Exception:
                pass

    def _increment_seq(self) -> None:
        self._seq += 1

    def snapshot(self) -> dict[str, ResolvedValue]:
        self._ensure_initialized()
        with self._lock:
            field_paths = list(self._schemas.keys())
        result: dict[str, ResolvedValue] = {}
        for fp in field_paths:
            try:
                rv = self.resolve(fp)
                result[fp] = rv
            except KeyError:
                pass
        return result

    @property
    def deprecated_aliases_in_use(self) -> set[str]:
        """Legacy env vars detected at startup. Triggers lazy init on first read."""
        self._ensure_initialized()
        return self._deprecated_aliases

    def emit_deprecation_summary(self) -> None:
        aliases = self._deprecated_aliases
        if not aliases:
            return
        # Allow silencing: set SILENCE_DEPRECATION_WARNINGS=true in .env
        # These vars still work — the resolver translates them. This is purely cosmetic.
        import os as _os
        if _os.environ.get("SILENCE_DEPRECATION_WARNINGS", "").lower() in ("true", "1", "yes"):
            return
        print("\n⚠  Deprecated env vars in use (set modern equivalents to silence):")
        for alias in sorted(aliases):
            target = self.LEGACY_ALIAS_MAP.get(alias, "")
            hint = f" → {target}" if target else ""
            print(f"  {alias}{hint}")
        print("")

    @property
    def layers(self) -> dict[ConfigLayer, dict[str, Any]]:
        return self._layers


# ── Singleton ───────────────────────────────────────────────────────────────────

resolver = ConfigResolver()


def get_resolver() -> ConfigResolver:
    resolver._ensure_initialized()
    return resolver

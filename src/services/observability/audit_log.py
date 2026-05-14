"""Append-only audit log for successful configuration writes.

One JSON line per write at logs/config-audit.log. Secret-shaped field values
are masked before the entry is appended.

See specs/001-unified-config-system/data-model.md#auditlogentry (FR-030, FR-035).
Implementation lands in Phase 2 (task T012 masking utility) and Phase 7 (task T070 writer).
"""

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Secret patterns per research.md R12
API_KEY_PATTERNS = [
    re.compile(r"^sk-[A-Za-z0-9]{48,}$"),  # OpenAI sk-*
    re.compile(r"^sk-or-[A-Za-z0-9]{32,}$"),  # OpenRouter
    re.compile(r"^sk-ant-[A-Za-z0-9_-]+$"),  # Anthropic (legacy)
    re.compile(r"^sk-ant-oat01-[A-Za-z0-9_-]+$"),  # Anthropic OAuth (R12)
    re.compile(r"^Bearer [A-Za-z0-9+/=._-]+$", re.IGNORECASE),  # OAuth tokens
    re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"),  # JWT
    re.compile(r"^[0-9a-f]{40,}$", re.IGNORECASE),  # long-hex (GitHub/40+ hex)
]


# Prefixes preserved verbatim during masking (longest first — order matters).
_PREFIX_RULES: list[tuple[str, int, int]] = [
    # (prefix, body_first_chars, body_last_chars)
    ("sk-ant-oat01-", 3, 3),
    ("sk-ant-", 3, 3),
    ("sk-or-", 3, 3),
    ("sk-", 3, 3),
    ("Bearer ", 4, 3),
]
_JWT_RE = re.compile(r"^eyJ[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
_LONG_HEX_RE = re.compile(r"^[0-9a-f]{40,}$", re.IGNORECASE)


def mask_secret(value: Any) -> str:
    """Mask a secret value for audit log display.

    Per-pattern masking:
      - Known token prefix (sk-*, Bearer *) → keep prefix, show first/last
        chars of the body. If body < 8 chars, fully mask as ``***``.
      - JWT → first 4 chars + "..." + last 2 chars.
      - Long hex (40+) → first 4 + "..." + last 4.
      - Non-secrets → returned unchanged.
    """
    if not isinstance(value, (str, bytes)):
        return str(value)
    s = value.decode() if isinstance(value, bytes) else value

    for prefix, head, tail in _PREFIX_RULES:
        if s.startswith(prefix):
            body = s[len(prefix):]
            if len(body) < 8:
                return "***"
            return f"{prefix}{body[:head]}...{body[-tail:]}"

    if _JWT_RE.match(s):
        return f"{s[:4]}...{s[-2:]}"

    if _LONG_HEX_RE.match(s):
        return f"{s[:4]}...{s[-4:]}"

    return s


def mask_dict_secrets(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask secret-shaped values in a dict."""
    masked = {}
    for k, v in data.items():
        if isinstance(v, dict):
            masked[k] = mask_dict_secrets(v)
        elif isinstance(v, list):
            masked[k] = [
                mask_dict_secrets(i)
                if isinstance(i, dict)
                else (mask_secret(i) if isinstance(i, str) else i)
                for i in v
            ]
        elif isinstance(v, str):
            masked[k] = mask_secret(v)
        else:
            masked[k] = v
    return masked


# ── Audit log writer ────────────────────────────────────────────────────────────
# Monotonic sequence counter (process-local)
_seq_lock = threading.Lock()
_last_seq = 0


def _next_seq() -> int:
    global _last_seq
    with _seq_lock:
        _last_seq += 1
        return _last_seq


def _resolve_log_file() -> Path:
    """Return the audit log path. Honors AUDIT_LOG_PATH env var; defaults to
    ``logs/config-audit.log``. A module-level ``log_file`` attribute, if set,
    takes priority — tests use this to redirect writes to a temp directory.
    """
    override = globals().get("log_file")
    if override:
        return Path(override)
    env_override = os.environ.get("AUDIT_LOG_PATH")
    if env_override:
        return Path(env_override)
    return Path("logs/config-audit.log")


def append_audit(
    principal: str,
    surface: str,
    endpoint: str,
    field_path: str,
    before_value: Any,
    after_value: Any,
    client_ip: Optional[str] = None,
) -> None:
    """Append one audit entry to the active audit log."""
    log_file_path = _resolve_log_file()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    seq = _next_seq()
    timestamp = datetime.now(timezone.utc).isoformat()
    # Mask values
    masked_before = mask_secret(before_value) if before_value is not None else None
    masked_after = mask_secret(after_value) if after_value is not None else None

    entry = {
        "seq": seq,
        "timestamp": timestamp,
        "principal": principal,
        "surface": surface,
        "endpoint": endpoint,
        "field_path": field_path,
        "before_value": masked_before,
        "after_value": masked_after,
    }
    if client_ip:
        entry["client_ip"] = client_ip

    try:
        with open(str(log_file_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # Best-effort: never raise from audit path
        pass


# Minimal AuditLogEntry builder for T012 contract
def format_audit_entry(
    seq: int,
    timestamp: str,
    principal: str,
    surface: str,
    endpoint: str,
    field_path: str,
    before_value: Any,
    after_value: Any,
    client_ip: str | None = None,
) -> dict:
    """Build a structured audit log entry with secret masking."""
    entry = {
        "seq": seq,
        "timestamp": timestamp,
        "principal": principal,
        "surface": surface,
        "endpoint": endpoint,
        "field_path": field_path,
        "before_value": mask_secret(before_value)
        if isinstance(before_value, str)
        else before_value,
        "after_value": mask_secret(after_value)
        if isinstance(after_value, str)
        else after_value,
    }
    if client_ip:
        entry["client_ip"] = client_ip
    return entry

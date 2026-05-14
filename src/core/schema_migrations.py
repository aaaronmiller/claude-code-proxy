"""Versioned auto-migration for stored config files.

On proxy startup, if the stored config's schema_version is older than the
running proxy's expected version, this module chains migration functions to
bring it forward, writes a migration log, and refuses to mutate the file when
the transformation would be unsafe (FR-023c).

See specs/001-unified-config-system/data-model.md#proxychain and research.md R13.
Implementation lands in Phase 2 (tasks T019-T022).
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Dict, Any

CURRENT_VERSION = "2.0.0"

MIGRATIONS: Dict[str, Callable[[dict], dict]] = {}


def register(version: str):
    """Decorator: register a migration function for a specific target version."""

    def decorator(fn: Callable[[dict], dict]) -> Callable[[dict], dict]:
        MIGRATIONS[version] = fn
        return fn

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Migration functions (each upgrades _from_ a specific predecessor version)
# ─────────────────────────────────────────────────────────────────────────────


@register("2.0.0")
def migrate_v1_to_v2(data: dict) -> dict:
    """Upgrade from v1.0.0 to v2.0.0.

    Transforms:
      - Legacy tier env-var fields (BIG_MODEL, MIDDLE_MODEL, SMALL_MODEL) → assignments[kind=tier]
      - Legacy router section (router.default, router.background, …) → assignments[kind=slot]
      - Preserve chain.entries
      - Add schema_version = "2.0.0"
    """
    errors: list[str] = []
    assignments: list[dict] = []

    # 0. Check for unknown top-level keys (FR-023c / R13)
    allowed_keys = {
        "entries",
        "router",
        "schema_version",
        "big_model",
        "middle_model",
        "small_model",
        "big_endpoint",
        "middle_endpoint",
        "small_endpoint",
        "big_api_key",
        "middle_api_key",
        "small_api_key",
    }
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        errors.append(
            f"Unknown configuration fields: {', '.join(sorted(unknown_keys))}"
        )

    # 1. Tier assignments from legacy tier fields
    legacy_tier_fields = {
        "big": ("big_model", "big_endpoint", "big_api_key"),
        "middle": ("middle_model", "middle_endpoint", "middle_api_key"),
        "small": ("small_model", "small_endpoint", "small_api_key"),
    }
    for tier, (model_key, url_key, key_key) in legacy_tier_fields.items():
        if model_key in data:
            assignments.append(
                {
                    "id": tier,
                    "kind": "tier",
                    "model": data.get(model_key, ""),
                    "provider": "",
                    "base_url": data.get(url_key, ""),
                    "api_key": data.get(key_key, ""),
                    "enabled": True,
                    "cascade": [],
                }
            )

    # 2. Slot assignments from router section
    router_data = data.get("router", {})
    slot_field_map = {
        "default": "default",
        "background": "background",
        "think": "think",
        "long_context": "long_context",
        "web_search": "web_search",
        "image": "image",
    }
    for slot_id, router_field in slot_field_map.items():
        rt = router_data.get(router_field, {})
        if isinstance(rt, str):
            model_val = rt
            url_val = ""
            key_val = ""
        elif isinstance(rt, dict):
            model_val = rt.get("model", "")
            url_val = rt.get("base_url", "")
            key_val = rt.get("api_key", "")
        else:
            model_val = ""
            url_val = ""
            key_val = ""
        if model_val:
            assignments.append(
                {
                    "id": slot_id,
                    "kind": "slot",
                    "model": model_val,
                    "provider": "",
                    "base_url": url_val,
                    "api_key": key_val,
                    "enabled": True,
                    "cascade": [],
                }
            )

    # 3. Clean legacy keys
    for tier_keys in legacy_tier_fields.values():
        for key in tier_keys:
            data.pop(key, None)

    # 4. Duplicate assignment ID detection
    seen_ids: set[str] = set()
    for a in assignments:
        aid = a["id"]
        if aid in seen_ids:
            errors.append(
                f"Duplicate assignment id '{aid}' produced by migration; conflict between legacy fields"
            )
        seen_ids.add(aid)

    # 5. Inject v2 fields
    data["schema_version"] = "2.0.0"
    data["assignments"] = assignments
    data["identifier_mappings"] = []

    if errors:
        raise RuntimeError(f"Migration unsafe: {', '.join(errors)}")

    # Safe migration — log the success
    _migration_log(
        "v1-to-v2",
        "Converted legacy tier env-var fields + router slots into unified Assignment model.",
        None,
    )
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def migrate_if_needed(data: dict, file_path: Path) -> dict:
    """Detect schema_version and apply all required migrations in order.

    On successful migration, rewrites the source file at `file_path` with the
    migrated data (FR-023a). Writes migration log beforehand (FR-023b).
    If migration would be unsafe (FR-023c), raises and leaves file untouched.
    """
    from_version = data.get("schema_version", "1.0.0")
    if from_version == CURRENT_VERSION:
        return data

    print(f"⚙️  Migrating config from {from_version} → {CURRENT_VERSION} …")

    # Build migration path
    target_versions = sorted(MIGRATIONS.keys())
    if from_version not in ["1.0.0"] + target_versions:
        raise RuntimeError(f"No migration path known from version '{from_version}'")

    # Apply only the direct v2 migration for now (single-step upgrade)
    if from_version == "1.0.0":
        # Backup original before mutating
        backup_path = file_path.with_suffix(
            f".bak.{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M%S')}"
        )
        shutil.copy2(file_path, backup_path)
        print(f"📦 Backup: {backup_path}")

        result = MIGRATIONS["2.0.0"](data.copy())
        # Atomic rewrite of stored file
        tmp_path = file_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        tmp_path.replace(file_path)
        return result
    else:
        # Unknown version — best effort: try to apply v2 anyway (may still work)
        print(
            f"⚠️  Unknown schema_version '{from_version}'; attempting direct v2 migration"
        )
        return MIGRATIONS["2.0.0"](data.copy())


def _migration_log(slug: str, message: str, errors: Optional[list[str]]) -> None:
    """Write human-readable migration log under config/migrations/."""
    log_dir = Path("config/migrations")
    log_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.log"
    log_path = log_dir / filename

    lines = [
        f"=== Migration: {slug} ===",
        f"Timestamp (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"{message}",
    ]
    if errors:
        lines.append("ERRORS:")
        lines.extend(f"  - {e}" for e in errors)
    lines.append("")  # trailing newline

    log_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 Migration log: {log_path}")

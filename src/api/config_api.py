"""HTTP API for config, assignments, chain, and identifier-mappings.

Implements endpoints from specs/001-unified-config-system/contracts/config-api.yaml.
All write verbs are gated by require_admin; reads require an authenticated user.

See Phase 3 tasks T028, T029, T030 and Phase 6 task T064.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.users_rbac import get_current_user, require_admin
from src.core.assignments import (
    Assignment,
    AssignmentError,
    get_registry as get_assignment_registry,
)
from src.core.identifier_mapping import (
    IdentifierMapping,
    IdentifierMappingError,
    get_registry as get_identifier_mapping_registry,
)
from src.core.config_resolver import resolver
from src.services.observability.audit_log import mask_secret

router = APIRouter(prefix="/api", tags=["config"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas (wire format)
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentIn(BaseModel):
    id: str
    kind: str = Field(pattern="^(tier|slot)$")
    model: str = ""
    provider: str = ""
    base_url: str = ""
    api_key: str = ""
    enabled: bool = True
    cascade: List[str] = Field(default_factory=list)


class AssignmentUpdate(BaseModel):
    model: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    cascade: Optional[List[str]] = None


class IdentifierMappingIn(BaseModel):
    incoming_identifier: str
    assignment_id: str
    enabled: bool = True
    priority: int = 0
    notes: str = ""


class IdentifierMappingUpdate(BaseModel):
    assignment_id: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Assignments
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/assignments")
async def list_assignments(
    _user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """List all assignments — any authenticated user."""
    return [a.to_dict() for a in get_assignment_registry().list()]


@router.get("/assignments/{assignment_id}")
async def get_assignment(
    assignment_id: str, _user=Depends(get_current_user)
) -> Dict[str, Any]:
    a = get_assignment_registry().get(assignment_id)
    if a is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown assignment '{assignment_id}'"
        )
    return a.to_dict()


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    body: AssignmentIn, user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    """Create a new assignment. Tiers cannot be created via API — they are seeded."""
    if body.kind == "tier":
        raise HTTPException(
            status_code=400,
            detail="Tiers are fixed (big/middle/small); use PATCH to modify, not POST",
        )
    try:
        assignment = Assignment.from_dict(body.model_dump())
        created = get_assignment_registry().register(
            assignment, principal=user.get("username", "unknown")
        )
        return created.to_dict()
    except (ValueError, AssignmentError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    user: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        updated = get_assignment_registry().update(
            assignment_id, updates, principal=user.get("username", "unknown")
        )
        return updated.to_dict()
    except AssignmentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: str, user: Dict[str, Any] = Depends(require_admin)
) -> None:
    try:
        get_assignment_registry().delete(
            assignment_id, principal=user.get("username", "unknown")
        )
    except AssignmentError as e:
        msg = str(e)
        if "tier" in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=404, detail=msg)


# ─────────────────────────────────────────────────────────────────────────────
# Identifier mappings
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/identifier-mappings")
async def list_identifier_mappings(
    _user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    return [m.to_dict() for m in get_identifier_mapping_registry().list()]


@router.post("/identifier-mappings", status_code=status.HTTP_201_CREATED)
async def create_identifier_mapping(
    body: IdentifierMappingIn, _user=Depends(require_admin)
) -> Dict[str, Any]:
    try:
        mapping = IdentifierMapping.from_dict(body.model_dump())
        created = get_identifier_mapping_registry().register(mapping)
        return created.to_dict()
    except IdentifierMappingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/identifier-mappings/{incoming_identifier}")
async def update_identifier_mapping(
    incoming_identifier: str,
    body: IdentifierMappingUpdate,
    _user=Depends(require_admin),
) -> Dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        updated = get_identifier_mapping_registry().update(incoming_identifier, updates)
        return updated.to_dict()
    except IdentifierMappingError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)


@router.delete(
    "/identifier-mappings/{incoming_identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_identifier_mapping(
    incoming_identifier: str, _user=Depends(require_admin)
) -> None:
    try:
        get_identifier_mapping_registry().delete(incoming_identifier)
    except IdentifierMappingError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Chain management — US2 (Phase 4)
# ─────────────────────────────────────────────────────────────────────────────

from src.core.proxy_chain import ProxyChain, ProxyEntry, get_chain, reload_chain
import jsonschema


class ProxyEntryIn(BaseModel):
    id: str
    name: str
    url: str = ""
    auth_key: str = ""
    enabled: bool = True
    service_cmd: str = ""
    port: int = 0
    health_path: str = "/health"
    timeout: int = 90
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    type: str = "http"  # or cli_wrapper
    model_prefixes: List[str] = Field(default_factory=list)


class ReorderRequest(BaseModel):
    order: List[str]  # list of entry ids in desired sequence


def _get_entry_by_id(chain: ProxyChain, entry_id: str) -> Optional[ProxyEntry]:
    return next((e for e in chain.entries if e.id == entry_id), None)


@router.get("/chain")
async def list_chain(_user=Depends(get_current_user)) -> List[Dict[str, Any]]:
    """List chain entries in order."""
    chain = get_chain()
    return [asdict(e) for e in chain.entries]


@router.post("/chain", status_code=status.HTTP_201_CREATED)
async def add_chain_entry(
    body: ProxyEntryIn, _user=Depends(require_admin)
) -> Dict[str, Any]:
    """Add a new chain entry. Validates for port conflicts etc."""
    chain = get_chain()
    # Construct ProxyEntry
    entry = ProxyEntry(
        id=body.id,
        name=body.name,
        url=body.url,
        auth_key=body.auth_key,
        enabled=body.enabled,
        order=len(chain.entries),
        service_cmd=body.service_cmd,
        port=body.port,
        health_path=body.health_path,
        timeout=body.timeout,
        extra_headers=body.extra_headers,
        type=body.type,
        model_prefixes=body.model_prefixes,
    )
    # Run validation before adding
    chain.add(entry)
    errors = chain.validate_edit()
    if errors:
        # Remove the entry we just added
        chain.entries.pop()
        chain._renumber()
        raise HTTPException(
            status_code=400, detail="Validation errors: " + "; ".join(errors)
        )
    chain.save()
    # Reload singleton so the running proxy picks up changes
    reload_chain()
    return entry.to_dict()


@router.post("/chain/reorder")
async def reorder_chain(
    body: ReorderRequest, _user=Depends(require_admin)
) -> Dict[str, str]:
    """Reorder the chain according to the provided list of ids."""
    chain = get_chain()
    # Build map id->entry
    existing = {e.id: e for e in chain.entries}
    # Verify all ids are known
    missing = [eid for eid in body.order if eid not in existing]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown entry ids: {missing}")
    # Check for duplicates
    if len(body.order) != len(set(body.order)):
        raise HTTPException(status_code=400, detail="Duplicate ids in order list")
    # Reorder entries in chain based on order list
    new_entries = [existing[eid] for eid in body.order]
    chain.entries = new_entries
    chain._renumber()
    chain.save()
    reload_chain()
    return {"status": "reordered"}


@router.patch("/chain/{entry_id}")
async def update_chain_entry(
    entry_id: str,
    body: Dict[str, Any],
    _user=Depends(require_admin),
) -> Dict[str, Any]:
    """Update a chain entry (partial update)."""
    chain = get_chain()
    entry = _get_entry_by_id(chain, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown entry '{entry_id}'")
    # Apply updates to entry fields (ignore id and order)
    for key, value in body.items():
        if key in ("id", "order"):
            continue
        if hasattr(entry, key):
            setattr(entry, key, value)
    # Validate
    errors = chain.validate_edit()
    if errors:
        # revert changes? Hard to revert; we did in-place mutation. For now, reject.
        raise HTTPException(
            status_code=400, detail="Validation errors: " + "; ".join(errors)
        )
    chain.save()
    reload_chain()
    return entry.to_dict()


@router.delete("/chain/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chain_entry(entry_id: str, _user=Depends(require_admin)) -> None:
    """Remove a chain entry by id."""
    chain = get_chain()
    entry = _get_entry_by_id(chain, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Unknown entry '{entry_id}'")
    idx = next((i for i, e in enumerate(chain.entries) if e.id == entry_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found")
    chain.entries.pop(idx)
    chain._renumber()
    chain.save()
    reload_chain()
    # No content response (204)


# ─────────────────────────────────────────────────────────────────────────────
# Config (provenance) — read-only (T064)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/config")
async def get_full_config(_user=Depends(get_current_user)) -> Dict[str, Any]:
    """Return full resolved config tree with provenance (T064)."""
    snap = resolver.snapshot()
    result: dict[str, Any] = {}
    for field_path, rv in snap.items():
        # Secret masking per FR-035
        schema = resolver._schemas.get(field_path)
        raw_val = rv.raw_value
        val = rv.value
        if schema and schema.is_secret:
            if isinstance(raw_val, str):
                raw_val = mask_secret(raw_val)
            if isinstance(val, str):
                val = mask_secret(val)
        result[field_path] = {
            "value": val,
            "raw_value": raw_val,
            "source_layer": rv.source_layer,
        }
    return result


@router.get("/config/{field_path:path}")
async def get_config_field(
    field_path: str, _user=Depends(get_current_user)
) -> Dict[str, Any]:
    """Return a single field with provenance (T064)."""
    try:
        rv = resolver.resolve(field_path)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown field '{field_path}'")

    # Secret masking per FR-035
    schema = resolver._schemas.get(field_path)
    raw_val = rv.raw_value
    val = rv.value
    if schema and schema.is_secret:
        if isinstance(raw_val, str):
            raw_val = mask_secret(raw_val)
        if isinstance(val, str):
            val = mask_secret(val)

    return {
        "field_path": rv.field_path,
        "value": val,
        "raw_value": raw_val,
        "source_layer": rv.source_layer,
    }


# ── Settings write endpoint (manifest-driven) ─────────────────────────────────

from pydantic import BaseModel as _BaseModel
from typing import Any as _Any


class _SettingsPayload(_BaseModel):
    settings: dict  # {ENV_VAR: value}
    persist: bool = True  # write to .env (default True)


@router.get("/settings")
async def get_all_settings(_user=Depends(get_current_user)):
    """
    Return ALL configurable settings from the manifest with current values.
    Uses config_manifest.py as the canonical source of truth.
    Masks secret fields.
    """
    from src.core.config_manifest import as_config_response, SETTINGS, GROUP_LABELS, get_all_groups
    response = as_config_response()
    # Add metadata: groups, descriptions, types, widget hints
    meta = {}
    for s in SETTINGS:
        meta[s.env_var.lower()] = {
            "env_var": s.env_var,
            "group": s.group,
            "group_label": GROUP_LABELS.get(s.group, s.group),
            "description": s.description,
            "type": s.type.__name__,
            "default": str(s.default) if s.default is not None else None,
            "choices": s.choices,
            "secret": s.secret,
            "tui_widget": s.tui_widget,
            "web_component": s.web_component,
            "units": s.units,
            "min_val": s.min_val,
            "max_val": s.max_val,
            "cli_flag": s.cli_flag,
        }
    return {
        "values": response,
        "meta": meta,
        "groups": get_all_groups(),
        "group_labels": GROUP_LABELS,
    }


@router.post("/settings")
async def update_settings(
    payload: _SettingsPayload,
    _user=Depends(require_admin),
):
    """
    Update settings by writing ENV_VAR values.

    If persist=True (default): writes to .env file.
    If persist=False: applies to os.environ for this session only.

    Body: {"settings": {"ENV_VAR": "value", ...}, "persist": true}
    """
    import os as _os
    from src.core.config_manifest import get_by_env_var

    updated = {}
    skipped = {}

    for key, value in payload.settings.items():
        env_key = str(key).upper()
        # Validate against manifest if setting is known
        setting = get_by_env_var(env_key)
        if setting is None:
            skipped[env_key] = "unknown setting (not in manifest)"
            continue

        str_val = str(value) if value is not None else ""
        _os.environ[env_key] = str_val
        updated[env_key] = "***" if setting.secret else str_val

    if payload.persist and updated:
        try:
            from src.cli.env_utils import update_env_values
            update_env_values({k: _os.environ.get(k, "") for k in updated if not k.endswith("_KEY")})
            # Write secrets separately (don't log them)
            secret_updates = {k: _os.environ.get(k, "") for k in updated if k.endswith("_KEY") or get_by_env_var(k) and get_by_env_var(k).secret}
            if secret_updates:
                update_env_values(secret_updates)
        except Exception as e:
            return {"updated": updated, "skipped": skipped, "persist_error": str(e)}

    return {
        "updated": updated,
        "skipped": skipped,
        "persisted": payload.persist,
        "count": len(updated),
    }

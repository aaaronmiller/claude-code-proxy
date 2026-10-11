"""Structured model-scan diagnostics across the eight operator states.

CG-T050. One read-only report distinguishes process, dependency, catalog,
snapshot, quota, binding, reload, and degraded state. The report carries
counts, hashes, versions, and paths only: no credential values, no request
data, and no provider traffic.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.core.model_scan_runtime import (
    get_active_allocation,
    get_active_binding,
    last_reload_summary,
)
from src.core.proxy_chain import get_chain
from src.core.quota_store import QuotaMeterStore
from src.services.models import model_scan_snapshot

SECTIONS = (
    "process",
    "dependency",
    "catalog",
    "snapshot",
    "quota",
    "binding",
    "reload",
)


def _sanitized_url(value: str) -> str:
    if not value:
        return ""
    parts = urlsplit(value)
    netloc = parts.netloc.rpartition("@")[2]
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


@dataclass
class _Report:
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)
    degraded: list[str] = field(default_factory=list)

    def put(self, name: str, state: str, **facts: Any) -> dict[str, Any]:
        entry: dict[str, Any] = {"state": state}
        entry.update(facts)
        self.sections[name] = entry
        if state in {"missing", "stale", "degraded", "corrupt", "error"}:
            self.degraded.append(f"{name}:{state}")
        return entry


def collect_diagnostics(*, quota_store_path: str | None = None) -> dict[str, Any]:
    """Collect the current read-only diagnostic report."""
    report = _Report()
    chain = get_chain()
    config = chain.model_scan
    now = datetime.now(timezone.utc)

    process = report.put(
        "process",
        "ok",
        model_scan_enabled=config.enabled,
        allocator_enabled=bool(getattr(config, "allocator_enabled", False)),
        policy=str(config.policy),
        proxy_chain_schema_version=chain.schema_version,
        runtime_module="src.core.model_scan_runtime",
        python_version=sys.version.split()[0],
    )
    if not config.enabled:
        process["state"] = "disabled"

    snapshot_path = str(getattr(config, "snapshot_path", "") or "").strip()
    gateway_url = str(getattr(config, "gateway_url", "") or "").strip()
    raw_snap = None
    dependency_state = "ok"
    if not snapshot_path and not gateway_url:
        dependency_state = "missing"
        report.put(
            "dependency",
            "missing",
            reason="neither snapshot_path nor gateway_url is configured",
        )
    else:
        exists = bool(snapshot_path) and Path(snapshot_path).expanduser().exists()
        report.put(
            "dependency",
            "ok" if exists else "missing",
            snapshot_path=snapshot_path or None,
            snapshot_file_exists=exists,
            gateway_url=_sanitized_url(gateway_url) if gateway_url else None,
        )
        if snapshot_path and not exists:
            dependency_state = "missing"
        if exists:
            try:
                raw_snap = model_scan_snapshot.load(
                    str(Path(snapshot_path).expanduser())
                )
            except Exception:
                raw_snap = None

    snap_facts: dict[str, Any] = {}
    snapshot_state = "missing"
    if raw_snap is not None:
        generated_at = getattr(raw_snap, "generated_at", None)
        scan_id = getattr(raw_snap, "scan_id", None)
        schema_version = getattr(raw_snap, "schema_version", "")
        slots = getattr(raw_snap, "slots", None) or {}
        snap_facts = {
            "scan_id": scan_id,
            "snapshot_schema_version": schema_version,
            "generated_at": generated_at,
            "slot_count": len(slots),
        }
        limit = int(getattr(config, "staleness_limit_s", 86400) or 86400)
        stale = model_scan_snapshot.is_data_stale(raw_snap, limit)
        snapshot_state = "stale" if stale else "ok"
    report.put("snapshot", snapshot_state, **snap_facts)

    if raw_snap is not None:
        report.put("catalog", "ok", **snap_facts)
    else:
        report.put(
            "catalog",
            "missing",
            reason="no loadable routing snapshot carries catalog facts",
        )

    store_path = quota_store_path or str(
        getattr(config, "quota_store_path", "") or ""
    )
    quota_state = "ok"
    quota_facts: dict[str, Any] = {"store_path": store_path or None}
    if store_path:
        expanded = Path(store_path).expanduser()
        quota_facts["store_exists"] = expanded.exists()
        if expanded.exists():
            try:
                raw = expanded.read_text(encoding="utf-8")
                payload = json.loads(raw) if raw.strip() else {}
                meters = QuotaMeterStore(str(expanded)).load()
                if not isinstance(payload, dict) or "meters" not in payload:
                    raise ValueError("meter store is not a valid meter document")
                limit = int(
                    getattr(config, "quota_staleness_limit_s", 86400) or 86400
                )
                stale_count = 0
                for meter in meters:
                    observed = float(getattr(meter, "observed_at", 0.0) or 0.0)
                    if observed <= 0.0:
                        continue
                    if now.timestamp() - observed > limit:
                        stale_count += 1
                quota_facts.update(
                    meter_count=len(meters), stale_meter_count=stale_count
                )
                if stale_count:
                    quota_state = "stale"
            except Exception:
                quota_facts["reason"] = "meter store could not be parsed"
                quota_state = "corrupt"
    else:
        quota_state = "missing"
        quota_facts["reason"] = "no quota store path configured"
    report.put("quota", quota_state, **quota_facts)

    active = get_active_binding()
    if active is not None:
        report.put(
            "binding",
            "ok",
            scan_id=active.scan_id,
            binding_schema_version=active.schema_version,
            global_tier_count=len(active.global_tiers),
            overlay_profiles=sorted(active.overlay.keys()),
            provenance_sources=sorted(set(active.provenance.values())),
        )
    else:
        report.put(
            "binding",
            "ok" if not config.enabled else "missing",
            reason="no active binding" if config.enabled else "model scan disabled",
        )

    reload_summary = last_reload_summary()
    if reload_summary is None:
        report.put("reload", "idle", reason="no reload has run in this process")
    else:
        reload_state = "ok" if not reload_summary.get("error") else "error"
        report.put(
            "reload",
            reload_state,
            enabled=reload_summary.get("enabled"),
            changed=reload_summary.get("changed"),
            scan_id=reload_summary.get("scan_id"),
            error=reload_summary.get("error") or "",
            allocator=reload_summary.get("allocator", {}).get("enabled", False),
        )

    allocation = get_active_allocation()
    report.sections["binding"]["allocator_active"] = bool(
        allocation.get("enabled")
    )

    overall = "ok"
    if process["state"] == "disabled":
        overall = "disabled"
    elif report.degraded:
        overall = "degraded"
    return {
        "mode": "diagnostics",
        "schema_version": "1.0.0",
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model_scan_enabled": config.enabled,
        "overall": overall,
        "sections": report.sections,
        "degraded": report.degraded,
        "persistent_writes": [],
        "credential_fields_excluded": True,
    }


def assert_no_secrets(report: dict[str, Any]) -> None:
    """Raise if any credential-bearing field leaked into the report."""
    forbidden = ("api_key", "apikey", "authorization", "bearer ")
    blob = json.dumps(report, default=str).lower()
    for needle in forbidden:
        if needle in blob:
            raise ValueError(f"diagnostics leaked a forbidden field: {needle}")

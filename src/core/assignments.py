"""Unified Assignment model + registry — replaces tier/slot asymmetry.

An Assignment is a (provider, model, base_url, api_key, enabled, cascade) target.
Two kinds: `tier` (fixed: big/middle/small) and `slot` (operator-defined).

See specs/001-unified-config-system/data-model.md for the full schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional
import re
import threading


@dataclass
class Assignment:
    """Configuration assignment for a tier or slot."""

    id: str
    kind: Literal["tier", "slot"]
    model: str = ""
    provider: str = ""
    base_url: str = ""
    api_key: str = ""
    enabled: bool = True
    cascade: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Validate Assignment constraints (FR-003, FR-003a)."""
        if self.kind == "tier":
            if self.id not in {"big", "middle", "small"}:
                raise ValueError(
                    f"Tier id must be one of 'big', 'middle', 'small'; got '{self.id}'"
                )
        elif self.kind == "slot":
            if not re.match(r"^[a-z][a-z0-9_]{0,63}$", self.id):
                raise ValueError(
                    f"Slot id must match ^[a-z][a-z0-9_]{0, 63}$; got '{self.id}'"
                )
        else:
            raise ValueError(f"kind must be 'tier' or 'slot', got '{self.id}'")

        # cascade must be list of non-empty strings
        if self.cascade:
            for item in self.cascade:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("cascade entries must be non-empty strings")

    def to_dict(self) -> dict:
        """Serialize to dict for JSON API responses."""
        return {
            "id": self.id,
            "kind": self.kind,
            "model": self.model,
            "provider": self.provider,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "enabled": self.enabled,
            "cascade": self.cascade,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Assignment":
        """Deserialize from dict (API request body)."""
        return cls(
            id=data["id"],
            kind=data["kind"],
            model=data.get("model", ""),
            provider=data.get("provider", ""),
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            cascade=data.get("cascade", []),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Registry (T025) — CRUD over Assignment list backed by ProxyChain persistence
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentError(Exception):
    """Raised on invalid registry operations (duplicate id, tier deletion, …)."""


class AssignmentRegistry:
    """CRUD facade over the Assignment list held in ProxyChain.

    All mutations persist via ProxyChain.save() and notify the ConfigResolver
    so downstream readers (Config shim, request router) see the change
    immediately (FR-007).
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()

    # ── internal helpers ────────────────────────────────────────────────────

    def _chain(self):
        """Return the current ProxyChain singleton."""
        from src.core.proxy_chain import get_chain

        return get_chain()

    def _persist(self, principal: str = "registry") -> None:
        """Save ProxyChain to disk and push per-field updates into the resolver."""
        chain = self._chain()
        chain.save()

        # Push to resolver STORED layer so Config shim reads see the new values.
        try:
            from src.core.config_resolver import resolver, ConfigLayer, FieldSchema

            for a in chain.assignments:
                prefix = f"assignments.{a.id}"
                fields = [
                    ("model", str, "", False),
                    ("provider", str, "", False),
                    ("base_url", str, "", False),
                    ("api_key", str, "", True),
                    ("enabled", bool, True, False),
                ]
                for field_name, ftype, fdefault, fsecret in fields:
                    fp = f"{prefix}.{field_name}"
                    if fp not in resolver._schemas:
                        resolver.register_schema(
                            fp,
                            FieldSchema(type=ftype, default=fdefault, is_secret=fsecret),
                        )
                    resolver._layers[ConfigLayer.STORED][fp] = getattr(a, field_name)
                cascade_fp = f"{prefix}.cascade"
                if cascade_fp not in resolver._schemas:
                    resolver.register_schema(
                        cascade_fp,
                        FieldSchema(type=list, default=[], is_secret=False),
                    )
                resolver._layers[ConfigLayer.STORED][cascade_fp] = a.cascade
        except Exception:
            # Resolver not yet initialized during early startup — chain persist is enough.
            pass

    # ── public API ──────────────────────────────────────────────────────────

    def list(self) -> list[Assignment]:
        """All assignments (tiers + slots) in insertion order."""
        with self._lock:
            return list(self._chain().assignments)

    def get(self, assignment_id: str) -> Optional[Assignment]:
        """Look up by id, or None if absent."""
        with self._lock:
            for a in self._chain().assignments:
                if a.id == assignment_id:
                    return a
            return None

    def register(self, assignment: Assignment, principal: str = "registry") -> Assignment:
        """Add a new assignment. Raises AssignmentError on duplicate id."""
        with self._lock:
            chain = self._chain()
            if any(a.id == assignment.id for a in chain.assignments):
                raise AssignmentError(f"Assignment id '{assignment.id}' already exists")
            chain.assignments.append(assignment)
            self._persist(principal=principal)
            return assignment

    def update(
        self, assignment_id: str, updates: dict, principal: str = "registry"
    ) -> Assignment:
        """Partial update. `kind` and `id` are immutable."""
        with self._lock:
            chain = self._chain()
            for i, a in enumerate(chain.assignments):
                if a.id != assignment_id:
                    continue
                # kind / id are immutable
                forbidden = {"id", "kind"} & updates.keys()
                if forbidden:
                    raise AssignmentError(
                        f"Cannot modify immutable fields: {', '.join(sorted(forbidden))}"
                    )
                # Build a new Assignment with updates applied so validators fire
                new_data = a.to_dict()
                new_data.update(updates)
                new_assignment = Assignment.from_dict(new_data)
                chain.assignments[i] = new_assignment
                self._persist(principal=principal)
                return new_assignment
            raise AssignmentError(f"Assignment '{assignment_id}' not found")

    def delete(self, assignment_id: str, principal: str = "registry") -> None:
        """Remove a slot assignment. Tier deletion is forbidden (FR-003)."""
        with self._lock:
            chain = self._chain()
            for i, a in enumerate(chain.assignments):
                if a.id != assignment_id:
                    continue
                if a.kind == "tier":
                    raise AssignmentError(
                        f"Cannot delete tier '{assignment_id}' — tiers are fixed (FR-003)"
                    )
                chain.assignments.pop(i)
                self._persist(principal=principal)
                return
            raise AssignmentError(f"Assignment '{assignment_id}' not found")


# Module-level singleton
_registry: Optional[AssignmentRegistry] = None


def get_registry() -> AssignmentRegistry:
    """Return the global AssignmentRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = AssignmentRegistry()
    return _registry

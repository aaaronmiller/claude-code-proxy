"""Incoming-identifier → Assignment mapping + registry.

Routes upstream identifiers (Anthropic model names, Hermes agent roles,
future Anthropic task types) to assignments without code changes.

See specs/001-unified-config-system/data-model.md#identifiermapping.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IdentifierMapping:
    """Maps an incoming identifier to an assignment."""

    incoming_identifier: str
    assignment_id: str
    enabled: bool = True
    priority: int = 0
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict for JSON API responses."""
        return {
            "incoming_identifier": self.incoming_identifier,
            "assignment_id": self.assignment_id,
            "enabled": self.enabled,
            "priority": self.priority,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IdentifierMapping":
        """Deserialize from dict (API request body)."""
        return cls(
            incoming_identifier=data["incoming_identifier"],
            assignment_id=data["assignment_id"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            notes=data.get("notes", ""),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Registry (T026) — CRUD + priority-respecting lookup
# ─────────────────────────────────────────────────────────────────────────────


class IdentifierMappingError(Exception):
    """Raised on duplicate incoming_identifier, unknown assignment reference, etc."""


class IdentifierMappingRegistry:
    """CRUD facade + lookup_by_incoming_identifier, backed by ProxyChain persistence."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def _chain(self):
        from src.core.proxy_chain import get_chain

        return get_chain()

    def _persist(self) -> None:
        self._chain().save()

    # ── public API ──────────────────────────────────────────────────────────

    def list(self) -> list[IdentifierMapping]:
        with self._lock:
            return list(self._chain().identifier_mappings)

    def get(self, incoming_identifier: str) -> Optional[IdentifierMapping]:
        with self._lock:
            for m in self._chain().identifier_mappings:
                if m.incoming_identifier == incoming_identifier:
                    return m
            return None

    def register(self, mapping: IdentifierMapping) -> IdentifierMapping:
        with self._lock:
            chain = self._chain()
            if any(
                m.incoming_identifier == mapping.incoming_identifier
                for m in chain.identifier_mappings
            ):
                raise IdentifierMappingError(
                    f"Mapping for incoming_identifier '{mapping.incoming_identifier}' already exists"
                )
            # Validate that assignment_id exists (FK check)
            self._validate_assignment_exists(mapping.assignment_id, chain)
            chain.identifier_mappings.append(mapping)
            self._persist()
            return mapping

    def update(self, incoming_identifier: str, updates: dict) -> IdentifierMapping:
        with self._lock:
            chain = self._chain()
            if "incoming_identifier" in updates:
                raise IdentifierMappingError(
                    "Cannot modify immutable field 'incoming_identifier'; delete and re-add"
                )
            for i, m in enumerate(chain.identifier_mappings):
                if m.incoming_identifier != incoming_identifier:
                    continue
                new_data = m.to_dict()
                new_data.update(updates)
                if "assignment_id" in updates:
                    self._validate_assignment_exists(
                        updates["assignment_id"], chain
                    )
                new_mapping = IdentifierMapping.from_dict(new_data)
                chain.identifier_mappings[i] = new_mapping
                self._persist()
                return new_mapping
            raise IdentifierMappingError(
                f"Mapping '{incoming_identifier}' not found"
            )

    def delete(self, incoming_identifier: str) -> None:
        with self._lock:
            chain = self._chain()
            for i, m in enumerate(chain.identifier_mappings):
                if m.incoming_identifier != incoming_identifier:
                    continue
                chain.identifier_mappings.pop(i)
                self._persist()
                return
            raise IdentifierMappingError(
                f"Mapping '{incoming_identifier}' not found"
            )

    def lookup_by_incoming_identifier(
        self, incoming_identifier: str
    ) -> Optional[IdentifierMapping]:
        """Return the enabled mapping for `incoming_identifier` with highest priority.

        On no match, returns None — caller falls back to existing tier-based
        resolution (FR-003b, FR-003c).
        """
        with self._lock:
            candidates = [
                m
                for m in self._chain().identifier_mappings
                if m.enabled and m.incoming_identifier == incoming_identifier
            ]
            if not candidates:
                return None
            candidates.sort(key=lambda m: m.priority, reverse=True)
            return candidates[0]

    def _validate_assignment_exists(self, assignment_id: str, chain) -> None:
        """FK-style check: referenced assignment must exist."""
        if not any(a.id == assignment_id for a in chain.assignments):
            raise IdentifierMappingError(
                f"Referenced assignment_id '{assignment_id}' does not exist"
            )


_registry: Optional[IdentifierMappingRegistry] = None


def get_registry() -> IdentifierMappingRegistry:
    global _registry
    if _registry is None:
        _registry = IdentifierMappingRegistry()
    return _registry

"""CLI-argument → ConfigResolver CLI-layer adapter.

Translates argparse output into ConfigResolver writes at the CLI (highest-precedence)
layer so CLI flags flow through the same resolution path as every other surface (FR-017).

Used by start_proxy.py after argparse parses --assign and --map-identifier flags.
"""

from __future__ import annotations

import argparse
from typing import Any, Iterable


def _parse_kv_pairs(tokens: Iterable[str]) -> dict[str, str]:
    """Parse `k=v k=v …` tokens into a dict. Values after `=` may contain `=`."""
    result: dict[str, str] = {}
    for tok in tokens:
        if "=" not in tok:
            raise ValueError(
                f"Expected key=value, got '{tok}' (missing '=')"
            )
        k, v = tok.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def apply_cli_overlay(args: argparse.Namespace) -> None:
    """Translate argparse namespace into resolver CLI-layer writes + registry calls.

    Handles:
    - --assign id k=v …     → upsert assignment via AssignmentRegistry
    - --map-identifier k=v  → upsert IdentifierMapping
    - --chain-order a,b,c   → reorder ProxyChain (US2 territory but wired here)
    - --chain-enable id     → toggle entry enabled=True
    - --chain-disable id    → toggle entry enabled=False

    CLI writes update both the resolver CLI layer (for provenance) and the
    stored registries (for persistence). This dual-write is consistent with
    Principle VI: every surface goes through the same resolver.
    """
    from src.core.config_resolver import resolver, ConfigLayer
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

    # --assign big model=... provider=... api_key=...
    assign_args: list[list[str]] | None = getattr(args, "assign", None)
    if assign_args:
        reg = get_assignment_registry()
        for group in assign_args:
            if not group:
                continue
            assignment_id = group[0]
            try:
                fields = _parse_kv_pairs(group[1:])
            except ValueError as e:
                print(f"⚠️  --assign {assignment_id}: {e}; skipping")
                continue

            existing = reg.get(assignment_id)
            if existing is None:
                kind = fields.pop(
                    "kind",
                    "tier" if assignment_id in {"big", "middle", "small"} else "slot",
                )
                try:
                    a = Assignment.from_dict({"id": assignment_id, "kind": kind, **fields})
                    reg.register(a, principal="cli")
                    print(f"✓ created assignment '{assignment_id}' (kind={kind})")
                except (ValueError, AssignmentError) as e:
                    print(f"⚠️  --assign {assignment_id}: {e}")
            else:
                try:
                    reg.update(assignment_id, fields, principal="cli")
                    print(f"✓ updated assignment '{assignment_id}' ({', '.join(fields)})")
                except (ValueError, AssignmentError) as e:
                    print(f"⚠️  --assign {assignment_id}: {e}")

            # Also write each field into the CLI layer for provenance
            prefix = f"assignments.{assignment_id}"
            for fname, fval in fields.items():
                try:
                    resolver._layers[ConfigLayer.CLI][f"{prefix}.{fname}"] = fval
                except Exception:
                    pass

    # --map-identifier incoming=... assignment=...
    map_args: list[list[str]] | None = getattr(args, "map_identifier", None)
    if map_args:
        reg = get_identifier_mapping_registry()
        for group in map_args:
            try:
                fields = _parse_kv_pairs(group)
            except ValueError as e:
                print(f"⚠️  --map-identifier: {e}; skipping")
                continue

            inc = fields.get("incoming") or fields.get("incoming_identifier")
            assign = fields.get("assignment") or fields.get("assignment_id")
            if not inc or not assign:
                print(
                    "⚠️  --map-identifier requires 'incoming=...' and 'assignment=...'; skipping"
                )
                continue

            mapping_data = {
                "incoming_identifier": inc,
                "assignment_id": assign,
                "enabled": fields.get("enabled", "true").lower() == "true",
                "priority": int(fields.get("priority", "0")),
                "notes": fields.get("notes", ""),
            }
            try:
                if reg.get(inc) is None:
                    reg.register(IdentifierMapping.from_dict(mapping_data))
                    print(f"✓ mapped '{inc}' → '{assign}'")
                else:
                    reg.update(
                        inc,
                        {
                            k: v
                            for k, v in mapping_data.items()
                            if k != "incoming_identifier"
                        },
                    )
                    print(f"✓ updated mapping '{inc}' → '{assign}'")
            except IdentifierMappingError as e:
                print(f"⚠️  --map-identifier '{inc}': {e}")

    # --chain-order a,b,c (US2 territory; wired here for CLI parity)
    chain_order: str | None = getattr(args, "chain_order", None)
    if chain_order:
        from src.core.proxy_chain import get_chain

        chain = get_chain()
        desired = [x.strip() for x in chain_order.split(",") if x.strip()]
        by_id = {e.id: e for e in chain.entries}
        missing = [x for x in desired if x not in by_id]
        if missing:
            print(f"⚠️  --chain-order: unknown entry id(s): {', '.join(missing)}")
        else:
            # Preserve any entries not mentioned, at the tail
            mentioned = set(desired)
            reordered = [by_id[i] for i in desired] + [
                e for e in chain.entries if e.id not in mentioned
            ]
            for i, e in enumerate(reordered):
                e.order = i
            chain.entries = reordered
            chain.save()
            print(f"✓ chain reordered: {', '.join(e.id for e in chain.entries)}")

    # --chain-enable / --chain-disable
    for flag_name, target_enabled in (("chain_enable", True), ("chain_disable", False)):
        ids = getattr(args, flag_name, None)
        if not ids:
            continue
        from src.core.proxy_chain import get_chain

        chain = get_chain()
        for eid in ids:
            for e in chain.entries:
                if e.id == eid:
                    e.enabled = target_enabled
                    print(
                        f"✓ chain entry '{eid}' {'enabled' if target_enabled else 'disabled'}"
                    )
                    break
            else:
                print(f"⚠️  --chain-{'enable' if target_enabled else 'disable'}: unknown id '{eid}'")
        chain.save()

    # --delete-assignment
    delete_assignments = getattr(args, "delete_assignment", None)
    if delete_assignments:
        reg = get_assignment_registry()
        for aid in delete_assignments:
            try:
                reg.delete(aid, principal="cli")
                print(f"✓ deleted assignment '{aid}'")
            except AssignmentError as e:
                print(f"⚠️  --delete-assignment '{aid}': {e}")

    # --delete-mapping
    delete_mappings = getattr(args, "delete_mapping", None)
    if delete_mappings:
        reg = get_identifier_mapping_registry()
        for inc in delete_mappings:
            try:
                reg.delete(inc)
                print(f"✓ deleted mapping '{inc}'")
            except IdentifierMappingError as e:
                print(f"⚠️  --delete-mapping '{inc}': {e}")

    # --chain-add id k=v ...
    chain_add: list[list[str]] | None = getattr(args, "chain_add", None)
    if chain_add:
        from src.core.proxy_chain import get_chain, ProxyEntry

        chain = get_chain()
        for group in chain_add:
            if not group:
                continue
            entry_id = group[0]
            try:
                fields = _parse_kv_pairs(group[1:])
            except ValueError as e:
                print(f"⚠️  --chain-add {entry_id}: {e}")
                continue
            if any(e.id == entry_id for e in chain.entries):
                print(f"⚠️  --chain-add: entry '{entry_id}' already exists")
                continue
            entry_fields = {
                "id": entry_id,
                "name": fields.get("name", entry_id),
                "url": fields.get("url", ""),
                "auth_key": fields.get("auth_key", ""),
                "enabled": fields.get("enabled", "true").lower() == "true",
                "order": len(chain.entries),
                "service_cmd": fields.get("service_cmd", ""),
                "port": int(fields.get("port", "0")),
                "health_path": fields.get("health_path", "/health"),
                "timeout": int(fields.get("timeout", "90")),
                "type": fields.get("type", "http"),
            }
            try:
                chain.entries.append(ProxyEntry(**entry_fields))
                errors = chain.validate_edit() if hasattr(chain, "validate_edit") else []
                if errors:
                    chain.entries.pop()
                    print(f"⚠️  --chain-add '{entry_id}': validation failed: {'; '.join(errors)}")
                else:
                    chain.save()
                    print(f"✓ added chain entry '{entry_id}'")
            except Exception as e:
                print(f"⚠️  --chain-add '{entry_id}': {e}")

    # --chain-remove
    chain_remove: list[str] | None = getattr(args, "chain_remove", None)
    if chain_remove:
        from src.core.proxy_chain import get_chain

        chain = get_chain()
        for rid in chain_remove:
            idx = next(
                (i for i, e in enumerate(chain.entries) if e.id == rid), None
            )
            if idx is None:
                print(f"⚠️  --chain-remove: unknown id '{rid}'")
                continue
            chain.entries.pop(idx)
            print(f"✓ removed chain entry '{rid}'")
        # Renumber + save once after all removals
        for i, e in enumerate(chain.entries):
            e.order = i
        chain.save()


def apply_cli_readonly(args: argparse.Namespace) -> None:
    """Read-only CLI commands: --list-*, --show-config. Print and exit.

    These do not start the proxy server; they print to stdout for scripting.
    """
    from src.core.assignments import get_registry as get_assignment_registry
    from src.core.identifier_mapping import (
        get_registry as get_identifier_mapping_registry,
    )
    from src.core.proxy_chain import get_chain
    from src.core.config_resolver import resolver

    if getattr(args, "list_assignments", False):
        print("Assignments:")
        for a in get_assignment_registry().list():
            enabled = "✓" if a.enabled else "✗"
            cascade = f" cascade=[{','.join(a.cascade)}]" if a.cascade else ""
            print(
                f"  [{enabled}] {a.id:<20} kind={a.kind:<4} model={a.model or '(inherit)'!s:<40} "
                f"provider={a.provider or '(auto)'}{cascade}"
            )

    if getattr(args, "list_mappings", False):
        print("Identifier Mappings (by priority desc):")
        mappings = sorted(
            get_identifier_mapping_registry().list(),
            key=lambda m: (-m.priority, m.incoming_identifier),
        )
        for m in mappings:
            enabled = "✓" if m.enabled else "✗"
            notes = f"  [{m.notes}]" if m.notes else ""
            print(
                f"  [{enabled}] p={m.priority:<3} {m.incoming_identifier:<35} → {m.assignment_id}{notes}"
            )

    if getattr(args, "list_chain", False):
        print("Chain entries (in request order):")
        for e in get_chain().entries:
            enabled = "✓" if e.enabled else "✗"
            port = f":{e.port}" if e.port else ""
            print(
                f"  [{enabled}] [{e.order}] {e.id:<20} {e.name:<40} {e.url or '(cli wrapper)'}{port}"
            )

    # --show-config-field or --where (alias)
    show = getattr(args, "show_config_field", None)
    if show is None:
        show = getattr(args, "where_field", None)
    if show is not None:
        if show == "*":
            print("Full resolved config (with provenance):")
            for field_path, rv in sorted(resolver.snapshot().items()):
                masked = rv.value
                schema = resolver._schemas.get(field_path)
                if schema and schema.is_secret and isinstance(masked, str) and masked:
                    masked = f"{masked[:4]}...{masked[-4:]}" if len(masked) >= 12 else "***"
                print(f"  {field_path:<45} = {masked!r:<30}  [{rv.source_layer}]")
        else:
            try:
                rv = resolver.resolve(show)
                print(f"{rv.field_path}:")
                print(f"  value:        {rv.value!r}")
                print(f"  raw_value:    {rv.raw_value!r}")
                print(f"  source_layer: {rv.source_layer}")
            except KeyError:
                print(f"⚠️  unknown field '{show}'")

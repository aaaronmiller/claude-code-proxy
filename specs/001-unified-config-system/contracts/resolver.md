# Internal Contract — `ConfigResolver`

**Feature**: 001-unified-config-system | **Phase**: 1 | **Date**: 2026-04-23
**Module**: `src/core/config_resolver.py`

Contract for the single resolver that every surface uses. Every configuration read in feature code MUST go through this contract (Constitution Principle VI).

---

## Invariants

1. **Layer order is data, not code.** Stored as a module-level tuple `LAYERS_BY_PRECEDENCE: tuple[ConfigLayer, ...]`. Tests MAY permute this tuple to verify precedence walking; production code MUST NOT.
2. **Resolve is pure.** `resolve(field_path)` produces the same `ResolvedValue` for identical layer contents; it performs no I/O on the hot path.
3. **Writes are atomic per field.** A `set()` either succeeds fully or leaves no trace; partial writes are a contract violation.
4. **Thread-safety.** `resolve()` is safe to call concurrently with `set()` and with other `resolve()` calls. `set()` is serialized by an internal lock.
5. **In-flight isolation.** A `set()` DOES NOT affect requests already resolving values. Each request captures a snapshot of the resolver state at its entry; subsequent reads within the same request use that snapshot.

---

## Methods

### `resolve(field_path: str) -> ResolvedValue`

Walk `LAYERS_BY_PRECEDENCE`. Return the first layer whose dict contains `field_path`. `raw_value` is the stored value; `value` is post-`${VAR}`-expansion. `source_layer` names the winning layer.

- Raises `KeyError` when no layer supplies the field AND no default exists.
- Does not emit logs or metrics on the hot path (Principle V).

### `set(field_path: str, value: Any, layer: ConfigLayer) -> None`

Write into the specified layer. Valid layers for `set`:

- `ConfigLayer.CLI` — only during startup by argparse adapter.
- `ConfigLayer.STORED` — every UI-initiated edit. Persists to disk (`proxy_chain.json`) on success.
- All other layers are **read-only** to `set()`; they come from environment or defaults.

On persistent-layer writes:
1. Validate against schema (types, cross-field constraints from spec FRs).
2. If valid: atomic file rewrite (write-to-temp + rename).
3. Emit change event to subscribers.
4. Append `AuditLogEntry` (caller-provided `principal`).

On invalid writes: raise `ConfigValidationError` with `field_path` + specific message (FR-013). No state change.

### `snapshot() -> dict[str, ResolvedValue]`

Full resolved view for every known field path. Used by `GET /api/config`. O(N) where N is total field count. Safe to call concurrently with writes.

### `subscribe(callback: Callable[[ConfigChangeEvent], None]) -> Callable[[], None]`

Register a callback fired on every persisted write. Returns an unsubscribe fn. Callbacks run on a dedicated notifier thread — must not block. Used by the SSE endpoint and the TUI refresh layer.

`ConfigChangeEvent` carries: `field_path`, `after_value` (resolved, secrets masked), `source_layer`, `seq` (monotonic).

### `register_schema(field_path: str, field_schema: FieldSchema) -> None`

Tell the resolver about a new field. `FieldSchema` declares type, default, validators, `is_secret` flag (gates masking), and optional `env_alias` for legacy env-var translation (FR-023, R5).

Used at startup by each module that owns config fields (e.g., `proxy_chain.py` registers `chain.*` fields, `assignments.py` registers `assignments.*`).

---

## `FieldSchema`

| Field | Type | Purpose |
|---|---|---|
| `type` | `type` or typing hint | For coercion and JSON-schema generation |
| `default` | `Any` | Value used when no layer supplies it |
| `validators` | `list[Callable[[Any], None]]` | Raise `ConfigValidationError` on invalid input |
| `is_secret` | `bool` | Controls masking in audit log and `/api/config` responses |
| `env_alias` | `Optional[str]` | Legacy env-var name to honor during deprecation window |
| `description` | `str` | For operator-facing help text |

Schemas are the one place where "what is a valid value for this field" is expressed. All surfaces consult them.

---

## Legacy env-var aliasing (FR-023, FR-024)

On startup, the resolver scans shell env + `.env` for every `FieldSchema.env_alias`. Matching values populate the `SHELL_ENV` or `DOTENV` layer at the modern field path. The legacy name in the env is flagged in a deprecation-summary set.

At end-of-startup (per R5), the resolver logs one block:

```
⚠  Deprecated env vars in use (set modern equivalents to silence):
   BIG_MODEL          → assignments.big.model
   ENABLE_BIG_ENDPOINT → (remove; enabled flag is on the assignment)
   BIG_ENDPOINT        → assignments.big.base_url
```

---

## Change-event contract

`subscribe()` callbacks receive `ConfigChangeEvent` objects with no sensitive values (`is_secret=True` fields have masked `after_value`). Consumers (SSE endpoint, TUI redraw) are free to read full resolved values for their own purposes via `resolve()`.

Change events are coalesced per `(field_path, seq)` — a caller that writes 10 times in 100ms produces 10 events, not 1. If coalescing becomes necessary for performance, it lives in the subscriber, not the resolver.

---

## Invariant tests (required for Phase 2)

1. `resolve` precedence — property test over all 2^5 layer-presence combinations.
2. `set` atomicity — concurrent writes from multiple threads; final state matches one of the writes, never a mix.
3. In-flight isolation — snapshot captured at request entry is stable across `resolve()` calls within that request's context even when `set()` occurs.
4. Secret masking — every field with `is_secret=True` produces masked values in `AuditLogEntry.before_value`/`after_value` and in `/api/config/{field_path}` responses; full value returned only to `resolve()` callers inside the proxy process.
5. Legacy alias resolution — for every registered `env_alias`, setting the legacy env var makes the modern `resolve()` path return the value.
6. Deprecation summary contents — summary emitted once and only once per process; every legacy var in use appears; no legacy var unused appears.

---

## Non-goals

- Multi-process / multi-node config sync — out of scope (plan Technical Context).
- Real-time validation of `${VAR}` references against current environment — validation happens at expansion time; a stale reference yields empty string with a warning log.
- Access control — enforced at the HTTP layer via `users_rbac.py`, not in the resolver. The resolver knows about `principal` only as an opaque tag passed through to `AuditLogEntry`.

---
description: "Task list for Model-Scan Integration"
---

# Tasks: Model-Scan Integration

**Input**: Design documents in `specs/003-model-scan-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included where they de-risk a contract or core logic; the project uses pytest.

**Organization**: Grouped by the design phases, tagged with the user story each advances. Two
spikes are front-loaded. `[P]` marks tasks that touch different files with no dependency.

## Format: `[ID] [P?] [Story] Description`

## Phase 0: Shared contract (Setup)

- [X] T001 [US1] Finalize `specs/003-model-scan-integration/contracts/routing_snapshot.schema.json`
  (already drafted) and add a validation test fixture under `tests/fixtures/snapshots/`.
- [X] T002 [P] [US1] Copy the snapshot schema into the model-scan repo at
  `model-scan/contracts/routing_snapshot.schema.json` (contract mirrored both sides).
- [X] T003 [P] [US3] Finalize `contracts/session_config.schema.json` (already drafted) and add a
  parse test fixture under `tests/fixtures/sessions/`.
- [X] T004 [US1] Document the `api_model` derivation rule (model-scan) and the base_url gap-fill
  rule (router) in `research.md`.

## Phase 1: Snapshot production and role coverage, model-scan (stories US1, US6)

- [X] T010 [US6] Per-role needs analysis for the five aux roles; add `R_title_gen`, `R_triage`,
  `R_kanban`, `R_profile_desc`, `R_curator` to `model-scan/slot_definitions.yaml`
  (`eval_mode: cost_basis`, gates per analysis).
- [X] T011 [US1] Implement `emit_snapshot(path)` projector in `model-scan/routing_snapshot.py`
  (project per-slot data to the snapshot schema, derive `api_model`, attach `price_blended`,
  `provider_health`, `blocklist`); atomic temp-file-plus-rename write.
- [X] T012 [US1] Add `--emit-snapshot[=PATH]` flag to `model-scan/dink.py`.
- [X] T013 [US1] Emit the snapshot from `model-scan/cron_manager.py` after each scan.
- [X] T014 [P] [US1] Add `GET /routing-snapshot` to `model-scan/gateway.py`.
- [X] T015 [US1] Test: emitted snapshot validates against the shared schema (model-scan harness).

## Phase 2: Snapshot consumption and binding, router (story US1)

- [X] T020 [US1] `src/services/models/model_scan_snapshot.py`: immutable `RoutingSnapshot` loader
  with `load(path)`, `from_gateway(url)`, schema validation, TTL and staleness, major-version
  refusal.
- [X] T021 [P] [US1] Tests for the loader (valid, truncated returns None, newer major rejected,
  TTL, staleness) in `tests/test_model_scan_snapshot.py`.
- [X] T022 [US1] `src/core/model_scan_binder.py`: `SelectionPolicy` (static, free, budget,
  quality, roles) with `parse` and `choose` (blocklist and gate filtering, primary excluded).
- [X] T023 [US1] Binder `bind(snapshot, policy, profile_bindings)` producing global tier
  assignments (default profile) plus a per-profile overlay map; provenance; atomic swap;
  writes the `AssignmentRegistry` and cascades.
- [X] T024 [P] [US1] Tests: cascade excludes blocklist and primary; empty candidates keep static;
  role absent keeps static; provenance correct.
- [X] T025 [US1] Add the `model_scan` section to `config/proxy_chain.json` (enabled, policy,
  snapshot_path, gateway_url, cache_ttl_s, staleness_limit_s) defaulting to disabled/static.
- [X] T026 [US1] Wire binding into `start_proxy.py` startup and the SIGHUP reload path
  (alongside `reload_router`).
- [X] T027 [US1] `POST /api/proxy/reload-models` in `src/api/endpoints.py` (re-read or pull,
  rebind, return assignments + provenance + staleness).

## Phase 3: Profile role bindings (stories US1, US3)

- [X] T030 [US1] Add `slot_bindings` support to `src/core/profiles.py` (global `default` plus
  per-profile overrides).
- [X] T031 [US1] Apply the binder overlay map in the `endpoints.py` profile overlay block
  (sibling to `tier_overrides`); request-time lookup only, no file IO.
- [X] T032 [P] [US6] Add the full fifteen-role `hermes` profile `slot_bindings` to
  `profiles/profiles.json`.

## Phase 4: Launcher, sessions, and chain lifecycle (stories US2, US3)

- [X] T040 [US3] Extend `src/api/routing_profiles_api.py` with `POST /api/routing-profiles`
  (register ephemeral, returns id + url_prefix) and `DELETE /api/routing-profiles/{id}`, backed
  by an in-memory ephemeral overlay store with a TTL sweep.
- [X] T041 [P] [US3] Tests: two ephemeral profiles route independently; delete is idempotent;
  TTL sweep reclaims orphans.
- [X] T042 [US2] `scripts/ccp-launch.sh` dispatcher: `ccp <tool>` with `--preset`, `--config`,
  `--role`, `--policy`, `--provider`, `--no-compress`, `--continue`; layered overlay composition;
  register and tear down ephemeral session profile; exec under rtk.
- [X] T043 [US2] `ccp up`: bring up the chain via `proxies up`; spawn a visible terminal
  (wezterm-aware) with tmux panes (headroom, proxy, clip); `--background` to detach.
- [X] T044 [US2] Extend `config/proxy_chain.json` chain entries: conditional CLIProxyAPIPlus
  (8317) entry, populated Headroom (8787) entry whose `service_cmd` also launches the local model.
- [X] T045 [P] [US2] Curate presets in `profiles/profiles.json`: claude, codex, hermes, pi, ante,
  opencode, antigravity (lane declared per preset).
- [X] T046 [US2] Extend `scripts/install-aliases.sh` to install `ccp`, add ante and antigravity
  aliases, preserve existing aliases, add optional policy and config.

## Phase 5: Lanes, quota ledger, and rotation (story US4)

- [X] T050 [US4] SPIKE: confirm the tokscale SQLite schema and confirm the router has no
  per-provider key pool today; record findings in `research.md`.
- [X] T051 [US4] `QuotaSource` adapter interface plus adapters: tokscale (primary, SQLite),
  ccusage (secondary, `--json`), and internal `usage_tracker`, `billing`, `rate_limiter`,
  `model_scan_quota`; normalize to `QuotaSample` and merge by provider with precedence/freshness.
- [X] T052 [US4] Add lanes to `src/core/model_scan_binder.py` and the `model_scan.lanes` config;
  presets declare a lane; `standby` never spends paid quota.
- [X] T053 [US4] Extend the snapshot with `provider_quota`; model-scan publishes merged quota and
  reset times (update `emit_snapshot`).
- [X] T054 [US4] `src/core/rotation.py`: quota-aware S-tier rotation for the interactive primary,
  free toolcalling, free floor (configurable preferred default), hysteresis and cooldown; reuse
  `rate_limiter` scores; live ledger decrement on usage and 429s.
- [X] T055 [US4] Per-provider key/account pool rotation (native rotate-on-429) in `src/core/client.py`
  and the provider registry.
- [X] T056 [P] [US4] Tests: free picks zero price; budget excludes over-ceiling and unknown price;
  rotation advances on drain and 429; free floor engages when paid drained; standby spends no paid
  quota; cooldown prevents flapping.

## Phase 6: Observability and the chain monitor (story US5)

- [X] T060 [US5] Stamp the session correlation id (ephemeral profile id) on every log line, metric,
  and error in `src/core/logging.py` and the request path.
- [X] T061 [US5] Unified error sink `~/.ccp/errors.jsonl` written by the proxy, launcher, and chain
  components via a shared emitter.
- [X] T062 [P] [US5] `ccp errors` subcommand: tail and filter by tool, provider, or session.
- [X] T063 [P] [US5] Dashboard panels: model source/provenance, compression ratios, error feed.

## Phase 7: Reliability feedback loop (story US6)

- [X] T070 [US6] Aggregate per-provider and per-model reliability (latency p95, error rate,
  rate-limit frequency) in the router and `POST /reliability` to model-scan on an interval.
- [X] T071 [US6] model-scan: accept `POST /reliability` and weight it into future scans and quota
  estimates.

## Polish and validation

- [X] T080 [P] Integration test: launch best-free with a fixture snapshot, verify bindings (US1).
- [X] T081 [P] Integration test: kill primary provider, verify cascade recovery (US1).
- [X] T082 [P] Integration test: two sessions of one tool, independent routing (US3).
- [X] T083 [P] Integration test: snapshot removed, static serving continues (US1).
- [X] T084 [P] Integration test: a dozen concurrent profiles during a rebind (US3, NFR-002).
- [X] T085 Regression: feature disabled or static policy is byte-for-byte baseline behavior (NFR-030).
- [X] T086 Update `CHANGELOG.md` and `docs/` for the new `ccp` launcher, policies, lanes, and
  the model-scan contract.

## Dependencies and parallelism

- Phase 0 precedes all. Phase 1 (model-scan) and Phase 2 (router) can proceed in parallel after
  the contract (T001 to T004) is fixed.
- Phase 3 depends on Phase 2 (binder). Phase 4 depends on Phase 3 (overlay) for sessions.
- Phase 5 depends on Phase 2 (binder) and the T050 spike. Phase 6 depends on Phase 4 (session id).
  Phase 7 depends on Phase 1 (gateway) and live traffic.
- `[P]` tasks within a phase touch distinct files and may run together.

## MVP boundary

US1 plus US2 (Phases 0 to 4 minimum for a single-session launch with measured binding and
cascade) is the first shippable increment. US3, US4, US5, US6 are independent follow-on
increments.

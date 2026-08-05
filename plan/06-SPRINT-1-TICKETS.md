---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, sprint-1, tickets, tasks, acceptance-tests, implementation]
---

# Sprint 1 Tickets

Concrete starting work, grounded in the real `claude-code-proxy` tree. Approach: extend, do not
rebuild. Each ticket has files to touch, steps, and a runnable acceptance test (AT). Order =
dependency order. Sizes: S < 0.5d, M ~ 1-2d, L ~ 3-5d.

Repo root for all paths: `/home/cheta/code/claude-code-proxy`.

## S1-01 [W0] Validate the config spine [S]
- Files: `tests/`, `specs/001-unified-config-system/tasks.md` (T062).
- Steps: run `pytest tests/`; triage failures; implement or formally waive the skipped T062
  in-flight snapshot-isolation test (mock provider).
- AT: `pytest tests/` green; T062 either passes or is documented as a known waiver with reason.
- Deps: none.

## S1-02 [W0] Prove the manifest parity path [S]
- Files: `src/core/config_manifest.py`.
- Steps: add one throwaway setting via the manifest; confirm it surfaces in `.env`, a CLI flag,
  the `--configure-advanced` TUI, and the web settings without per-surface code.
- AT: setting readable/writable from all 4 surfaces through `ConfigResolver`; CI grep (no stray
  `os.environ.get`) passes. Then revert the throwaway.
- Deps: S1-01.

## S1-03 [W1] Hardcoded-model audit (URGENT) [M]
- Files: `src/core/model_router.py`, `src/core/client.py`.
- Steps: per RECON-01, the only real spot is `model_router.py:170` name-prefix tool check; replace
  with `src/services/usage/model_limits.supports_tool_call(model)` (models.dev-backed registry
  already exists) + snapshot `has_tools`. Ensure an unknown/renamed model passes through and is
  logged, never 404s the request. (request_converter.py reasoning table = follow-up under W11.)
- AT: `grep -nE '"[a-z0-9-]+/[a-z0-9.:-]+"' src/core/model_router.py src/core/client.py` shows no
  routing-decision literals; a fixture request naming an unknown model returns a handled response
  (passthrough or explicit error), not a crash.
- Deps: S1-05 (snapshot available).

## S1-04 [W1] Dead-model exclusion / no 404-storm [M]
- Files: `src/core/circuit_breaker.py`, `src/core/client.py`, `tests/`.
- Steps: confirm cascade build excludes OPEN-breaker + blocklisted models; add a test simulating a
  free model returning repeated 404/500.
- AT: new test shows the failing model is skipped after `CB_FAILURE_THRESHOLD`, request completes
  via fallback, and each drop is logged with cause. No unbounded retry loop.
- Deps: none.

## S1-05 [W5] Vendor model-scan into the repo [M]
- Files: new `src/services/model_scan/` (or git submodule of `/home/cheta/code/model-scan`),
  `config/proxy_chain.json` (model_scan.snapshot_path).
- Steps: bring model-scan in as a package; keep the snapshot producer/consumer boundary (no
  scoring on hot path); point `snapshot_path` at the in-repo output.
- AT: `model-scan --emit-snapshot` writes the snapshot; `POST :8082/api/proxy/reload-models`
  loads it; `model_scan_binder` binds candidates into `AssignmentRegistry`.
- Deps: none.

## S1-06 [W4/F06] Quota-meter schema + 4 header adapters [M] (re-scoped, see RECON-02)
- Files: EXTEND `src/core/quota_sources.py` (do NOT make a new package; substrate exists there:
  QuotaSample, QuotaSource Protocol, merge_quota_samples, Tokscale/Ccusage/Static adapters).
  Add `ledger.py` reusing usage SQLite (`USAGE_TRACKING_DB_PATH`).
- Steps: generalize `QuotaSample` -> multi-dimensional `QuotaMeter` (per-window/per-model/unit per
  `04-DATA-CONTRACTS.md`); add 4 Tier-1 header-passthrough adapters implementing the existing
  `QuotaSource` Protocol; persistent ledger (counters survive restart); token-bucket per meter.
- AT: an internal `GET /api/quota/meters` returns live meters for the 4 providers with
  remaining/limit/reset; restart the proxy and counters persist; never reads JSONL token counts.
- Deps: S1-02 (config), S1-05 (provider registry).

## S1-07 [W4/F18] LP allocator dry-run [L]
- Files: new `src/services/allocator/` (`lp.py`, `profiles.py`, `report.py`).
- Steps: implement the allocator per `04-DATA-CONTRACTS.md` and `05-CONFIG-SCHEMA.md`: load
  snapshot (value=fitness) + meters (S1-06) + a fixture `session_profiles` set (3 Hermes + CC +
  5 Pi, 2 economy / 3 premium); solve the LP with PuLP; emit a dry-run `AllocationResult` +
  `shadow_prices` to a file/endpoint. NO enforcement yet.
- AT: for the fixture fleet, output gives each role a primary + diversity-capped cascade honoring
  every meter; satisficing roles (aux, pi-economy primary) receive free/abundant models while
  scarce smart models go to maximizing roles; a shadow-price report names the binding meter.
- Deps: S1-05, S1-06.

## S1-08 [W4] Wire allocator output into the snapshot [M]
- Files: `src/services/allocator/`, `src/core/` (binder consumption).
- Steps: map `AllocationResult` onto the augmented snapshot shape the `model_scan_binder` already
  loads (best=primary, candidates=cascade), as a post-processor of the model-scan snapshot.
- AT: with the allocator enabled, routing for two different session profiles resolves the same
  tier to different models per the allocation; with it disabled, behavior is unchanged (baseline).
- Deps: S1-07.

## Sprint-1 definition of done
- Tests green; config parity path proven; routing fully snapshot-driven with zero hardcoded model
  ids; dead models excluded (no 404-storm) with logged cause; model-scan vendored; quota meters
  live for 4 providers with persistent ledger; allocator produces a verifiable dry-run allocation
  + shadow-price report for the real fleet; allocator output optionally drives routing, off by
  default (baseline preserved).
- Guardrails (all tickets): no hardcoded model ids; free-only default; 4-surface parity via
  manifest; secrets env-only; never modify ANTHROPIC_API_KEY=pass / x-api-key:pass / loading order.

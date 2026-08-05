# File Organization Log — July 2026 Audit

This log tracks the relocation of non-functional files (markdown files, unused scripts, obsolete tests) inside `claude-code-proxy` for cleanup and auditing.

## Reorganization Summary Table

| Original File Location | New Archived Location | Category / Purpose | Status / Classification | Date Sourced |
|------------------------|-----------------------|--------------------|-------------------------|--------------|
| `litellm-gateway.yaml` | `archive/trash/litellm-gateway.yaml` | Trash / Obsolete LiteLLM configuration | **Obsolete / Trash** (LiteLLM rejected) | 2026-04-18 |
| `compress-monitor-web.py` | `archive/scripts/compress-monitor-web.py` | Standalone Python Web monitor for Headroom + RTK | **Useful Utility** (Standalone monitor) | 2026-05-19 |
| `cs-dashboard.py` | `archive/scripts/cs-dashboard.py` | Standalone CLI dashboard for compression stack | **Useful Utility** (Standalone dashboard) | 2026-05-19 |
| `extract_prompts.py` | `archive/scripts/extract_prompts.py` | Standalone tool to extract user prompts from logs | **Useful Utility** (Standalone tool) | 2026-06-01 |
| `hermes-verify` | `archive/scripts/hermes-verify` | Standalone preflight health probe wrapper for Hermes | **Useful Utility** (Hermes verification helper) | 2026-04-18 |
| `tests/2026-03-19-live-run/run_concurrent_claude.py` | `archive/tests/run_concurrent_claude.py` | Historical live-run concurrency test script | **Obsolete Test** (Historical artifact) | 2026-03-19 |
| `tests/legacy/test_startup.sh` | `archive/tests/test_startup.sh` | Legacy startup validation test script | **Obsolete Test** (Legacy script) | Legacy |
| `tests/integration/debug_vibeproxy.py` | `archive/tests/debug_vibeproxy.py` | Non-standard diagnostic stress test for VibeProxy auth | **Diagnostic Script** (Manual test helper) | 2026-04-18 |
| `tests/integration/run_simple.py` | `archive/tests/run_simple.py` | Non-standard basic proxy sanity check script | **Diagnostic Script** (Manual test helper) | 2026-04-18 |
| `tests/integration/quick_headless_test.py` | `archive/tests/quick_headless_test.py` | Non-standard headless execution test script | **Diagnostic Script** (Manual test helper) | 2026-04-18 |
| `tests/integration/run_tier_tests.py` | `archive/tests/run_tier_tests.py` | Non-standard model tier routing validation script | **Diagnostic Script** (Manual test helper) | 2026-04-18 |
| `tests/integration/skill_test_runner.py` | `archive/tests/skill_test_runner.py` | Non-standard skill execution tester script | **Diagnostic Script** (Manual test helper) | 2026-04-18 |
| `plans/design.md` | `archive/plans_unimplemented/design.md` | Design spec for Bun/Svelte/Ink rewrite | **Unimplemented Plan** (Bun-based v2 plan) | 2026-05-14 |
| `plans/requirements.md` | `archive/plans_unimplemented/requirements.md` | Requirements spec for Bun/Svelte/Ink rewrite | **Unimplemented Plan** (Bun-based v2 plan) | 2026-05-14 |
| `plans/future-plans.md` | `archive/plans_unimplemented/future-plans.md` | List of deferred/rejected items for Bun rewrite | **Unimplemented Plan** (Bun-based v2 plan) | 2026-05-14 |
| `plans/model-scan-integration-plan.md` | `archive/plans_implemented/model-scan-integration-plan.md` | Integration plan for model-scan snapshot routing | **Implemented Plan** (Model-scan Phase 1) | 2026-05-30 |
| `plans/observability-overhaul-plan.md` | `archive/plans_partially_implemented/observability-overhaul-plan.md` | Plan for deep logging, Prometheus metrics, and UI | **Partially Implemented** (UI Svelte dashboards mocked) | 2026-05-19 |
| `docs/guides/crosstalk-proposal.md` | `archive/proposals_unimplemented/crosstalk-proposal.md` | Detailed proposal for Crosstalk V2 agent patterns | **Unimplemented Proposal** (Crosstalk V2) | 2026-04-18 |
| `docs/guides/crosstalk-quick-ref.md` | `archive/proposals_unimplemented/crosstalk-quick-ref.md` | Quick reference for Crosstalk V2 topologies | **Unimplemented Proposal** (Crosstalk V2) | 2026-04-18 |
| `docs/proposals/free-model-cascade-design.md` | `archive/proposals_implemented/free-model-cascade-design.md` | Design document for free model cascade routing | **Implemented Proposal** (Free Cascade) | 2026-04-18 |
| `docs/proposals/free-model-cascade-prd.md` | `archive/proposals_implemented/free-model-cascade-prd.md` | PRD for free model cascade and quota tracking | **Implemented Proposal** (Free Cascade) | 2026-04-18 |
| `docs/proposals/free-model-cascade-tasks.md` | `archive/proposals_implemented/free-model-cascade-tasks.md` | Implementation task list for free model cascade | **Implemented Proposal** (Free Cascade) | 2026-04-18 |
| `docs/LOGGING_AUDIT_PROPOSAL.md` | `archive/proposals_partially_implemented/LOGGING_AUDIT_PROPOSAL.md` | Audit of logging levels and DB request tracking | **Partially Implemented** (DB tracking done, lean tool schema deferred) | 2026-05-19 |
| `docs/superpowers/specs/2026-05-19-dashboard-overhaul-design.md` | `archive/proposals_partially_implemented/2026-05-19-dashboard-overhaul-design.md` | Design spec for dashboard overhaul (metrics & charts) | **Partially Implemented** (Aggregate API done, charts mocked) | 2026-05-19 |
| `docs/research/infrastructure-of-agency.md` | `archive/research/infrastructure-of-agency.md` | Research paper analyzing agent management ecosystems | **Research Artifact** (Whitepaper) | 2026-04-03 |
| `docs/research/synthetic-cortex.md` | `archive/research/IDEA - synthetic-cortex.md` | Master proposal for Fractal Council/Synthetic Cortex | **Research Artifact** (Living Document spec) | 2026-04-03 |
| `docs/guides/adversarial_report_v2.md` | `archive/history/adversarial_report_v2.md` | Adversarial audit report from past cleanup | **Historical Record** (Audit report) | 2026-05-14 |
| `docs/guides/cleanup_prompt.md` | `archive/history/cleanup_prompt.md` | Past prompt instruction used for codebase cleanup | **Historical Record** (Utility prompt) | 2026-05-14 |
| `docs/guides/final_adversarial_report.md` | `archive/history/final_adversarial_report.md` | Concluding audit report from past cleanup session | **Historical Record** (Audit report) | 2026-05-14 |
| `.remember/archive.md` | `archive/history/remember/archive.md` | Past session logs and context records | **Historical Record** (Session logging) | 2026-04-30 |
| `.remember/now.md` | `archive/history/remember/now.md` | Past session logs and context records | **Historical Record** (Session logging) | 2026-06-19 |
| `.remember/recent.md` | `archive/history/remember/recent.md` | Past session logs and context records | **Historical Record** (Session logging) | 2026-06-19 |
| `.remember/remember.md` | `archive/history/remember/remember.md` | Past session logs and context records | **Historical Record** (Session logging) | 2026-06-19 |
| `.remember/today-*.md` | `archive/history/remember/today-*.md` | Past session logs and context records (multiple files) | **Historical Record** (Session logging) | April-June 2026 |
| `audit-reports/hardcoded-model-names-audit.md` | `archive/history/audit_reports/hardcoded-model-names-audit.md` | Audit of hardcoded model names | **Audit Report** | 2026-07-04 |
| `audit-reports/proxy-gateway-maudit-2026-07-04.md` | `archive/history/audit_reports/proxy-gateway-maudit-2026-07-04.md` | Proxy gateway manual audit report | **Audit Report** | 2026-07-04 |
| `audit-reports/saas-transformation-report.md` | `archive/history/audit_reports/saas-transformation-report.md` | SaaS transformation gap analysis report | **Audit Report** | 2026-07-04 |
| `booger/*` | `archive/history/booger/*` | Standalone workspace indices, inventory logs, and scratch lists | **Historical Record / Scrap** | Legacy |
| `SNAKESKIN/*` | `archive/history/snakeskin/*` | Audit logs and troubleshooting docs from SNAKESKIN phase | **Historical Record / Troubleshooting** | Nov 2025 - Feb 2026 |
| `config/proxy_chain.bak.2026-04-24-111912` | `archive/trash/proxy_chain.bak.2026-04-24-111912` | Backup of proxy chain configuration | **Obsolete Config Backup** | 2026-04-24 |
| `tests/integration/ranking_alignment_report.json` | `archive/trash/ranking_alignment_report.json` | Report of ranking alignment validation test run | **Obsolete Test Artifact** | 2026-07-10 |
| `tests/integration/test_results.txt` | `archive/trash/test_results.txt` | Temporary debug log file from test execution | **Obsolete Test Log** | Legacy |
| `tests/integration/empty_chain.bak.*` (multiple files) | `archive/trash/empty_chain.bak.*` | Backups of empty chain configuration templates from test suite | **Obsolete Test Backups** | 2026-05-14 |
| `src/services/openrouter_model_scout/main.py.tmp` | `archive/trash/openrouter_model_scout_main.py.tmp` | Temporary debug script leftover | **Temporary Debug File** | 2026-03-24 |
| `model-scraper/src/openrouter_model_scout/main.py.tmp` | `archive/trash/model-scraper_openrouter_model_scout_main.py.tmp` | Temporary debug script leftover | **Temporary Debug File** | 2026-03-06 |

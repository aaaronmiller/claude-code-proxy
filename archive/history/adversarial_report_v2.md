# Adversarial Report v2: Deep Audit of Current State

## 1. The "Junk Drawer" Problem (`src/utils`)
**Critique:** `src/utils` contains 18 files with mixed concerns.
- **Logging:** `compact_logger.py`, `request_logger.py`, `startup_display.py` -> Should be `src/core/logging/` or `src/services/logging/`.
- **Cost/Usage:** `cost_calculator.py`, `usage_tracker.py`, `model_limits.py` -> Should be `src/services/billing/` or `src/services/usage/`.
- **Prompting:** `prompt_injector.py`, `system_prompt_loader.py`, `templates.py` -> Should be `src/services/prompts/`.
- **Models:** `model_filter.py`, `model_parser.py`, `provider_detector.py` -> Should be `src/services/models/`.

**Verdict:** `src/utils` is a dumping ground. It violates the "Service Layer" architecture.

## 2. Redundancy in Entry Points
**Critique:** `src/main.py` is the FastAPI app definition, but it contains logic that might overlap with `start_proxy.py` (like static file mounting logic).
- **Observation:** `src/main.py` has comments about "redundant blocks".
- **Action:** Clean up `src/main.py` to be purely the App Factory.

## 3. CLI Organization
**Critique:** `src/cli` is flat.
- **Observation:** It's mostly fine, but `wizard.py` is huge (31KB).
- **Action:** Consider splitting `wizard.py` if it grows, but acceptable for now.

## 4. Missing "Service" Abstractions
**Critique:** The code relies on "Managers" and "Trackers" instantiated globally or in modules.
- **Action:** Ensure dependency injection or clear singleton patterns in `src/core/container.py` (if we were being very strict), but for now, just grouping them into `src/services/` is a huge win.

## Plan for Phase 3 (Execution)
1.  **Explode `src/utils`**: Move files to their semantic homes.
2.  **Refine `src/main.py`**: Remove dead comments.
3.  **Update Imports**: This will be the hardest part. Every move breaks imports.

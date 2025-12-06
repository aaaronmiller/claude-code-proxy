# Task-Focused Repository Cleanup Prompt

Use this prompt to instruct an AI assistant to clean up a cluttered repository based on *purpose* and *utility*, rather than just file types.

---

# Task-Focused Repository Cleanup Prompt

Use this prompt to instruct an AI assistant to transform a cluttered repository into a professional, production-ready project in a single, comprehensive pass.

---

**Prompt:**

> I need you to perform a **"Deep Repository Professionalization"** of this project.
>
> **The Goal:**
> Transform this repository from a collection of scripts into a **Unified, Production-Ready Application**. The end result should be a clean root, a single entry point, and a logical service-oriented architecture.
>
> **The Philosophy:**
> - **Architecture over Organization:** Don't just move files; architect them. Separate *Interface* (CLI/API) from *Implementation* (Services).
> - **Unified Experience:** The user should interact with ONE entry point (e.g., `start_proxy.py` or `main.py`) that exposes all functionality via subcommands.
> - **Safety First:** Preserve secrets, permissions, and build contexts.
>
> **Execution Plan: The Phased Adversarial Protocol**
>
> **Phase 1: Audit & Architect (The Architect & Security Engineer)**
> 1.  **Audit:** Scan `src/utils`, `src/core`, and root. Identify "Junk Drawers".
> 2.  **Architect:** Define the Service Layer. (e.g., `src/services/billing`, `src/services/prompts`).
> 3.  **Security Check:** Identify secrets, permissions, and build contexts that must be preserved.
> 4.  **Stop & Review:** Critique your own plan. "Is this architecture sustainable?"
>
> **Phase 2: The Deep Clean (The Refactorer)**
> 1.  **Explode Junk Drawers:** Move files from `src/utils` to `src/services/<domain>`.
> 2.  **Consolidate:** Merge redundant scripts into the CLI.
> 3.  **Refactor:** Clean up `main.py` and entry points.
>
> **Phase 3: Verification (The QA & DevOps Engineer)**
> 1.  **Fix Imports:** Aggressively update all imports.
> 2.  **Test:** Run `python start_proxy.py --help` and `--validate-config`.
> 3.  **Build Check:** Verify Dockerfiles still build (or at least paths are correct).
>
> **Phase 4: Documentation (The Product Manager)**
> 1.  **Rewrite Docs:** Update `README.md` with the new structure.
> 2.  **Final Adversarial Check:** "If I were a new user, would this make sense?"
>
> **Deliverable:**
> -   A repository that passes the "Adversarial Check".
> -   Zero "Junk Drawers".
> -   A unified, verified CLI.
>
> **Deliverable:**
> -   A fully refactored codebase.
> -   A working, unified CLI.
> -   A verified, import-error-free state.
>
> Please proceed with this plan. Start by auditing the current structure.

# Adversarial Validation: Task-Focused Cleanup Prompt

We convened a panel of 8 simulated experts to critique the original "Task-Focused Cleanup Prompt". Here are their findings and the resulting improvements.

## The Panel

1.  **🏗️ The Architect** (System Design)
2.  **🚀 The DevOps Engineer** (Deployment & Operations)
3.  **🛡️ The Security Engineer** (Safety & Permissions)
4.  **🧪 The QA Engineer** (Testing & Verification)
5.  **✨ The DX Expert** (Developer Experience)
6.  **📝 The Tech Writer** (Documentation)
7.  **💼 The Product Manager** (Value & Usability)
8.  **😈 The Chaos Monkey** (Edge Cases & Failure Modes)

---

## Critique of Original Prompt

### 1. 🏗️ The Architect
> "The prompt asks to 'categorize and move', but it doesn't explicitly mandate a **Service Layer**. It risks just dumping everything into `utils/` or `lib/`. It needs to enforce a separation between *Interface* (CLI/API) and *Implementation* (Services)."

### 2. 🚀 The DevOps Engineer
> "It mentions `deploy/`, but what about **CI/CD**? `.github/`, `.gitlab-ci.yml`? Also, moving `Dockerfile` can break build contexts if you don't update the build command. The prompt needs to warn about *Build Context*."

### 3. 🛡️ The Security Engineer
> "Moving files is dangerous. What if a file has specific **permissions** (chmod +x)? What if `.env` files are moved and suddenly exposed? The prompt must explicitly protect secrets and permissions."

### 4. 🧪 The QA Engineer
> "The prompt says 'Fix imports', but it doesn't say **'Run Tests'**. A refactor without a test run is a hallucination. It needs a mandatory Verification step using the project's own test suite."

### 5. ✨ The DX Expert
> "Consolidating scripts is good, but if you merge 5 scripts into one `main.py` without a clear **Help Menu** or **Subcommands**, you've made it harder to use. It needs to mandate a *Self-Documenting CLI* (like `argparse` or `click`)."

### 6. 📝 The Tech Writer
> "Updating the `README` is mentioned, but it needs to be more aggressive. It should ask to **'Rewrite the Quick Start'** entirely, not just 'update'. The old instructions will be 100% wrong."

### 7. 💼 The Product Manager
> "Does this actually help the user? The prompt focuses on 'cleaning', but the goal is **'Professionalization'**. It should frame the task as 'Preparing for Production', not just 'Janitorial Work'."

### 8. 😈 The Chaos Monkey
> "What if `src/` doesn't exist? What if there are name collisions? What if the repo is a monorepo? The prompt assumes a standard Python layout. It needs a **'Pre-Flight Check'** to assess the repo type first."

---

## Verdict: "Good, but not Autonomous"

The original prompt would likely result in a cleaner file structure but might leave the project in a broken state (broken builds, confusing CLI, missing tests). To be truly "One-Shot", it needs to be more prescriptive about **Architecture**, **Verification**, and **Usability**.

## Refinement Strategy

We will upgrade the prompt to:
1.  **Enforce Architecture:** Explicitly define `src/cli`, `src/services`, `src/core`.
2.  **Mandate Verification:** Require running `--help` and tests.
3.  **Protect Ops:** Handle Docker contexts and secrets.
4.  **Elevate DX:** Require a unified CLI with subcommands.

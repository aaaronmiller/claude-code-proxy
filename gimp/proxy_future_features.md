# Claude Code Proxy - Future Features & Roadmap

These items were either explicitly requested by the user in sessions or identified as critical missing gaps during the audit.

## 1. Proxy Chain Configuration TUI (High Priority)
- **Description**: A visual Terminal User Interface (similar to BIOS boot order) to manage the proxy stack.
- **Specifics**:
  - Show existing chain: `[1] Headroom, [2] RTK, [3] Proxy`.
  - Allow users to select a number to edit an endpoint.
  - Arrow keys to reorder (move a proxy up or down in the chain).
  - Add/Remove new proxies dynamically.
- **Tech Goal**: Implement using Python `textual` or similar library.

## 2. Web UI Setup & Dashboard Facelift
- **Description**: The current web UI is "totally broken" or lacks feature parity with the TUI.
- **Specifics**:
  - **Setup Wizard**: Web-based interface to set `.env` variables and proxy chain order.
  - **Analytics Pro**: Color-coded graphs for tokens/s, cost, and compression efficiency.
  - **Theme Support**: Integrate 3 distinct themes with micro-animations.
  - **Nano Banana Assets**: Use procedurally generated or placeholder images as requested in `USERPROMPTS.md` (Prompt 7).

## 3. Dynamic Model Substitution Controls
- **Description**: Allow the user to toggle "task-based" substitutions on or off via the `proxies` command or the TUI.
- **Specifics**:
  - Useful for Anthropic Pro subscribers who want to "pass through" their requests without the proxy intervening in model selection.
  - Support for `CUSTOM_ROUTER_PATH`: A way for users to provide a script (Python or JS) that defines custom routing logic.

## 4. Enhanced Status Bar Builder
- **Description**: A TUI feature (erroneously named "prompt injection" in early sessions) to customize the Claude Code status bar.
- **Specifics**:
  - Real-time preview of the status bar as the user adds/removes metrics.
  - Support for left and right alignment to prevent "jitter" when model names change length.
  - Metrics to include: `tokens/s`, `compression %`, `active_proxy_health`, and `last_error_code`.

## 5. Universal Mounting Script (`macdrive`)
- **Description**: Enhance the script in `/code/scripts` to auto-mount any external drive in WSL2 regardless of partition type (APFS, NTFS, etc.).
- **Specifics**: Hands-free operation when a drive is connected.

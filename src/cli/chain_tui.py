"""
Proxy Chain TUI — manage the ordered list of upstream proxies and per-use-case
model routing from a terminal UI.

Usage:
    python -m src.cli.chain_tui

Keybindings (chain list):
    ↑ / ↓       Navigate entries
    Enter       Select / de-select entry for reordering
    W / S       Move selected entry up / down  (while selected)
    A           Add new proxy entry
    D           Delete selected entry
    E           Edit selected entry
    T           Toggle enabled/disabled
    R           Restart services for selected entry
    Tab         Switch between Chain and Router panels
    Q / Ctrl+C  Quit (auto-saves on exit)
"""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import fields
from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Pretty,
    Rule,
    Static,
    Switch,
)

from src.core.proxy_chain import ProxyChain, ProxyEntry, RouterConfig

# ─────────────────────────────────────────────────────────────────────────────
# Helper: status badge
# ─────────────────────────────────────────────────────────────────────────────

def _badge(entry: ProxyEntry) -> str:
    if not entry.enabled:
        return "[dim]DISABLED[/dim]"
    if entry.type == "cli_wrapper":
        return "[cyan]CLI[/cyan]"
    return "[green]HTTP[/green]"


# ─────────────────────────────────────────────────────────────────────────────
# Edit-entry modal
# ─────────────────────────────────────────────────────────────────────────────

class EntryEditScreen(ModalScreen):
    """Full-screen form to create or edit a ProxyEntry."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, entry: Optional[ProxyEntry] = None, **kwargs):
        super().__init__(**kwargs)
        self._entry = entry or ProxyEntry(
            id="new-proxy",
            name="New Proxy",
            url="http://127.0.0.1:8888/v1",
        )

    def compose(self) -> ComposeResult:
        e = self._entry
        with Vertical(id="edit-form"):
            yield Label("Edit Proxy Entry", id="form-title")
            yield Rule()
            yield Label("ID (slug, no spaces)")
            yield Input(e.id, id="f-id", placeholder="headroom")
            yield Label("Name (display)")
            yield Input(e.name, id="f-name", placeholder="My Proxy")
            yield Label("URL  (leave blank for CLI wrapper)")
            yield Input(e.url, id="f-url", placeholder="http://127.0.0.1:8787/v1")
            yield Label("Auth key  (blank = inherit OPENROUTER_API_KEY from env)")
            yield Input(e.auth_key or "", id="f-auth", placeholder="${OPENROUTER_API_KEY}")
            yield Label("Service start command  (blank = not managed here)")
            yield Input(e.service_cmd or "", id="f-cmd", placeholder="headroom proxy --port 8787")
            yield Label("Port  (for health-check display, 0 = not applicable)")
            yield Input(str(e.port), id="f-port", placeholder="8787")
            yield Label("Health path")
            yield Input(e.health_path, id="f-health", placeholder="/health")
            yield Label("Timeout (seconds)")
            yield Input(str(e.timeout), id="f-timeout", placeholder="90")
            yield Rule()
            with Horizontal(id="form-buttons"):
                yield Button("Save  [Ctrl+S]", variant="primary", id="btn-save")
                yield Button("Cancel  [Esc]", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def action_save(self) -> None:
        try:
            port = int(self.query_one("#f-port", Input).value or "0")
        except ValueError:
            port = 0
        try:
            timeout = int(self.query_one("#f-timeout", Input).value or "90")
        except ValueError:
            timeout = 90

        url = self.query_one("#f-url", Input).value.strip()
        updated = ProxyEntry(
            id=self.query_one("#f-id", Input).value.strip() or self._entry.id,
            name=self.query_one("#f-name", Input).value.strip() or self._entry.name,
            url=url,
            auth_key=self.query_one("#f-auth", Input).value.strip(),
            enabled=self._entry.enabled,
            order=self._entry.order,
            service_cmd=self.query_one("#f-cmd", Input).value.strip(),
            port=port,
            health_path=self.query_one("#f-health", Input).value.strip() or "/health",
            timeout=timeout,
            type="http" if url else "cli_wrapper",
        )
        self.dismiss(updated)

    @on(Button.Pressed, "#btn-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)


# ─────────────────────────────────────────────────────────────────────────────
# Router-config panel (inline, shown in right pane)
# ─────────────────────────────────────────────────────────────────────────────

class RouterPanel(Container):
    """Editable panel for RouterConfig fields."""

    DEFAULT_CSS = """
    RouterPanel {
        padding: 1 2;
        border: round $accent;
        height: auto;
    }
    RouterPanel Label { margin-top: 1; }
    RouterPanel Input { margin-bottom: 0; }
    """

    def __init__(self, rc: RouterConfig, **kwargs):
        super().__init__(**kwargs)
        self._rc = rc

    def compose(self) -> ComposeResult:
        rc = self._rc
        yield Label("[bold]Model Router[/bold]")
        yield Rule()
        yield Label("Default  (general tasks, blank = BIG_MODEL)")
        yield Input(rc.default, id="r-default", placeholder="")
        yield Label("Background  (lightweight background tasks)")
        yield Input(rc.background, id="r-background", placeholder="stepfun/step-3.5-flash:free")
        yield Label("Think  (reasoning / Plan Mode)")
        yield Input(rc.think, id="r-think", placeholder="")
        yield Label("Long-context model")
        yield Input(rc.long_context, id="r-long-context", placeholder="minimax/minimax-m2.5:free")
        yield Label("Long-context threshold (tokens)")
        yield Input(str(rc.long_context_threshold), id="r-threshold", placeholder="60000")
        yield Label("Web search model  (add :online suffix for OpenRouter)")
        yield Input(rc.web_search, id="r-web-search", placeholder="")
        yield Label("Image model  (vision-capable)")
        yield Input(rc.image, id="r-image", placeholder="qwen/qwen2.5-vl-72b-instruct")
        yield Label("Custom router path  (.py or .js)")
        yield Input(rc.custom_router_path, id="r-custom-path", placeholder="config/custom_router.py")

    def collect(self) -> RouterConfig:
        """Read current field values into a RouterConfig."""
        try:
            threshold = int(self.query_one("#r-threshold", Input).value or "60000")
        except ValueError:
            threshold = 60000
        return RouterConfig(
            default=self.query_one("#r-default", Input).value.strip(),
            background=self.query_one("#r-background", Input).value.strip(),
            think=self.query_one("#r-think", Input).value.strip(),
            long_context=self.query_one("#r-long-context", Input).value.strip(),
            long_context_threshold=threshold,
            web_search=self.query_one("#r-web-search", Input).value.strip(),
            image=self.query_one("#r-image", Input).value.strip(),
            custom_router_path=self.query_one("#r-custom-path", Input).value.strip(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main app
# ─────────────────────────────────────────────────────────────────────────────

class ChainTUI(App):
    """Proxy chain management TUI."""

    TITLE = "Claude Code Proxy — Chain Manager"
    SUB_TITLE = "Tab = switch panel · Q = quit & save"

    CSS = """
    Screen {
        layout: horizontal;
    }
    #left-panel {
        width: 55%;
        border: round $primary;
        padding: 0 1;
    }
    #right-panel {
        width: 45%;
        padding: 0 1;
    }
    #chain-table {
        height: 1fr;
    }
    #toolbar {
        height: 3;
        align: center middle;
        padding: 0 1;
    }
    #status-bar {
        height: 1;
        background: $boost;
        padding: 0 1;
        color: $text-muted;
    }
    Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit_save", "Quit & Save"),
        Binding("ctrl+c", "quit_save", "Quit & Save", show=False),
        Binding("a", "add_entry", "Add"),
        Binding("d", "delete_entry", "Delete"),
        Binding("e", "edit_entry", "Edit"),
        Binding("t", "toggle_entry", "Toggle"),
        Binding("w", "move_up", "Move Up"),
        Binding("s", "move_down", "Move Down"),
        Binding("r", "restart_service", "Restart svc"),
        Binding("tab", "focus_next", "Next Panel", show=False),
    ]

    _selected_row: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chain = ProxyChain.load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Label("[bold]Proxy Chain[/bold]  (W/S = reorder · E = edit · T = toggle)")
                yield Rule()
                yield DataTable(id="chain-table", zebra_stripes=True, cursor_type="row")
                yield Rule()
                with Horizontal(id="toolbar"):
                    yield Button("Add [A]", id="btn-add", variant="success")
                    yield Button("Delete [D]", id="btn-del", variant="error")
                    yield Button("Edit [E]", id="btn-edit")
                    yield Button("Toggle [T]", id="btn-toggle")
                    yield Button("↑ [W]", id="btn-up")
                    yield Button("↓ [S]", id="btn-down")
                yield Static("", id="status-bar")
            with ScrollableContainer(id="right-panel"):
                yield RouterPanel(self._chain.router, id="router-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_table()
        self.query_one("#chain-table", DataTable).focus()

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        table = self.query_one("#chain-table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Name", "Type", "URL / Mode", "Status")
        for i, e in enumerate(self._chain.entries):
            url_display = e.display_url[:38] + "…" if len(e.display_url) > 40 else e.display_url
            table.add_row(
                str(i + 1),
                e.name,
                e.type,
                url_display,
                _badge(e),
            )
        if self._chain.entries:
            row = min(self._selected_row, len(self._chain.entries) - 1)
            table.move_cursor(row=row)

    def _current_idx(self) -> int:
        table = self.query_one("#chain-table", DataTable)
        return table.cursor_row

    def _set_status(self, msg: str) -> None:
        self.query_one("#status-bar", Static).update(msg)

    # ── Chain actions ─────────────────────────────────────────────────────────

    def action_add_entry(self) -> None:
        def _on_result(entry: Optional[ProxyEntry]) -> None:
            if entry:
                self._chain.add(entry)
                self._selected_row = len(self._chain.entries) - 1
                self._refresh_table()
                self._set_status(f"Added: {entry.name}")

        self.push_screen(EntryEditScreen(), _on_result)

    def action_edit_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        entry = self._chain.entries[idx]

        def _on_result(updated: Optional[ProxyEntry]) -> None:
            if updated:
                updated.order = entry.order
                updated.enabled = entry.enabled
                self._chain.entries[idx] = updated
                self._chain._renumber()
                self._refresh_table()
                self._set_status(f"Updated: {updated.name}")

        self.push_screen(EntryEditScreen(entry), _on_result)

    def action_delete_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        name = self._chain.entries[idx].name
        self._chain.remove(idx)
        self._selected_row = max(0, idx - 1)
        self._refresh_table()
        self._set_status(f"Deleted: {name}")

    def action_toggle_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        e = self._chain.entries[idx]
        e.enabled = not e.enabled
        self._refresh_table()
        state = "enabled" if e.enabled else "disabled"
        self._set_status(f"{e.name}: {state}")

    def action_move_up(self) -> None:
        idx = self._current_idx()
        if idx > 0:
            self._chain.move_up(idx)
            self._selected_row = idx - 1
            self._refresh_table()

    def action_move_down(self) -> None:
        idx = self._current_idx()
        if idx < len(self._chain.entries) - 1:
            self._chain.move_down(idx)
            self._selected_row = idx + 1
            self._refresh_table()

    def action_restart_service(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        e = self._chain.entries[idx]
        if not e.service_cmd:
            self._set_status(f"{e.name}: no service_cmd configured")
            return
        try:
            subprocess.Popen(
                e.service_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._set_status(f"Restarted: {e.name}")
        except Exception as ex:
            self._set_status(f"Error restarting {e.name}: {ex}")

    # ── Button bindings ───────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-add")
    def _btn_add(self) -> None:
        self.action_add_entry()

    @on(Button.Pressed, "#btn-del")
    def _btn_del(self) -> None:
        self.action_delete_entry()

    @on(Button.Pressed, "#btn-edit")
    def _btn_edit(self) -> None:
        self.action_edit_entry()

    @on(Button.Pressed, "#btn-toggle")
    def _btn_toggle(self) -> None:
        self.action_toggle_entry()

    @on(Button.Pressed, "#btn-up")
    def _btn_up(self) -> None:
        self.action_move_up()

    @on(Button.Pressed, "#btn-down")
    def _btn_down(self) -> None:
        self.action_move_down()

    # ── Save & quit ───────────────────────────────────────────────────────────

    def action_quit_save(self) -> None:
        # Collect router config from panel
        try:
            router_panel = self.query_one("#router-panel", RouterPanel)
            self._chain.router = router_panel.collect()
        except Exception:
            pass
        self._chain.save()
        # Reload singleton so the running proxy picks up changes without restart
        try:
            from src.core.proxy_chain import reload_chain
            from src.core.model_router import reload_router
            reload_chain()
            reload_router()
        except Exception:
            pass
        self.exit()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    ChainTUI().run()


if __name__ == "__main__":
    main()

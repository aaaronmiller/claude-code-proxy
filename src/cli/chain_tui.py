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
import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import fields
from pathlib import Path
from typing import Any, Optional

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
from src.cli.assignment_tui import AssignmentPanel
from src.cli.identifier_mapping_tui import IdentifierMappingPanel

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Chain API client (talks to running proxy on 127.0.0.1:8082)
# ─────────────────────────────────────────────────────────────────────────────


class ChainAPI:
    """Thin wrapper around the chain management HTTP API."""

    BASE = "http://127.0.0.1:8082"

    @classmethod
    def _request(
        cls, method: str, path: str, *, json: dict | None = None, expected: int
    ) -> Any:
        url = f"{cls.BASE}{path}"
        data = json.dumps(json).encode() if json is not None else None
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method=method
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status != expected:
                    raise RuntimeError(f"HTTP {resp.status}: {resp.read().decode()}")
                return json.loads(resp.read()) if resp.read() else None
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from e
        except Exception as e:
            raise RuntimeError(f"API error: {e}") from e

    @classmethod
    def list_chain(cls) -> list[dict]:
        return cls._request("GET", "/api/chain", expected=200) or []

    @classmethod
    def create(cls, payload: dict) -> dict:
        return cls._request("POST", "/api/chain", json=payload, expected=201)

    @classmethod
    def update(cls, entry_id: str, payload: dict) -> dict:
        return cls._request(
            "PATCH", f"/api/chain/{entry_id}", json=payload, expected=200
        )

    @classmethod
    def delete(cls, entry_id: str) -> None:
        cls._request("DELETE", f"/api/chain/{entry_id}", expected=204)

    @classmethod
    def reorder(cls, order: list[str]) -> None:
        cls._request("POST", "/api/chain/reorder", json={"order": order}, expected=200)


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
            yield Input(
                e.auth_key or "", id="f-auth", placeholder="${OPENROUTER_API_KEY}"
            )
            yield Label("Service start command  (blank = not managed here)")
            yield Input(
                e.service_cmd or "",
                id="f-cmd",
                placeholder="headroom proxy --port 8787",
            )
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
        yield Input(
            rc.background,
            id="r-background",
            placeholder="nvidia/nemotron-nano-9b-v2:free",
        )
        yield Label("Think  (reasoning / Plan Mode)")
        yield Input(rc.think, id="r-think", placeholder="")
        yield Label("Long-context model")
        yield Input(
            rc.long_context,
            id="r-long-context",
            placeholder="minimax/minimax-m2.5:free",
        )
        yield Label("Long-context threshold (tokens)")
        yield Input(
            str(rc.long_context_threshold), id="r-threshold", placeholder="60000"
        )
        yield Label("Web search model  (add :online suffix for OpenRouter)")
        yield Input(rc.web_search, id="r-web-search", placeholder="")
        yield Label("Image model  (vision-capable)")
        yield Input(rc.image, id="r-image", placeholder="qwen/qwen2.5-vl-72b-instruct")
        yield Label("Custom router path  (.py or .js)")
        yield Input(
            rc.custom_router_path,
            id="r-custom-path",
            placeholder="config/custom_router.py",
        )

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
    SUB_TITLE = "[R]outer · [A]ssignments · [M]appings · Q = quit & save"

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
        layout: vertical;
    }
    #right-tabs {
        height: 1;
        width: 100%;
        align: center middle;
    }
    #right-content {
        height: 1fr;
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
    TabButton {
        margin: 0 1;
        padding: 0 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit_save", "Quit & Save"),
        Binding("ctrl+c", "quit_save", "Quit & Save", show=False),
        Binding("a", "add_entry", "Add"),
        Binding("d", "delete_entry", "Delete"),
        Binding("e", "edit_entry", "Edit"),
        Binding("t", "toggle_entry", "Toggle"),
        Binding("space", "toggle_entry", "Toggle", show=False),
        Binding("w", "move_up", "Move Up"),
        Binding("s", "move_down", "Move Down"),
        Binding("shift+up", "move_up", "Move Up", show=False),
        Binding("shift+down", "move_down", "Move Down", show=False),
        Binding("r", "restart_service", "Restart svc"),
        Binding("R", "show_router", "Router tab", show=False),
        Binding("A", "show_assignments", "Assignments tab", show=False),
        Binding("M", "show_mappings", "Mappings tab", show=False),
    ]

    _selected_row: reactive[int] = reactive(0)
    _right_mode: reactive[str] = reactive("router")  # router | assignments | mappings

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chain = ProxyChain.load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left-panel"):
                yield Label(
                    "[bold]Proxy Chain[/bold]  (W/S = reorder · E = edit · T = toggle)"
                )
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
            with Vertical(id="right-panel"):
                # Tab bar
                with Horizontal(id="right-tabs"):
                    yield Button("Router", id="tab-router", variant="primary")
                    yield Button("Assignments", id="tab-assignments")
                    yield Button("Identifier Mappings", id="tab-mappings")
                # Content area — only one child visible at a time
                with ScrollableContainer(id="right-content"):
                    yield RouterPanel(self._chain.router, id="router-panel")
                    yield AssignmentPanel(id="assignments-panel")
                    yield IdentifierMappingPanel(id="mappings-panel")
        yield Footer()

    async     async def on_mount(self) -> None:
        self._refresh_table()
        self.query_one("#chain-table", DataTable).focus()
        self._update_right_panel_visibility()
        # Start SSE listener for live config changes (T060)
        self._sse_task = asyncio.create_task(self._sse_listener())

    async def _sse_listener(self) -> None:
        """Background task: listen for config change events and refresh UI."""
        import httpx

        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET", "http://127.0.0.1:8082/api/config/events"
                    ) as resp:
                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data:"):
                                # Config change detected — refresh chain and panels
                                self.call_from_thread(self._refresh_chain_data)
                            # ignore non-data lines
            except Exception as e:
                self._set_status(f"SSE disconnected: {e}; reconnecting...")
                await asyncio.sleep(5)

    def _refresh_chain_data(self) -> None:
        """Reload chain from disk and refresh all panels (chain, assignments, mappings)."""
        try:
            self._chain = ProxyChain.load()
            self._refresh_table()
            # Refresh assignment panel if visible
            try:
                assign_panel = self.query_one("#assignments-panel", AssignmentPanel)
                assign_panel.refresh_table()
            except Exception:
                pass
            # Refresh identifier mapping panel if visible
            try:
                mapping_panel = self.query_one("#mappings-panel", IdentifierMappingPanel)
                mapping_panel.refresh_table()
            except Exception:
                pass
        except Exception as e:
            self._set_status(f"Error refreshing config: {e}")

    def on_unmount(self) -> None:
        """Clean up SSE listener task."""
        if hasattr(self, "_sse_task") and self._sse_task:
            self._sse_task.cancel()
        # Start SSE listener for live config changes (T060)
        self._sse_task = asyncio.create_task(self._sse_listener())

    async def _sse_listener(self) -> None:
        """Background task: listen for config change events and refresh chain data."""
        import httpx

        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET", "http://127.0.0.1:8082/api/config/events"
                    ) as resp:
                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data:"):
                                # Config change detected — reload chain and refresh UI
                                try:
                                    self._chain = ProxyChain.load()
                                    self._refresh_table()
                                except Exception as e:
                                    self._set_status(f"Error reloading chain: {e}")
                            # else ignore (comments, event lines)
            except Exception as e:
                self._set_status(f"SSE disconnected: {e}; retrying in 5s...")
                await asyncio.sleep(5)

    def on_unmount(self) -> None:
        """Clean up SSE listener task."""
        if hasattr(self, "_sse_task") and self._sse_task:
            self._sse_task.cancel()

    def _update_right_panel_visibility(self) -> None:
        """Show only the active right-panel and highlight the correct tab."""
        modes = ("router", "assignments", "mappings")
        panels = {
            "router": self.query_one("#router-panel"),
            "assignments": self.query_one("#assignments-panel"),
            "mappings": self.query_one("#mappings-panel"),
        }
        tabs = {
            "router": self.query_one("#tab-router", Button),
            "assignments": self.query_one("#tab-assignments", Button),
            "mappings": self.query_one("#tab-mappings", Button),
        }
        for m, widget in panels.items():
            widget.display = m == self._right_mode
        for m, btn in tabs.items():
            btn.variant = "primary" if m == self._right_mode else "default"

    # ── Tab navigation ────────────────────────────────────────────────────────

    def action_show_router(self) -> None:
        self._right_mode = "router"
        self._update_right_panel_visibility()

    def action_show_assignments(self) -> None:
        self._right_mode = "assignments"
        self._update_right_panel_visibility()

    def action_show_mappings(self) -> None:
        self._right_mode = "mappings"
        self._update_right_panel_visibility()

    @on(Button.Pressed, "#tab-router")
    def _tab_router(self) -> None:
        self.action_show_router()

    @on(Button.Pressed, "#tab-assignments")
    def _tab_assignments(self) -> None:
        self.action_show_assignments()

    @on(Button.Pressed, "#tab-mappings")
    def _tab_mappings(self) -> None:
        self.action_show_mappings()

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        table = self.query_one("#chain-table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Name", "Type", "URL / Mode", "Status")
        for i, e in enumerate(self._chain.entries):
            url_display = (
                e.display_url[:38] + "…" if len(e.display_url) > 40 else e.display_url
            )
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
                try:
                    payload = {
                        "id": entry.id,
                        "name": entry.name,
                        "url": entry.url or "",
                        "enabled": entry.enabled,
                        "port": entry.port or 0,
                        "type": entry.type,
                        "auth_key": entry.auth_key or "",
                        "service_cmd": entry.service_cmd or "",
                        "health_path": entry.health_path or "/health",
                        "timeout": entry.timeout,
                        "extra_headers": entry.extra_headers or {},
                        "model_prefixes": entry.model_prefixes or [],
                    }
                    ChainAPI.create(payload)
                    self._chain = ProxyChain.load()
                    self._selected_row = len(self._chain.entries) - 1
                    self._refresh_table()
                    self._set_status(f"Added: {entry.name}")
                except Exception as e:
                    self._set_status(f"Error adding: {e}")

        self.push_screen(EntryEditScreen(), _on_result)

    def action_edit_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        entry = self._chain.entries[idx]

        def _on_result(updated: Optional[ProxyEntry]) -> None:
            if updated:
                try:
                    payload = {
                        "name": updated.name,
                        "url": updated.url or "",
                        "enabled": updated.enabled,
                        "port": updated.port or 0,
                        "type": updated.type,
                        "auth_key": updated.auth_key or "",
                        "service_cmd": updated.service_cmd or "",
                        "health_path": updated.health_path or "/health",
                        "timeout": updated.timeout,
                        "extra_headers": updated.extra_headers or {},
                        "model_prefixes": updated.model_prefixes or [],
                    }
                    ChainAPI.update(entry.id, payload)
                    self._chain = ProxyChain.load()
                    self._refresh_table()
                    self._set_status(f"Updated: {updated.name}")
                except Exception as e:
                    self._set_status(f"Error updating: {e}")

        self.push_screen(EntryEditScreen(entry), _on_result)

    def action_delete_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        entry = self._chain.entries[idx]
        try:
            ChainAPI.delete(entry.id)
            self._chain = ProxyChain.load()
            self._selected_row = max(0, idx - 1)
            self._refresh_table()
            self._set_status(f"Deleted: {entry.name}")
        except Exception as e:
            self._set_status(f"Error deleting: {e}")

    def action_toggle_entry(self) -> None:
        idx = self._current_idx()
        if not self._chain.entries:
            return
        e = self._chain.entries[idx]
        try:
            new_enabled = not e.enabled
            ChainAPI.update(e.id, {"enabled": new_enabled})
            self._chain = ProxyChain.load()
            self._refresh_table()
            state = "enabled" if new_enabled else "disabled"
            self._set_status(f"{e.name}: {state}")
        except Exception as ex:
            self._set_status(f"Error toggling: {ex}")

    def action_move_up(self) -> None:
        idx = self._current_idx()
        if idx <= 0 or not self._chain.entries:
            return
        try:
            # Build new order: swap idx-1 and idx
            ids = [e.id for e in self._chain.entries]
            ids[idx - 1], ids[idx] = ids[idx], ids[idx - 1]
            ChainAPI.reorder(ids)
            self._chain = ProxyChain.load()
            self._selected_row = idx - 1
            self._refresh_table()
        except Exception as ex:
            self._set_status(f"Error moving up: {ex}")

    def action_move_down(self) -> None:
        idx = self._current_idx()
        if idx >= len(self._chain.entries) - 1 or not self._chain.entries:
            return
        try:
            ids = [e.id for e in self._chain.entries]
            ids[idx], ids[idx + 1] = ids[idx + 1], ids[idx]
            ChainAPI.reorder(ids)
            self._chain = ProxyChain.load()
            self._selected_row = idx + 1
            self._refresh_table()
        except Exception as ex:
            self._set_status(f"Error moving down: {ex}")

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
        # Collect router config from panel and persist only the router
        try:
            router_panel = self.query_one("#router-panel", RouterPanel)
            new_router = router_panel.collect()
            # Load fresh chain to avoid overwriting concurrent edits
            fresh = ProxyChain.load()
            fresh.router = new_router
            fresh.save()
        except Exception as ex:
            self._set_status(f"Error saving router: {ex}")
            return
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

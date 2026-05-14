"""Textual TUI panel for managing Identifier Mappings.

Provides CRUD + priority reorder for incoming_identifier → assignment_id mappings.
Writes go through the config API for cross-surface consistency.

Task: T035 (Phase 3 — US1)
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from src.cli.overlay import apply_cli_overlay
from src.core.config_resolver import get_resolver


# ─────────────────────────────────────────────────────────────────────────────
# HTTP client for identifier-mapping CRUD
# ─────────────────────────────────────────────────────────────────────────────


class MappingAPI:
    """Minimal HTTP client for identifier-mapping endpoints."""

    BASE_URL = "http://127.0.0.1:8082"

    @classmethod
    def list(cls) -> list[dict]:
        import urllib.request
        import json

        try:
            with urllib.request.urlopen(
                f"{cls.BASE_URL}/api/identifier-mappings", timeout=3
            ) as resp:
                data = json.loads(resp.read())
                return data.get("identifier_mappings", [])
        except Exception as e:
            print(f"[ERROR] MappingAPI.list: {e}")
            return []

    @classmethod
    def create(cls, payload: dict) -> Optional[dict]:
        import urllib.request
        import json

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/identifier-mappings",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[ERROR] MappingAPI.create: {e.code} {body}")
            return None
        except Exception as e:
            print(f"[ERROR] MappingAPI.create: {e}")
            return None

    @classmethod
    def update(cls, mapping_id: str, payload: dict) -> Optional[dict]:
        import urllib.request
        import json

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/identifier-mappings/{mapping_id}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[ERROR] MappingAPI.update: {e.code} {body}")
            return None
        except Exception as e:
            print(f"[ERROR] MappingAPI.update: {e}")
            return None

    @classmethod
    def delete(cls, mapping_id: str) -> bool:
        import urllib.request

        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/identifier-mappings/{mapping_id}", method="DELETE"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status in (200, 204)
        except urllib.error.HTTPError as e:
            print(f"[ERROR] MappingAPI.delete: {e.code}")
            return False
        except Exception as e:
            print(f"[ERROR] MappingAPI.delete: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Edit modal
# ─────────────────────────────────────────────────────────────────────────────


class MappingEditModal(ModalScreen[Optional[dict]]):
    """Form for creating/editing a single IdentifierMapping."""

    CSS = """
    MappingEditModal {
        align: center middle;
    }
    #dialog {
        width: 50;
        height: 15;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel"), ("enter", "submit", "Submit")]

    def __init__(
        self,
        mapping: Optional[dict] = None,
        *,
        title: str = "Edit Mapping",
    ):
        super().__init__()
        self.mapping = mapping or {}
        self.title_str = title

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dialog"):
            yield Label("Incoming Identifier:")
            yield Input(
                value=self.mapping.get("incoming_identifier", ""),
                id="incoming",
                placeholder="e.g. claude-opus-4-7",
            )
            yield Label("Assignment ID (target):")
            yield Input(
                value=self.mapping.get("assignment_id", ""),
                id="assignment",
                placeholder="big, middle, small, my_slot",
            )
            yield Label("Enabled:")
            yield Select(
                options=[("True", "true"), ("False", "false")],
                value="true" if self.mapping.get("enabled", True) else "false",
                id="enabled",
            )
            yield Label("Priority (0 = highest):")
            yield Input(
                value=str(self.mapping.get("priority", 0)), id="priority", type="number"
            )
            yield Label("Notes:")
            yield Input(value=self.mapping.get("notes", ""), id="notes")
            with Horizontal():
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#dialog").border_title = self.title_str

    def action_submit(self) -> None:
        self._collect_and_dismiss(save=True)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._collect_and_dismiss(save=True)
        else:
            self.dismiss(None)

    def _collect_and_dismiss(self, save: bool) -> None:
        try:
            priority = int(self.query_one("#priority", Input).value)
        except ValueError:
            priority = 0
        data = {
            "incoming_identifier": self.query_one("#incoming", Input).value.strip(),
            "assignment_id": self.query_one("#assignment", Input).value.strip(),
            "enabled": self.query_one("#enabled", Select).value == "true",
            "priority": priority,
            "notes": self.query_one("#notes", Input).value.strip(),
        }
        if not data["incoming_identifier"] or not data["assignment_id"]:
            self.notify(
                "Incoming identifier and assignment ID are required", severity="error"
            )
            return
        self.dismiss(data if save else None)


# ─────────────────────────────────────────────────────────────────────────────
# Main mapping listing panel
# ─────────────────────────────────────────────────────────────────────────────


class IdentifierMappingPanel(Static):
    """Table panel for identifier mappings with priority reordering."""

    CSS = """
    IdentifierMappingPanel {
        height: 1fr;
        border: solid $primary;
    }
    #toolbar {
        height: 3;
        dock: top;
        layout: horizontal;
    }
    Button { margin: 0 1; }
    #table { height: 1fr; overflow: auto; }
    """

    BINDINGS = [
        ("n", "new", "New"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("u", "up", "Priority Up"),
        ("down", "down", "Priority Down"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._mappings: list[dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="toolbar"):
            yield Button(" New ", variant="success", id="new")
            yield Button(" Edit ", id="edit")
            yield Button(" Delete ", variant="error", id="delete")
            yield Button(" ↑ ", id="up")
            yield Button(" ↓ ", id="down")
            yield Button(" Refresh ", id="refresh")
        yield Static(id="table")

    def on_mount(self) -> None:
        self.refresh_table()
        self._unsub = get_resolver().subscribe(self._on_config_change)

    def _on_config_change(self, event: dict) -> None:
        if event.get("field_path", "").startswith("identifier_mappings."):
            self.call_from_thread(self.refresh_table)

    def on_unmount(self) -> None:
        if hasattr(self, "_unsub"):
            self._unsub()

    def action_new(self) -> None:
        def on_submit(data: Optional[dict]) -> None:
            if not data:
                return
            resp = MappingAPI.create(data)
            if resp:
                self.notify(f"Mapping created for '{data['incoming_identifier']}'")
                self.refresh_table()
            else:
                self.notify("Create failed", severity="error")

        self.app.push_screen(MappingEditModal(None, title="New Mapping"), on_submit)

    def action_edit(self) -> None:
        from textual.widgets import Input

        class QuickInput(ModalScreen[Optional[str]]):
            def compose(self):
                yield Header()
                with Vertical():
                    yield Label("Incoming identifier to edit:")
                    yield Input(id="key", placeholder="e.g. claude-opus-4-7")
                    with Horizontal():
                        yield Button("OK", id="ok", variant="primary")
                        yield Button("Cancel", id="cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(self.query_one("#key", Input).value)

        def on_key(key: Optional[str]) -> None:
            if not key:
                return
            existing = next(
                (m for m in self._mappings if m.get("incoming_identifier") == key), None
            )
            if not existing:
                self.notify(f"No mapping for '{key}'", severity="error")
                return

            def on_update(data: Optional[dict]) -> None:
                if not data:
                    return
                resp = MappingAPI.update(existing.get("id", ""), data)
                if resp:
                    self.notify(f"Mapping updated")
                    self.refresh_table()
                else:
                    self.notify("Update failed", severity="error")

            self.app.push_screen(
                MappingEditModal(existing, title=f"Edit {key}"), on_update
            )

        self.app.push_screen(QuickInput(), on_key)

    def action_delete(self) -> None:
        from textual.widgets import Input

        class QuickInput(ModalScreen[Optional[str]]):
            def compose(self):
                yield Header()
                with Vertical():
                    yield Label("Incoming identifier to delete:")
                    yield Input(id="key", placeholder="e.g. claude-opus-4-7")
                    with Horizontal():
                        yield Button("Delete", id="del", variant="error")
                        yield Button("Cancel", id="cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(self.query_one("#key", Input).value)

        def on_key(key: Optional[str]) -> None:
            if not key:
                return
            mapping = next(
                (m for m in self._mappings if m.get("incoming_identifier") == key), None
            )
            if not mapping:
                self.notify(f"No mapping for '{key}'", severity="error")
                return
            if MappingAPI.delete(mapping.get("id", "")):
                self.notify(f"Mapping for '{key}' deleted")
                self.refresh_table()
            else:
                self.notify("Delete failed", severity="error")

        self.app.push_screen(QuickInput(), on_key)

    def action_up(self) -> None:
        self._reorder("up")

    def action_down(self) -> None:
        self._reorder("down")

    def action_refresh(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        self._mappings = sorted(
            MappingAPI.list(),
            key=lambda m: (m.get("priority", 0), m.get("incoming_identifier", "")),
        )
        table = self.query_one("#table", Static)
        lines = [
            "─" * 95,
            f"{'ID':<6} | {'Incoming':<25} | {'Assignment':<15} | {'Enabled':<7} | {'Pri'}",
            "─" * 95,
        ]
        for m in self._mappings:
            lines.append(
                f"{m.get('id', ''):<6} | "
                f"{m.get('incoming_identifier', ''):<25} | "
                f"{m.get('assignment_id', ''):<15} | "
                f"{m.get('enabled', True):<7} | "
                f"{m.get('priority', 0)}"
            )
        lines.append("─" * 95)
        table.update("\n".join(lines))

    def _reorder(self, direction: str) -> None:
        from textual.widgets import Input

        class ReorderScreen(ModalScreen[Optional[tuple[str, str]]]):
            def compose(self):
                yield Header()
                with Vertical():
                    yield Label(
                        f"Move which mapping {direction}? Enter incoming_identifier:"
                    )
                    yield Input(id="from", placeholder="current identifier")
                    yield Label(f"Swap with which identifier?")
                    yield Input(id="to", placeholder="target identifier")
                    with Horizontal():
                        yield Button("OK", id="ok", variant="primary")
                        yield Button("Cancel", id="cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(
                    (
                        self.query_one("#from", Input).value,
                        self.query_one("#to", Input).value,
                    )
                )

        def do_reorder(pair: Optional[tuple[str, str]]) -> None:
            if not pair:
                return
            a, b = pair
            mappings = MappingAPI.list()
            idx_a = next(
                (
                    i
                    for i, m in enumerate(mappings)
                    if m.get("incoming_identifier") == a
                ),
                None,
            )
            idx_b = next(
                (
                    i
                    for i, m in enumerate(mappings)
                    if m.get("incoming_identifier") == b
                ),
                None,
            )
            if idx_a is None or idx_b is None:
                self.notify("One or both identifiers not found", severity="error")
                return
            pri_a = mappings[idx_a].get("priority", 0)
            pri_b = mappings[idx_b].get("priority", 0)
            MappingAPI.update(mappings[idx_a]["id"], {"priority": pri_b})
            MappingAPI.update(mappings[idx_b]["id"], {"priority": pri_a})
            self.refresh_table()
            self.notify(f"Swapped priorities: {a} ↔ {b}")

        self.app.push_screen(ReorderScreen(), do_reorder)

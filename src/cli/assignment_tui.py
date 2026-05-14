"""Textual TUI panel for managing Assignments.

Allows operator to view, create, edit, and delete assignment records.
Writes go through the config API (HTTP) for cross-surface consistency.

Task: T034 (Phase 3 — US1)
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Table

from src.cli.overlay import apply_cli_overlay
from src.core.config_resolver import get_resolver
from src.services.observability.audit_log import mask_secret


# ─────────────────────────────────────────────────────────────────────────────
# HTTP client for assignment CRUD
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentAPI:
    """Minimal HTTP client for assignment CRUD — hits config_api on localhost."""

    BASE_URL = "http://127.0.0.1:8082"

    @classmethod
    def list(cls) -> list[dict]:
        import urllib.request
        import json

        try:
            with urllib.request.urlopen(
                f"{cls.BASE_URL}/api/assignments", timeout=3
            ) as resp:
                data = json.loads(resp.read())
                return data.get("assignments", [])
        except Exception as e:
            print(f"[ERROR] AssignmentAPI.list: {e}")
            return []

    @classmethod
    def get(cls, assignment_id: str) -> Optional[dict]:
        import urllib.request
        import json

        try:
            with urllib.request.urlopen(
                f"{cls.BASE_URL}/api/assignments/{assignment_id}", timeout=3
            ) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"[ERROR] AssignmentAPI.get: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] AssignmentAPI.get: {e}")
            return None

    @classmethod
    def create(cls, payload: dict) -> Optional[dict]:
        import urllib.request
        import json

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/assignments",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[ERROR] AssignmentAPI.create: {e.code} {body}")
            return None
        except Exception as e:
            print(f"[ERROR] AssignmentAPI.create: {e}")
            return None

    @classmethod
    def update(cls, assignment_id: str, payload: dict) -> Optional[dict]:
        import urllib.request
        import json

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/assignments/{assignment_id}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="PATCH",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[ERROR] AssignmentAPI.update: {e.code} {body}")
            return None
        except Exception as e:
            print(f"[ERROR] AssignmentAPI.update: {e}")
            return None

    @classmethod
    def delete(cls, assignment_id: str) -> bool:
        import urllib.request

        req = urllib.request.Request(
            f"{cls.BASE_URL}/api/assignments/{assignment_id}", method="DELETE"
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status in (200, 204)
        except urllib.error.HTTPError as e:
            print(f"[ERROR] AssignmentAPI.delete: {e.code}")
            return False
        except Exception as e:
            print(f"[ERROR] AssignmentAPI.delete: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Edit modal
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentEditModal(ModalScreen[Optional[dict]]):
    """Inline form for creating/editing a single Assignment."""

    CSS = """
    AssignmentEditModal {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: 18;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    Button {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "submit", "Submit"),
    ]

    def __init__(
        self,
        assignment: Optional[dict] = None,
        *,
        title: str = "Edit Assignment",
    ):
        super().__init__()
        self.assignment = assignment or {}
        self.title_str = title

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dialog"):
            yield Label("ID (slot/tier name):")
            yield Input(
                value=self.assignment.get("id", ""),
                id="id",
                placeholder="e.g. big, my_slot",
            )
            yield Label("Kind:")
            yield Select(
                options=[("tier", "tier"), ("slot", "slot")],
                value=self.assignment.get("kind", "tier"),
                id="kind",
            )
            yield Label("Model:")
            yield Input(
                value=self.assignment.get("model", ""),
                id="model",
                placeholder="openai/gpt-4",
            )
            yield Label("Provider:")
            yield Input(
                value=self.assignment.get("provider", ""),
                id="provider",
                placeholder="openai",
            )
            yield Label("Base URL:")
            yield Input(
                value=self.assignment.get("base_url", ""),
                id="base_url",
                placeholder="https://api.openai.com/v1",
            )
            yield Label("API Key:")
            yield Input(
                value=self.assignment.get("api_key", ""),
                id="api_key",
                placeholder="${OPENAI_API_KEY}",
                password=True,
            )
            yield Label("Enabled:")
            yield Select(
                options=[("True", "true"), ("False", "false")],
                value="true" if self.assignment.get("enabled", True) else "false",
                id="enabled",
            )
            yield Horizontal(
                Button("Save", variant="primary", id="save"),
                Button("Cancel", variant="default", id="cancel"),
            )

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
        data = {
            "id": self.query_one("#id", Input).value.strip(),
            "kind": self.query_one("#kind", Select).value,
            "model": self.query_one("#model", Input).value.strip(),
            "provider": self.query_one("#provider", Input).value.strip(),
            "base_url": self.query_one("#base_url", Input).value.strip(),
            "api_key": self.query_one("#api_key", Input).value.strip(),
            "enabled": self.query_one("#enabled", Select).value == "true",
            "cascade": [],
        }
        if not data["id"]:
            self.notify("ID is required", severity="error")
            return
        self.dismiss(data if save else None)


# ─────────────────────────────────────────────────────────────────────────────
# Main assignment listing panel
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentPanel(Static):
    """Table + keyboard-driven CRUD panel for assignments."""

    CSS = """
    AssignmentPanel {
        height: 1fr;
        border: solid $primary;
    }
    #toolbar {
        height: 3;
        dock: top;
        layout: horizontal;
    }
    Button {
        margin: 0 1;
    }
    #table {
        height: 1fr;
        overflow: auto;
    }
    """

    BINDINGS = [
        ("n", "new", "New"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._assignments: list[dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="toolbar"):
            yield Button(" New ", variant="success", id="new")
            yield Button(" Edit ", id="edit")
            yield Button(" Delete ", variant="error", id="delete")
            yield Button(" Refresh ", id="refresh")
        yield Static(id="table")

    def on_mount(self) -> None:
        self.refresh_table()
        # Subscribe to config change events for auto-refresh
        self._unsub = get_resolver().subscribe(self._on_config_change)

    def _on_config_change(self, event: dict) -> None:
        # Only refresh if assignments changed
        if event.get("field_path", "").startswith("assignments."):
            self.call_from_thread(self.refresh_table)

    def on_unmount(self) -> None:
        if hasattr(self, "_unsub"):
            self._unsub()

    def action_new(self) -> None:
        def on_submit(data: Optional[dict]) -> None:
            if not data:
                return
            resp = AssignmentAPI.create(data)
            if resp:
                self.notify(f"Assignment '{data['id']}' created")
                self.refresh_table()
            else:
                self.notify("Create failed (see server log)", severity="error")

        self.app.push_screen(
            AssignmentEditModal(None, title="New Assignment"), on_submit
        )

    def action_edit(self) -> None:
        # Prompt for assignment ID
        from textual.widgets import Input
        from textual.screen import Screen

        class QuickInput(ModalScreen[Optional[str]]):
            def compose(self):
                yield Header()
                with Vertical():
                    yield Label("Assignment ID to edit:")
                    yield Input(id="aid", placeholder="e.g. big")
                    with Horizontal():
                        yield Button("OK", id="ok", variant="primary")
                        yield Button("Cancel", id="cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(self.query_one("#aid", Input).value)

        def on_id_input(assignment_id: Optional[str]) -> None:
            if not assignment_id:
                return
            existing = AssignmentAPI.get(assignment_id)
            if not existing:
                self.notify(f"Assignment '{assignment_id}' not found", severity="error")
                return

            def on_update(data: Optional[dict]) -> None:
                if not data:
                    return
                resp = AssignmentAPI.update(assignment_id, data)
                if resp:
                    self.notify(f"Assignment '{assignment_id}' updated")
                    self.refresh_table()
                else:
                    self.notify("Update failed", severity="error")

            self.app.push_screen(
                AssignmentEditModal(existing, title=f"Edit {assignment_id}"), on_update
            )

        self.app.push_screen(QuickInput(), on_id_input)

    def action_delete(self) -> None:
        from textual.widgets import Input

        class QuickInput(ModalScreen[Optional[str]]):
            def compose(self):
                yield Header()
                with Vertical():
                    yield Label("Assignment ID to delete:")
                    yield Input(id="aid", placeholder="e.g. big")
                    with Horizontal():
                        yield Button("Delete", id="del", variant="error")
                        yield Button("Cancel", id="cancel")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(self.query_one("#aid", Input).value)

        def on_id_input(assignment_id: Optional[str]) -> None:
            if not assignment_id:
                return
            if AssignmentAPI.delete(assignment_id):
                self.notify(f"Assignment '{assignment_id}' deleted")
                self.refresh_table()
            else:
                self.notify("Delete failed (maybe not found?)", severity="error")

        self.app.push_screen(QuickInput(), on_id_input)

    def action_refresh(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        self._assignments = AssignmentAPI.list()
        table = self.query_one("#table", Static)
        lines = [
            "─" * 90,
            f"{'ID':<11} | {'Kind':<5} | {'Model':<35} | {'Provider':<12} | {'Enabled'}",
            "─" * 90,
        ]
        for a in self._assignments:
            line = (
                f"{a.get('id', ''):<11} | "
                f"{a.get('kind', ''):<5} | "
                f"{a.get('model', ''):<35} | "
                f"{a.get('provider', ''):<12} | "
                f"{a.get('enabled', True)}"
            )
            lines.append(line)
        lines.append("─" * 90)
        table.update("\n".join(lines))

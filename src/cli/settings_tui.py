"""Textual TUI for the full manifest config surface (parity with the web settings page).

Reads GET /api/config/schema (render hints) + GET /api/config (values) and saves via
POST /api/config/manifest — the same generic endpoint the web UI uses, so edits are
cross-surface consistent. Group list on the left, field form on the right.

Launch:  python -m src.cli.settings_tui
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict

BASE_URL = "http://127.0.0.1:8082"


# ─────────────────────────────────────────────────────────────────────────────
# Pure helper (unit-tested) — decide what to actually send.
# ─────────────────────────────────────────────────────────────────────────────
def collect_changes(loaded: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """Return only genuinely-changed settings. A masked secret ("***") and an untouched
    (still-blank) secret field are never sent, so editing other fields can't wipe a secret."""
    out: Dict[str, Any] = {}
    for key, val in current.items():
        if val == "***":
            continue
        if val == "" and loaded.get(key) == "***":
            continue  # secret left blank => keep existing
        if str(val) != str(loaded.get(key)):
            out[key] = val
    return out


class SettingsAPI:
    """Minimal urllib client — mirrors the other TUIs' API access pattern."""

    @staticmethod
    def _get(path: str) -> dict:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=4) as r:
            return json.loads(r.read().decode())

    @classmethod
    def schema(cls) -> list:
        return cls._get("/api/config/schema").get("groups", [])

    @classmethod
    def values(cls) -> dict:
        return cls._get("/api/config")

    @classmethod
    def save(cls, updates: Dict[str, Any]) -> dict:
        req = urllib.request.Request(
            f"{BASE_URL}/api/config/manifest",
            data=json.dumps(updates).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read().decode())


def _build_app():
    """Import Textual lazily so the module (and its pure helper) imports without a TUI stack."""
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, VerticalScroll
    from textual.widgets import (
        Button,
        Footer,
        Header,
        Input,
        Label,
        Select,
        Static,
        Switch,
    )

    class SettingsApp(App):
        TITLE = "Clutch Gateway — Settings"
        CSS = """
        #body { height: 1fr; }
        #groups { width: 28; border-right: solid $panel; }
        #fields { padding: 1 2; }
        .desc { color: $text-muted; }
        #status { dock: bottom; height: 1; padding: 0 1; }
        """
        BINDINGS = [("ctrl+s", "save", "Save"), ("q", "quit", "Quit")]

        def __init__(self) -> None:
            super().__init__()
            self.schema: list = []
            self.loaded: dict = {}
            self.current: dict = {}
            self.active: str = ""

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal(id="body"):
                yield VerticalScroll(id="groups")
                yield VerticalScroll(id="fields")
            yield Static("", id="status")
            yield Footer()

        async def on_mount(self) -> None:
            try:
                self.schema = SettingsAPI.schema()
                self.loaded = SettingsAPI.values()
            except Exception as e:  # gateway not running, etc.
                self._status(f"cannot reach {BASE_URL} — is the gateway up? ({e})")
                return
            self.current = dict(self.loaded)
            groups = self.query_one("#groups")
            for g in self.schema:
                await groups.mount(Button(g["label"], id=f"g_{g['name']}"))
            if self.schema:
                await self._render_group(self.schema[0]["name"])

        async def _render_group(self, name: str) -> None:
            self.active = name
            fields = self.query_one("#fields")
            await fields.remove_children()
            grp = next((g for g in self.schema if g["name"] == name), None)
            if not grp:
                return
            await fields.mount(Label(f"[b]{grp['label']}[/b]"))
            for s in grp["settings"]:
                key = s["key"]
                cur = self.current.get(key)
                units = f"  ({s['units']})" if s.get("units") else ""
                await fields.mount(Label(f"{s['env_var']}{units}"))
                await fields.mount(Label(s["description"], classes="desc"))
                wid = f"f_{key}"
                if s["web_component"] == "switch" or s["type"] == "bool":
                    await fields.mount(Switch(value=bool(cur), id=wid))
                elif s["web_component"] == "select" and s.get("choices"):
                    opts = [(c, c) for c in s["choices"]]
                    val = str(cur) if cur in s["choices"] else Select.BLANK
                    await fields.mount(Select(opts, value=val, id=wid))
                else:
                    await fields.mount(
                        Input(
                            value="" if s["secret"] else ("" if cur is None else str(cur)),
                            password=bool(s["secret"]),
                            placeholder="set — leave blank to keep" if (s["secret"] and cur == "***") else "",
                            id=wid,
                        )
                    )

        # ── edit tracking ──────────────────────────────────────────────────
        def _track(self, wid: str | None, value: Any) -> None:
            if wid and wid.startswith("f_"):
                self.current[wid[2:]] = value

        def on_switch_changed(self, e) -> None:
            self._track(e.switch.id, e.value)

        def on_input_changed(self, e) -> None:
            self._track(e.input.id, e.value)

        def on_select_changed(self, e) -> None:
            if e.value is not Select.BLANK:
                self._track(e.select.id, e.value)

        async def on_button_pressed(self, e) -> None:
            bid = e.button.id or ""
            if bid.startswith("g_"):
                await self._render_group(bid[2:])

        def action_save(self) -> None:
            changes = collect_changes(self.loaded, self.current)
            if not changes:
                self._status("no changes")
                return
            try:
                resp = SettingsAPI.save(changes)
            except Exception as e:
                self._status(f"save failed: {e}")
                return
            self.loaded.update({k: self.current[k] for k in changes})
            rej = resp.get("rejected", {})
            msg = f"saved {len(resp.get('saved', []))}"
            if rej:
                msg += f", rejected {len(rej)}: {', '.join(rej)}"
            self._status(msg)

        def _status(self, text: str) -> None:
            self.query_one("#status", Static).update(text)

    return SettingsApp


def main() -> None:
    _build_app()().run()


if __name__ == "__main__":
    main()

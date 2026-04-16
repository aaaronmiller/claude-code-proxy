#!/usr/bin/env python3
"""
Statusline Builder TUI — visual configurator for Claude Code's status line.

Launch:
    python -m src.cli.statusline_tui
    proxies statusline

Features:
    - Toggle segments (proxy metrics, system, CC stdin-JSON fields)
    - Assign each enabled segment to line 1 or 2, left or right alignment
    - Reorder within alignment group (j/k)
    - Live preview renders using actual segment functions + mock CC JSON
    - Save writes ~/.claude/statusline-config.json + patches settings.json
      to wire up the universal renderer.

Keybindings:
    ↑ / ↓       Navigate
    space       Toggle selected segment on/off
    l / r       Switch selected segment to left / right alignment
    1 / 2       Assign selected segment to line 1 / line 2
    j / k       Move segment down / up within its group
    p           Refresh preview
    s           Save config
    q           Quit (prompts if unsaved)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Static,
)
from rich.text import Text

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
SEGMENTS_SH = SCRIPT_DIR / "statusline_segments.sh"
RENDER_SH = SCRIPT_DIR / "statusline_render.sh"

CONFIG_PATH = Path.home() / ".claude" / "statusline-config.json"
CC_SETTINGS = Path.home() / ".claude" / "settings.json"

MOCK_CC_JSON = {
    "model": {"display_name": "Opus 4.6", "id": "claude-opus-4-6"},
    "workspace": {"current_dir": str(Path.cwd())},
    "cost": {"total_cost_usd": 0.042},
    "transcript_path": "",
    "session_id": "demo",
}

DEFAULT_CONFIG = {
    "separator": "│",
    "sep_padding": 2,
    "lines": [
        {
            "left": [{"id": "model"}, {"id": "cwd"}, {"id": "git_branch"}],
            "right": [{"id": "clock"}],
        },
        {
            "left": [
                {"id": "proxy_health"},
                {"id": "headroom_health"},
                {"id": "routing_mode"},
            ],
            "right": [
                {"id": "session_tokens"},
                {"id": "tool_stats"},
                {"id": "headroom_savings"},
            ],
        },
    ],
}


@dataclass
class Segment:
    id: str
    label: str
    category: str
    sample: str
    enabled: bool = False
    line: int = 1  # 1 or 2
    align: str = "left"  # "left" or "right"


def load_segment_catalog() -> List[Segment]:
    """Call `statusline_segments.sh list` to get the full list of available segments."""
    try:
        result = subprocess.run(
            ["bash", str(SEGMENTS_SH), "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        segs = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 4:
                segs.append(
                    Segment(
                        id=parts[0],
                        label=parts[1],
                        category=parts[2],
                        sample=parts[3],
                    )
                )
        return segs
    except Exception:
        return []


def load_config(catalog: List[Segment]) -> List[Segment]:
    """Merge saved config with the catalog, marking enabled/line/align/order."""
    cfg = DEFAULT_CONFIG
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass

    # Reset all to defaults
    by_id = {s.id: s for s in catalog}
    for s in catalog:
        s.enabled = False
        s.line = 1
        s.align = "left"

    # Apply config, preserving order via list index
    ordered: List[Segment] = []
    for line_idx, line in enumerate(cfg.get("lines", []), start=1):
        for align in ("left", "right"):
            for seg in line.get(align, []):
                sid = seg.get("id")
                if sid in by_id:
                    s = by_id[sid]
                    s.enabled = True
                    s.line = line_idx
                    s.align = align
                    ordered.append(s)

    # Append disabled segments at the end
    remaining = [s for s in catalog if s not in ordered]
    return ordered + remaining


def save_config(segments: List[Segment]) -> None:
    """Persist enabled segments to JSON config, preserving order."""
    lines: dict = {1: {"left": [], "right": []}, 2: {"left": [], "right": []}}
    for s in segments:
        if not s.enabled:
            continue
        lines.setdefault(s.line, {"left": [], "right": []})
        lines[s.line][s.align].append({"id": s.id})

    cfg = {
        "separator": "│",
        "sep_padding": 2,
        "lines": [lines[i] for i in sorted(lines.keys())],
    }
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def patch_cc_settings() -> bool:
    """Update ~/.claude/settings.json so statusLine.command points to our renderer."""
    if not CC_SETTINGS.exists():
        return False
    try:
        settings = json.loads(CC_SETTINGS.read_text())
    except Exception:
        return False
    cmd = f"bash {RENDER_SH}"
    settings.setdefault("statusLine", {})
    if settings["statusLine"].get("command") == cmd:
        return True
    # Backup first
    backup = CC_SETTINGS.with_suffix(".json.bak")
    shutil.copy2(CC_SETTINGS, backup)
    settings["statusLine"] = {
        "type": "command",
        "command": cmd,
        "padding": settings["statusLine"].get("padding", 2),
    }
    CC_SETTINGS.write_text(json.dumps(settings, indent=2))
    return True


def render_preview(segments: List[Segment], term_width: int = 120) -> str:
    """
    Serialize current segments to a tmp config, invoke statusline_render.sh with
    mock stdin JSON, and return the output (ANSI codes intact) for display.
    """
    # Build tmp config
    lines: dict = {1: {"left": [], "right": []}, 2: {"left": [], "right": []}}
    for s in segments:
        if not s.enabled:
            continue
        lines.setdefault(s.line, {"left": [], "right": []})
        lines[s.line][s.align].append({"id": s.id})
    cfg = {
        "separator": "│",
        "sep_padding": 2,
        "lines": [lines[i] for i in sorted(lines.keys())],
    }

    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tf:
        json.dump(cfg, tf)
        tf_path = tf.name

    try:
        env = {
            **os.environ,
            "STATUSLINE_CONFIG": tf_path,
            "COLUMNS": str(term_width),
        }
        proc = subprocess.run(
            ["bash", str(RENDER_SH)],
            input=json.dumps(MOCK_CC_JSON),
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        return proc.stdout
    except Exception as e:
        return f"(preview error: {e})"
    finally:
        os.unlink(tf_path)


class SaveScreen(ModalScreen[bool]):
    """Confirmation screen for saving."""

    def compose(self) -> ComposeResult:
        with Vertical(id="save-dialog"):
            yield Label("Save statusline config?", id="save-label")
            yield Label(f"Target: {CONFIG_PATH}", id="save-target")
            yield Label(
                f"Will also patch {CC_SETTINGS} to point at the renderer.",
                id="save-patch",
            )
            with Horizontal():
                yield Button("Save", variant="primary", id="save-yes")
                yield Button("Cancel", id="save-no")

    @on(Button.Pressed, "#save-yes")
    def _save(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#save-no")
    def _cancel(self) -> None:
        self.dismiss(False)


class StatuslineTUI(App):
    CSS = """
    Screen { layout: vertical; }
    #header-bar { height: 1; background: $accent; color: $text; }
    #main { height: 1fr; }
    #seg-panel { width: 60%; border: solid $primary; }
    #info-panel { width: 40%; border: solid $secondary; }
    #preview-box {
        height: 8;
        border: solid $warning;
        padding: 1;
        background: $surface;
    }
    #preview-title { color: $warning; text-style: bold; }
    DataTable { height: 1fr; }
    #help-text { color: $text-muted; padding: 1; }
    SaveScreen { align: center middle; }
    #save-dialog {
        width: 60; height: 10; padding: 1;
        background: $panel; border: thick $warning;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle", "Enable/Disable"),
        Binding("l", "align_left", "Left"),
        Binding("r", "align_right", "Right"),
        Binding("1", "set_line_1", "Line 1"),
        Binding("2", "set_line_2", "Line 2"),
        Binding("j", "move_down", "Move ↓"),
        Binding("k", "move_up", "Move ↑"),
        Binding("p", "refresh_preview", "Refresh preview"),
        Binding("s", "save", "Save"),
    ]

    def __init__(self) -> None:
        super().__init__()
        catalog = load_segment_catalog()
        self.segments: List[Segment] = load_config(catalog)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="seg-panel"):
                yield Label("Segments (space=toggle, l/r=align, 1/2=line, j/k=reorder)")
                yield DataTable(id="seg-table", cursor_type="row")
            with Vertical(id="info-panel"):
                yield Label("Segment Info")
                yield Static("", id="seg-info")
                yield Label("Help", id="help-title")
                yield Static(
                    (
                        "[b]space[/b] toggle  [b]l/r[/b] align  [b]1/2[/b] line\n"
                        "[b]j/k[/b] reorder within group\n"
                        "[b]p[/b] refresh preview  [b]s[/b] save  [b]q[/b] quit\n\n"
                        "Right-aligned segments anchor to the terminal\n"
                        "edge so long model names or folder paths\n"
                        "don't push them around."
                    ),
                    id="help-text",
                )
        yield Label("📺 Live Preview", id="preview-title")
        yield Static("", id="preview-box")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#seg-table", DataTable)
        table.add_columns("✓", "ID", "Category", "Line", "Align", "Sample")
        self._refresh_table()
        self._refresh_preview()

    def _refresh_table(self) -> None:
        table = self.query_one("#seg-table", DataTable)
        # Save cursor
        cursor = table.cursor_row if table.row_count > 0 else 0
        table.clear()
        for i, s in enumerate(self.segments):
            check = "●" if s.enabled else "○"
            line = str(s.line) if s.enabled else "-"
            align = s.align if s.enabled else "-"
            table.add_row(check, s.id, s.category, line, align, s.sample)
        # Restore cursor
        if table.row_count > 0:
            table.move_cursor(row=min(cursor, table.row_count - 1))

    def _current_segment(self) -> Optional[Segment]:
        table = self.query_one("#seg-table", DataTable)
        if table.row_count == 0:
            return None
        return self.segments[table.cursor_row]

    def _refresh_preview(self) -> None:
        term_w = max(80, self.size.width - 4)
        raw = render_preview(self.segments, term_width=term_w)
        preview = self.query_one("#preview-box", Static)
        # Rich.Text.from_ansi preserves colors & cursor movements (best-effort)
        try:
            preview.update(Text.from_ansi(raw))
        except Exception:
            preview.update(raw)

    def _refresh_info(self) -> None:
        s = self._current_segment()
        if not s:
            return
        info = (
            f"[b]{s.id}[/b] — {s.label}\n"
            f"Category: {s.category}\n"
            f"Enabled: {'yes' if s.enabled else 'no'}\n"
            f"Position: line {s.line}, {s.align}-aligned\n"
            f"Sample:   {s.sample}"
        )
        self.query_one("#seg-info", Static).update(info)

    def on_data_table_row_highlighted(self, _: DataTable.RowHighlighted) -> None:
        self._refresh_info()

    # ── Actions ──────────────────────────────────────────────────────
    def action_toggle(self) -> None:
        s = self._current_segment()
        if s:
            s.enabled = not s.enabled
            self._refresh_table()
            self._refresh_preview()
            self._refresh_info()

    def action_align_left(self) -> None:
        s = self._current_segment()
        if s and s.enabled:
            s.align = "left"
            self._refresh_table()
            self._refresh_preview()

    def action_align_right(self) -> None:
        s = self._current_segment()
        if s and s.enabled:
            s.align = "right"
            self._refresh_table()
            self._refresh_preview()

    def action_set_line_1(self) -> None:
        s = self._current_segment()
        if s and s.enabled:
            s.line = 1
            self._refresh_table()
            self._refresh_preview()

    def action_set_line_2(self) -> None:
        s = self._current_segment()
        if s and s.enabled:
            s.line = 2
            self._refresh_table()
            self._refresh_preview()

    def action_move_up(self) -> None:
        table = self.query_one("#seg-table", DataTable)
        i = table.cursor_row
        if i <= 0:
            return
        self.segments[i], self.segments[i - 1] = self.segments[i - 1], self.segments[i]
        self._refresh_table()
        table.move_cursor(row=i - 1)
        self._refresh_preview()

    def action_move_down(self) -> None:
        table = self.query_one("#seg-table", DataTable)
        i = table.cursor_row
        if i >= len(self.segments) - 1:
            return
        self.segments[i], self.segments[i + 1] = self.segments[i + 1], self.segments[i]
        self._refresh_table()
        table.move_cursor(row=i + 1)
        self._refresh_preview()

    def action_refresh_preview(self) -> None:
        self._refresh_preview()

    def action_save(self) -> None:
        def _after(confirmed: bool) -> None:
            if confirmed:
                save_config(self.segments)
                patched = patch_cc_settings()
                msg = f"Saved {CONFIG_PATH}"
                if patched:
                    msg += f" + patched {CC_SETTINGS}"
                self.notify(msg, severity="information")

        self.push_screen(SaveScreen(), _after)


def main() -> None:
    StatuslineTUI().run()


if __name__ == "__main__":
    main()

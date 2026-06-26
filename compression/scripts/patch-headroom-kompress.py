#!/usr/bin/env python3
"""Make headroom's Kompress compressor model env-configurable (idempotent).

The upstream ``headroom`` package hardcodes the Kompress checkpoint
(``chopratejas/kompress-base``), its ModernBERT backbone, and the tokenizer
inside ``headroom/transforms/kompress_compressor.py``. There is no env/config
knob, so swapping the compression model on any machine means editing
site-packages by hand — which is lost on every ``pip install --upgrade
headroom``.

This patcher rewrites those three hardcoded spots to read environment
variables, defaulting to the exact current values (so applying it changes
NOTHING until you set the vars):

    HEADROOM_KOMPRESS_MODEL     (default: chopratejas/kompress-base)
    HEADROOM_KOMPRESS_BACKBONE  (default: answerdotai/ModernBERT-base)

Backbone + tokenizer are kept in lockstep so a future checkpoint trained on a
different backbone (e.g. ModernBERT-large, once such a Kompress head is
published or trained) is a one-variable swap. The model architecture already
sizes its heads from ``encoder.config.hidden_size``, so it adapts to the
backbone automatically.

Idempotent: re-running is a no-op once patched. Safe to run on every startup
(headroom-start.sh does) so the patch survives package upgrades.

Usage:
    python3 patch-headroom-kompress.py            # patch in place
    python3 patch-headroom-kompress.py --check    # report status, exit 1 if unpatched
"""
from __future__ import annotations

import sys

MARKER = "# [headroom-kompress-env-patch]"

# (needle, replacement) — replacement carries the MARKER so we never double-apply.
EDITS = [
    (
        'HF_MODEL_ID = "chopratejas/kompress-base"',
        'import os as _os  ' + MARKER + '\n'
        'HF_MODEL_ID = _os.environ.get("HEADROOM_KOMPRESS_MODEL", "chopratejas/kompress-base")',
    ),
    (
        "        model = HeadroomCompressorModel()",
        "        model = HeadroomCompressorModel(  " + MARKER + "\n"
        '            _os.environ.get("HEADROOM_KOMPRESS_BACKBONE", "answerdotai/ModernBERT-base")\n'
        "        )",
    ),
    (
        '        tokenizer = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")',
        "        tokenizer = AutoTokenizer.from_pretrained(  " + MARKER + "\n"
        '            _os.environ.get("HEADROOM_KOMPRESS_BACKBONE", "answerdotai/ModernBERT-base")\n'
        "        )",
    ),
]


def locate() -> str:
    import importlib.util

    spec = importlib.util.find_spec("headroom.transforms.kompress_compressor")
    if spec is None or not spec.origin:
        print("ERROR: headroom.transforms.kompress_compressor not importable", file=sys.stderr)
        sys.exit(2)
    return spec.origin


def main() -> int:
    check_only = "--check" in sys.argv
    path = locate()
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()

    if MARKER in src:
        print(f"already patched: {path}")
        return 0
    if check_only:
        print(f"UNPATCHED: {path}")
        return 1

    patched = src
    for needle, repl in EDITS:
        if needle not in patched:
            print(f"ERROR: anchor not found (headroom layout changed?): {needle!r}", file=sys.stderr)
            return 3
        patched = patched.replace(needle, repl, 1)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(patched)
    print(f"patched: {path}")
    print("  HEADROOM_KOMPRESS_MODEL / HEADROOM_KOMPRESS_BACKBONE now honored "
          "(defaults unchanged: kompress-base / ModernBERT-base)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

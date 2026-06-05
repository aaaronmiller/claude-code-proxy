"""Runtime patch for Headroom Kompress device selection.

Headroom 0.20.27 defaults OpenVINO Kompress to GPU.1 when the compressor
device is "auto". On this Intel Arc WSL host GPU.1 is not the Arc dGPU and can
fail with CL_OUT_OF_RESOURCES. Keep the patch local to this repo's launcher
instead of modifying the installed package.
"""

from __future__ import annotations

import os


def _patch_kompress_device() -> None:
    try:
        from headroom.transforms import kompress_compressor as kompress
    except Exception:
        return

    original_load = getattr(kompress, "_load_kompress", None)
    if original_load is None or getattr(original_load, "_ccp_device_patch", False):
        return

    def load_with_configured_device(device: str = "auto"):
        configured = os.environ.get("HEADROOM_KOMPRESS_DEVICE", "GPU.0").strip()
        if device in ("", "auto", None) and configured:
            device = configured
        return original_load(device)

    load_with_configured_device._ccp_device_patch = True  # type: ignore[attr-defined]
    kompress._load_kompress = load_with_configured_device


_patch_kompress_device()

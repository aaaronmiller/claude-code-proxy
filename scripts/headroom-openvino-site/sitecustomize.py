"""Runtime patches for Headroom Kompress device selection.

Headroom 0.20.27 defaults OpenVINO Kompress to GPU.1 when the compressor
device is "auto". On this Intel Arc WSL host GPU.1 is not the Arc dGPU and can
fail with CL_OUT_OF_RESOURCES. Keep the patch local to this repo's launcher
instead of modifying the installed package.
"""

from __future__ import annotations

import os


def _env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _ensure_onnx_model_wrapper(kompress) -> None:
    if hasattr(kompress, "_OnnxModel"):
        return

    class _OnnxModel:
        """Compatibility wrapper missing from some Headroom 0.20.27 installs."""

        def __init__(self, session):
            self._session = session

        def get_scores(self, input_ids, attention_mask):
            import numpy as np

            scores = self._session.run(
                ["final_scores"],
                {
                    "input_ids": np.asarray(input_ids, dtype=np.int64),
                    "attention_mask": np.asarray(attention_mask, dtype=np.int64),
                },
            )
            return scores[0]

        def get_keep_mask(self, input_ids, attention_mask):
            import numpy as np

            return (np.array(self.get_scores(input_ids, attention_mask)) > 0.5).tolist()

    kompress._OnnxModel = _OnnxModel


def _patch_kompress_device() -> None:
    try:
        from headroom.transforms import kompress_compressor as kompress
    except Exception:
        return

    _ensure_onnx_model_wrapper(kompress)

    if _env_true("HEADROOM_DISABLE_OPENVINO"):
        kompress._is_openvino_available = lambda: False

    if _env_true("HEADROOM_DISABLE_ONNX"):
        kompress._is_onnx_available = lambda: False

    original_load = getattr(kompress, "_load_kompress", None)
    if original_load is None or getattr(original_load, "_ccp_device_patch", False):
        return

    def load_with_configured_device(device: str = "auto"):
        configured = os.environ.get("HEADROOM_KOMPRESS_DEVICE", "").strip()
        if device in ("", "auto", None) and configured:
            device = configured
        return original_load(device)

    load_with_configured_device._ccp_device_patch = True  # type: ignore[attr-defined]
    kompress._load_kompress = load_with_configured_device


_patch_kompress_device()
